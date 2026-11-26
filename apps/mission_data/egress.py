"""Minimal historical public-data model egress control (RD1.3 / LLM_DATA_POLICY).

This module performs pure policy evaluation and payload inspection with zero
network imports. External model processing is default-deny; only explicitly
approved, non-expired public historical datasets with allowlisted fields may
leave the local host, and ground truth / hidden references are always forbidden.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
from typing import Any, Iterator, Literal, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from apps.contracts.v1 import ContractBase
from apps.llm_gateway_errors import LLMEgressDeniedError
from apps.mission_data.isolation import find_forbidden_label_keys
from apps.mission_data.provenance import require_non_blank, validate_source_url

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EGRESS_APPROVALS = (
    REPO_ROOT / "data" / "mission_registry" / "egress_approvals.json"
)

DataClass = Literal[
    "synthetic_ci",
    "historical_public",
    "unknown",
    "unlicensed",
    "mixed",
    "private",
    "sensitive",
    "customer",
    "live",
    "operational",
]

FORBIDDEN_EXTERNAL_DATA_CLASSES: frozenset[str] = frozenset(
    {
        "unknown",
        "unlicensed",
        "mixed",
        "private",
        "sensitive",
        "customer",
        "live",
        "operational",
    }
)

ProcessingKind = Literal["chat_completion", "embeddings", "reranking", "judge"]

SUPPORTED_REDACTION_RULES: frozenset[str] = frozenset(
    {
        "mask_emails",
        "mask_ip_addresses",
        "mask_absolute_paths",
    }
)

_URL_SCHEME_HOST_RE = re.compile(
    r"^(https?)://(?P<authority>[^/\s?#]+)(?:[/?#].*)?$", re.IGNORECASE
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_WINDOWS_ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\[A-Za-z0-9_.-]+\\)[^\s\"'`<>|]+"
)
_POSIX_ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.:/-])/(?:etc|home|Users|var|tmp|opt|root|proc|sys|mnt|srv)/[^\s\"'`<>|]+"
)
_FILE_URI_TEXT_RE = re.compile(r"\bfile://[^\s\"'<>]+", re.IGNORECASE)
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE)),
    ("pem_private_key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    (
        "url_credentials",
        re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@[^\s]+", re.IGNORECASE),
    ),
    (
        "credential_assignment",
        re.compile(
            r"\b(?:api_key|apikey|secret|password|passwd|access_token)\s*[:=]\s*['\"]?[^\s'\",;]{6,}",
            re.IGNORECASE,
        ),
    ),
)
_GROUND_TRUTH_TEXT_RE = re.compile(
    r"(?:['\"]?(?:ground_truth|hidden_reference|reference_answer|expected_root_cause|"
    r"anomaly_label|is_anomaly|telecommand_label|rare_nominal|is_rare_nominal|"
    r"class_label|expected_label)['\"]?\s*[:=])",
    re.IGNORECASE,
)

_GATEWAY_VERIFIED: ContextVar[bool] = ContextVar(
    "spaceops_egress_gateway_verified", default=False
)
_ACTIVE_PROTECTED_CONTEXT: ContextVar[EgressContext | None] = ContextVar(
    "spaceops_egress_protected_context", default=None
)


def _parse_utc_timestamp(raw: str, field_name: str) -> datetime:
    cleaned = require_non_blank(raw, field_name)
    normalized = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset or 'Z'")
    return parsed.astimezone(timezone.utc)


def is_loopback_endpoint(url: str | None) -> bool:
    """Strictly verify whether an http(s) URL targets a local loopback address."""
    if not url or not isinstance(url, str):
        return False
    cleaned = url.strip()
    if not cleaned or any(ch.isspace() for ch in cleaned):
        return False
    match = _URL_SCHEME_HOST_RE.match(cleaned)
    if not match:
        return False
    authority = match.group("authority")
    if "@" in authority:
        return False
    host: str
    if authority.startswith("["):
        end_bracket = authority.find("]")
        if end_bracket <= 1:
            return False
        host = authority[1:end_bracket]
        remainder = authority[end_bracket + 1 :]
        if remainder and (not remainder.startswith(":") or not remainder[1:].isdigit()):
            return False
    else:
        if authority.count(":") > 1:
            return False
        if ":" in authority:
            host, port = authority.split(":", 1)
            if not port.isdigit():
                return False
        else:
            host = authority
    lowered = host.lower().rstrip(".")
    if lowered == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    if ip.is_unspecified:
        return False
    return ip.is_loopback


def normalize_endpoint_origin(url: str) -> str:
    """Normalize an endpoint URL for exact approval comparison."""
    cleaned = require_non_blank(url, "endpoint_url").rstrip("/")
    match = _URL_SCHEME_HOST_RE.match(cleaned)
    if not match:
        return cleaned.lower()
    scheme = match.group(1).lower()
    rest = cleaned[len(match.group(1)) + 3 :]
    slash = rest.find("/")
    if slash == -1:
        return f"{scheme}://{rest.lower()}"
    return f"{scheme}://{rest[:slash].lower()}{rest[slash:]}"


class AllowedProcessing(ContractBase):
    chat_completion: bool = False
    embeddings: bool = False
    reranking: bool = False
    judge: bool = False

    def allows(self, kind: ProcessingKind) -> bool:
        return bool(getattr(self, kind, False))


class EgressApprovalRecord(ContractBase):
    """Explicit, versioned approval for one historical public dataset and endpoint."""

    approval_id: str = Field(..., min_length=1)
    policy_revision: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    version_or_checksum: str = Field(..., min_length=1)
    approved_fields: list[str] = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    approved_endpoint: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    model_id: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    allowed_processing: AllowedProcessing
    owner: str = Field(..., min_length=1)
    review_date: str = Field(..., min_length=1)
    expires_at: str = Field(..., min_length=1)
    license_spdx: str = Field(..., min_length=1)
    attribution: str = Field(..., min_length=1)
    confidentiality_export_assessment: str = Field(..., min_length=1)
    provider_retention_assessment: str = Field(..., min_length=1)
    redaction_required: bool = False
    redaction_rules: list[str] = Field(default_factory=list)

    @field_validator(
        "approval_id",
        "policy_revision",
        "dataset_id",
        "version_or_checksum",
        "purpose",
        "provider",
        "account_id",
        "model_id",
        "region",
        "owner",
        "license_spdx",
        "attribution",
        "confidentiality_export_assessment",
        "provider_retention_assessment",
    )
    @classmethod
    def reject_blank(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    @field_validator("approved_endpoint")
    @classmethod
    def check_endpoint(cls, value: str) -> str:
        return validate_source_url(value)

    @field_validator("approved_fields")
    @classmethod
    def check_approved_fields(cls, values: list[str]) -> list[str]:
        cleaned = [require_non_blank(item, "approved_field") for item in values]
        forbidden = find_forbidden_label_keys({item: True for item in cleaned})
        if forbidden:
            raise ValueError(
                f"approved_fields must not include ground-truth keys: {forbidden}"
            )
        return cleaned

    @model_validator(mode="after")
    def validate_dates_and_redaction(self) -> EgressApprovalRecord:
        review_dt = _parse_utc_timestamp(self.review_date, "review_date")
        expires_dt = _parse_utc_timestamp(self.expires_at, "expires_at")
        if expires_dt <= review_dt:
            raise ValueError("expires_at must be strictly after review_date")
        if self.redaction_required:
            if not self.redaction_rules:
                raise ValueError(
                    "redaction_rules must be non-empty when redaction_required is true"
                )
        unknown_rules = [
            rule
            for rule in self.redaction_rules
            if rule not in SUPPORTED_REDACTION_RULES
        ]
        if unknown_rules:
            raise ValueError(f"unsupported redaction_rules: {unknown_rules}")
        return self

    def expires_at_utc(self) -> datetime:
        return _parse_utc_timestamp(self.expires_at, "expires_at")


class EgressApprovalRegistryDocument(ContractBase):
    schema_version: Literal["1"]
    policy_revision: str = Field(..., min_length=1)
    default_decision: Literal["deny"] = "deny"
    approvals: list[EgressApprovalRecord] = Field(default_factory=list)

    @field_validator("policy_revision")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        return require_non_blank(value, "policy_revision")


class EgressApprovalRegistry:
    """Default-deny approval lookup keyed by dataset, version, provider, model, and endpoint."""

    def __init__(self, document: EgressApprovalRegistryDocument) -> None:
        self.document = document
        seen_ids: set[str] = set()
        for item in document.approvals:
            if item.approval_id in seen_ids:
                raise ValueError(f"duplicate approval_id {item.approval_id}")
            seen_ids.add(item.approval_id)

    @property
    def policy_revision(self) -> str:
        return self.document.policy_revision

    def find_matching(
        self,
        *,
        dataset_id: str,
        version_or_checksum: str,
        purpose: str,
        provider: str,
        endpoint_url: str,
        account_id: str,
        model_id: str,
        region: str,
    ) -> EgressApprovalRecord | None:
        norm_endpoint = normalize_endpoint_origin(endpoint_url)
        for item in self.document.approvals:
            if (
                item.dataset_id == dataset_id
                and item.version_or_checksum == version_or_checksum
                and item.purpose == purpose
                and item.provider.lower() == provider.lower()
                and normalize_endpoint_origin(item.approved_endpoint) == norm_endpoint
                and item.account_id == account_id
                and item.model_id == model_id
                and item.region == region
            ):
                return item
        return None


def load_egress_approvals(path: Path | None = None) -> EgressApprovalRegistry:
    registry_path = path or DEFAULT_EGRESS_APPROVALS
    payload: Any = json.loads(registry_path.read_text(encoding="utf-8"))
    return EgressApprovalRegistry(
        EgressApprovalRegistryDocument.model_validate(payload)
    )


class EgressRequest(ContractBase):
    """Concrete outbound model request evaluated at the egress boundary."""

    data_class: DataClass
    dataset_ids: list[str] = Field(default_factory=list)
    version_or_checksum: str | None = None
    purpose: str = "historical_read_only_triage"
    provider: str = Field(..., min_length=1)
    endpoint_url: str | None = None
    account_id: str = ""
    model_id: str = Field(..., min_length=1)
    region: str = ""
    processing_kind: ProcessingKind = "chat_completion"
    payload_fields: dict[str, Any] = Field(default_factory=dict)
    outbound_text: str = ""
    contains_ground_truth: bool = False
    local_only: bool = False
    now_utc: datetime | None = None

    @field_validator("provider", "model_id")
    @classmethod
    def reject_blank(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    @field_validator("now_utc")
    @classmethod
    def require_aware_now(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("now_utc must be timezone-aware")
        return value


class EgressContext(ContractBase):
    """Caller-supplied dataset and policy metadata attached to a model call."""

    data_class: DataClass
    dataset_ids: list[str] = Field(default_factory=list)
    version_or_checksum: str | None = None
    purpose: str = "historical_read_only_triage"
    account_id: str = ""
    region: str = ""
    processing_kind: ProcessingKind = "chat_completion"
    payload_fields: dict[str, Any] = Field(default_factory=dict)
    contains_ground_truth: bool = False
    local_only: bool = False
    allow_fallback: bool = False
    approvals_path: str | None = None

    def to_request(
        self,
        *,
        provider: str,
        model_id: str,
        endpoint_url: str | None,
        outbound_text: str,
        local_only_override: bool = False,
        now_utc: datetime | None = None,
    ) -> EgressRequest:
        return EgressRequest(
            data_class=self.data_class,
            dataset_ids=list(self.dataset_ids),
            version_or_checksum=self.version_or_checksum,
            purpose=self.purpose,
            provider=provider,
            endpoint_url=endpoint_url,
            account_id=self.account_id,
            model_id=model_id,
            region=self.region,
            processing_kind=self.processing_kind,
            payload_fields=dict(self.payload_fields),
            outbound_text=outbound_text,
            contains_ground_truth=self.contains_ground_truth,
            local_only=bool(self.local_only or local_only_override),
            now_utc=now_utc,
        )


def inherit_egress_classification(
    sources: Sequence[EgressContext],
) -> EgressContext:
    """Combine source contexts so derived summaries inherit the strictest restriction."""
    if not sources:
        return EgressContext(data_class="unknown", local_only=True)
    dataset_ids: list[str] = []
    seen_datasets: set[str] = set()
    classes: set[DataClass] = set()
    for src in sources:
        classes.add(src.data_class)
        for ds in src.dataset_ids:
            if ds not in seen_datasets:
                seen_datasets.add(ds)
                dataset_ids.append(ds)

    resolved_class: DataClass
    forbidden_present = [c for c in classes if c in FORBIDDEN_EXTERNAL_DATA_CLASSES]
    if forbidden_present:
        # Preserve a deterministic strictest class when any restricted class is present.
        priority: tuple[DataClass, ...] = (
            "operational",
            "live",
            "customer",
            "sensitive",
            "private",
            "unlicensed",
            "mixed",
            "unknown",
        )
        resolved_class = next(c for c in priority if c in classes)
    elif len(classes) > 1:
        # Mixing synthetic_ci and historical_public produces mixed (external denied).
        resolved_class = "mixed"
    else:
        resolved_class = next(iter(classes))

    versions = {(src.version_or_checksum or "").strip() or None for src in sources}
    merged_fields: dict[str, Any] = {}
    for src in sources:
        merged_fields.update(src.payload_fields)
    approvals_path = next(
        (src.approvals_path for src in sources if src.approvals_path), None
    )
    return EgressContext(
        data_class=resolved_class,
        dataset_ids=dataset_ids,
        version_or_checksum=next(iter(versions)) if len(versions) == 1 else None,
        purpose=sources[-1].purpose,
        account_id=sources[-1].account_id or sources[0].account_id,
        region=sources[-1].region or sources[0].region,
        processing_kind=sources[-1].processing_kind,
        payload_fields=merged_fields,
        contains_ground_truth=any(
            src.contains_ground_truth
            or bool(find_forbidden_label_keys(src.payload_fields))
            for src in sources
        ),
        local_only=any(src.local_only for src in sources),
        allow_fallback=all(src.allow_fallback for src in sources),
        approvals_path=approvals_path,
    )


class EgressDecision(ContractBase):
    """Sanitized audit metadata for an egress decision (never contains raw payloads)."""

    allowed: bool
    reason_code: str
    data_class: DataClass
    dataset_ids: list[str]
    policy_revision: str
    approval_id: str | None = None
    provider: str
    model_id: str
    processing_kind: ProcessingKind
    redaction_applied: bool = False
    decided_at_utc: str


class EgressEvaluationResult(ContractBase):
    decision: EgressDecision
    sanitized_text: str
    sanitized_fields: dict[str, Any] = Field(default_factory=dict)


def _apply_redaction_to_str(text: str, rules: Sequence[str]) -> tuple[str, bool]:
    updated = text
    changed = False
    for rule in rules:
        if rule == "mask_emails":
            replaced = _EMAIL_RE.sub("[REDACTED_EMAIL]", updated)
        elif rule == "mask_ip_addresses":
            replaced = _IPV4_RE.sub("[REDACTED_IP]", updated)
        elif rule == "mask_absolute_paths":
            replaced = _WINDOWS_ABS_PATH_RE.sub("[REDACTED_PATH]", updated)
            replaced = _POSIX_ABS_PATH_RE.sub("[REDACTED_PATH]", replaced)
            replaced = _FILE_URI_TEXT_RE.sub("[REDACTED_PATH]", replaced)
        else:
            raise ValueError(f"unsupported redaction rule: {rule}")
        if replaced != updated:
            changed = True
            updated = replaced
    return updated, changed


def _apply_redaction_to_obj(obj: Any, rules: Sequence[str]) -> tuple[Any, bool]:
    if isinstance(obj, str):
        return _apply_redaction_to_str(obj, rules)
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        changed = False
        for key, value in obj.items():
            new_val, item_changed = _apply_redaction_to_obj(value, rules)
            out[str(key)] = new_val
            changed = changed or item_changed
        return out, changed
    if isinstance(obj, list):
        out_list: list[Any] = []
        changed = False
        for item in obj:
            new_item, item_changed = _apply_redaction_to_obj(item, rules)
            out_list.append(new_item)
            changed = changed or item_changed
        return out_list, changed
    return obj, False


def _detect_sensitive_findings(text: str, fields: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []

    def _scan_str(value: str) -> None:
        for label, pattern in _SECRET_PATTERNS:
            if pattern.search(value):
                findings.append(label)
        if _EMAIL_RE.search(value):
            findings.append("email")
        if (
            _WINDOWS_ABS_PATH_RE.search(value)
            or _POSIX_ABS_PATH_RE.search(value)
            or _FILE_URI_TEXT_RE.search(value)
        ):
            findings.append("local_path")

    def _walk(obj: Any) -> None:
        if isinstance(obj, str):
            _scan_str(obj)
        elif isinstance(obj, Mapping):
            for value in obj.values():
                _walk(value)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _scan_str(text)
    _walk(fields)
    return sorted(set(findings))


def _is_local_target(provider: str, endpoint_url: str | None) -> bool:
    return provider.lower() in {"local", "gpu"} and is_loopback_endpoint(endpoint_url)


def evaluate_egress(
    request: EgressRequest,
    registry: EgressApprovalRegistry | None = None,
) -> EgressEvaluationResult:
    """Evaluate one outbound model request under the RD1.3 default-deny egress policy."""
    reg = registry or load_egress_approvals()
    now_dt = (
        request.now_utc.astimezone(timezone.utc)
        if request.now_utc is not None
        else datetime.now(timezone.utc)
    )
    now_iso = now_dt.replace(microsecond=0).isoformat()

    def _make(
        allowed: bool,
        reason_code: str,
        *,
        approval_id: str | None = None,
        redaction_applied: bool = False,
        text: str = request.outbound_text,
        fields: dict[str, Any] | None = None,
    ) -> EgressEvaluationResult:
        decision = EgressDecision(
            allowed=allowed,
            reason_code=reason_code,
            data_class=request.data_class,
            dataset_ids=list(request.dataset_ids),
            policy_revision=reg.policy_revision,
            approval_id=approval_id,
            provider=request.provider,
            model_id=request.model_id,
            processing_kind=request.processing_kind,
            redaction_applied=redaction_applied,
            decided_at_utc=now_iso,
        )
        return EgressEvaluationResult(
            decision=decision,
            sanitized_text=text,
            sanitized_fields=dict(
                fields if fields is not None else request.payload_fields
            ),
        )

    # 1. Ground truth and hidden references are never allowed in model requests.
    if (
        request.contains_ground_truth
        or find_forbidden_label_keys(request.payload_fields)
        or _GROUND_TRUTH_TEXT_RE.search(request.outbound_text)
    ):
        return _make(False, "ground_truth_forbidden")

    local_target = _is_local_target(request.provider, request.endpoint_url)

    # 2. Local-only mode denies all external endpoints, embeddings, rerankers, judges, fallback.
    if request.local_only:
        if not local_target:
            return _make(False, "local_only_external_denied")
        return _make(True, "local_only_loopback_allowed")

    # 3. Synthetic CI fixtures retain existing lab behavior unless ground truth/secrets leak.
    if request.data_class == "synthetic_ci":
        if not local_target and _detect_sensitive_findings(
            request.outbound_text, request.payload_fields
        ):
            return _make(False, "sensitive_payload_detected")
        return _make(True, "synthetic_ci_lab_path")

    # 4. Unknown, unlicensed, mixed, private, sensitive, customer, live, operational data:
    #    external processing has no exception under this policy.
    if request.data_class in FORBIDDEN_EXTERNAL_DATA_CLASSES:
        if local_target:
            return _make(True, "local_backend_allowed")
        return _make(False, f"forbidden_data_class:{request.data_class}")

    # 5. Historical public dataset: local loopback is allowed; external requires explicit approval.
    if local_target:
        return _make(True, "local_backend_allowed")

    if not request.dataset_ids:
        return _make(False, "missing_dataset_id")
    if not (request.version_or_checksum or "").strip():
        return _make(False, "missing_dataset_version")
    if not (request.endpoint_url or "").strip():
        return _make(False, "missing_endpoint_url")

    matched_approvals: list[EgressApprovalRecord] = []
    for ds_id in request.dataset_ids:
        approval = reg.find_matching(
            dataset_id=ds_id,
            version_or_checksum=str(request.version_or_checksum).strip(),
            purpose=request.purpose,
            provider=request.provider,
            endpoint_url=str(request.endpoint_url),
            account_id=request.account_id,
            model_id=request.model_id,
            region=request.region,
        )
        if approval is None:
            return _make(False, "unapproved_dataset_or_target")
        if now_dt >= approval.expires_at_utc():
            return _make(
                False,
                "approval_expired",
                approval_id=approval.approval_id,
            )
        if not approval.allowed_processing.allows(request.processing_kind):
            return _make(
                False,
                "processing_kind_not_approved",
                approval_id=approval.approval_id,
            )
        approved_field_set = set(approval.approved_fields)
        unapproved = [
            key for key in request.payload_fields if key not in approved_field_set
        ]
        if unapproved:
            return _make(
                False,
                "unapproved_payload_field",
                approval_id=approval.approval_id,
            )
        matched_approvals.append(approval)

    # Apply redaction rules when required by any matched approval.
    rules: list[str] = []
    for approval in matched_approvals:
        if approval.redaction_required:
            for rule in approval.redaction_rules:
                if rule not in rules:
                    rules.append(rule)

    out_text = request.outbound_text
    out_fields = dict(request.payload_fields)
    redaction_applied = False
    if rules:
        out_text, text_changed = _apply_redaction_to_str(out_text, rules)
        redacted_fields, fields_changed = _apply_redaction_to_obj(out_fields, rules)
        out_fields = dict(redacted_fields)
        redaction_applied = text_changed or fields_changed

    if _detect_sensitive_findings(out_text, out_fields):
        return _make(
            False,
            "sensitive_payload_detected",
            approval_id=matched_approvals[0].approval_id,
            redaction_applied=redaction_applied,
        )

    approval_ids = ",".join(item.approval_id for item in matched_approvals)
    return _make(
        True,
        "approved_historical_public",
        approval_id=approval_ids,
        redaction_applied=redaction_applied,
        text=out_text,
        fields=out_fields,
    )


def get_active_protected_context() -> EgressContext | None:
    """Return the active protected egress scope, if any."""
    return _ACTIVE_PROTECTED_CONTEXT.get()


@contextmanager
def protected_egress_scope(context: EgressContext) -> Iterator[None]:
    """Mark an active protected mission-data scope to catch direct-call bypasses."""
    token = _ACTIVE_PROTECTED_CONTEXT.set(context)
    try:
        yield
    finally:
        _ACTIVE_PROTECTED_CONTEXT.reset(token)


@contextmanager
def gateway_verified_scope() -> Iterator[None]:
    """Internal marker set only by llm_gateway after evaluate_egress() succeeds."""
    token = _GATEWAY_VERIFIED.set(True)
    try:
        yield
    finally:
        _GATEWAY_VERIFIED.reset(token)


def enforce_transport_egress_guard(
    *,
    endpoint_url: str,
    processing_kind: ProcessingKind = "chat_completion",
    local_only_setting: bool = False,
) -> None:
    """Low-level transport guard blocking direct-call bypasses and external calls in local-only mode."""
    active_ctx = _ACTIVE_PROTECTED_CONTEXT.get()
    local_only = bool(local_only_setting or (active_ctx and active_ctx.local_only))
    if local_only and not is_loopback_endpoint(endpoint_url):
        decision = EgressDecision(
            allowed=False,
            reason_code="local_only_external_denied",
            data_class=active_ctx.data_class if active_ctx else "unknown",
            dataset_ids=list(active_ctx.dataset_ids) if active_ctx else [],
            policy_revision="transport-guard",
            provider="external",
            model_id="unknown",
            processing_kind=processing_kind,
            redaction_applied=False,
            decided_at_utc=datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        )
        raise LLMEgressDeniedError(
            "LLM egress denied: external endpoint blocked in local-only mode",
            decision=decision,
        )
    if active_ctx is not None and not _GATEWAY_VERIFIED.get():
        decision = EgressDecision(
            allowed=False,
            reason_code="direct_call_bypass_denied",
            data_class=active_ctx.data_class,
            dataset_ids=list(active_ctx.dataset_ids),
            policy_revision="transport-guard",
            provider="direct",
            model_id="unknown",
            processing_kind=processing_kind,
            redaction_applied=False,
            decided_at_utc=datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        )
        raise LLMEgressDeniedError(
            "LLM egress denied: direct backend/embedding call bypassed gateway policy",
            decision=decision,
        )
