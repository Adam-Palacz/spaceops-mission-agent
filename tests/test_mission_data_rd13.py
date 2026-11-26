"""RD1.3 mission isolation, ground-truth separation, and model egress control tests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from apps import llm_gateway
from apps.common import reranker
from apps.llm_backends import http_common, nim_client
from apps.llm_gateway_errors import (
    LLMEgressDeniedError,
    LLMGatewayTimeoutError,
)
from apps.mcp.kb_server import index_kb as kb_index
from apps.mcp.kb_server import main as kb_main
from apps.mcp.telemetry_server import main as telemetry_mcp_main
from apps.mission_data import (
    AllowedProcessing,
    DatasetScope,
    EgressApprovalRecord,
    EgressApprovalRegistry,
    EgressApprovalRegistryDocument,
    EgressContext,
    GroundTruthRecord,
    GroundTruthStore,
    InvestigationTelemetryView,
    IsolationError,
    OPSSAT_AD_DATASET_ID,
    OPSSAT_DISTINCT_DATASET_IDS,
    OPSSAT_MISSION_ID,
    OPSSAT_REENTRY_UHF_DATASET_ID,
    PredictionRecord,
    PredictionStore,
    ToolAccessError,
    evaluate_egress,
    inherit_egress_classification,
    is_loopback_endpoint,
    load_egress_approvals,
    protected_egress_scope,
    require_tool_access,
    validate_prompt_template_no_labels,
)
from config import settings
from prompts.registry import DECIDE_PROMPT_ID, TRIAGE_PROMPT_ID, get_prompt


def _make_approval(**overrides) -> EgressApprovalRecord:
    base = {
        "approval_id": "appr-opssat-ad-test-1",
        "policy_revision": "2026-11-26.v1",
        "dataset_id": OPSSAT_AD_DATASET_ID,
        "version_or_checksum": "sha256:test-v1",
        "approved_fields": ["channel", "value", "unit", "ts", "segment_id"],
        "purpose": "historical_read_only_triage",
        "provider": "openai",
        "approved_endpoint": "https://api.openai.com/v1/chat/completions",
        "account_id": "lab-public-benchmark",
        "model_id": "gpt-4o-mini",
        "region": "us",
        "allowed_processing": AllowedProcessing(chat_completion=True),
        "owner": "mission-data-lead",
        "review_date": "2026-11-26T00:00:00Z",
        "expires_at": "2026-12-26T00:00:00Z",
        "license_spdx": "CC-BY-4.0",
        "attribution": "ESA OPSSAT-AD Zenodo 10.5281/zenodo.12588359",
        "confidentiality_export_assessment": "public-historical-only",
        "provider_retention_assessment": "zero-training-verified",
        "redaction_required": False,
        "redaction_rules": [],
    }
    base.update(overrides)
    return EgressApprovalRecord(**base)


def _make_registry(*records: EgressApprovalRecord) -> EgressApprovalRegistry:
    return EgressApprovalRegistry(
        EgressApprovalRegistryDocument(
            schema_version="1",
            policy_revision="2026-11-26.v1",
            default_decision="deny",
            approvals=list(records),
        )
    )


def _make_historical_context(**overrides) -> EgressContext:
    base = {
        "data_class": "historical_public",
        "dataset_ids": [OPSSAT_AD_DATASET_ID],
        "version_or_checksum": "sha256:test-v1",
        "purpose": "historical_read_only_triage",
        "account_id": "lab-public-benchmark",
        "region": "us",
        "processing_kind": "chat_completion",
        "payload_fields": {"channel": "CADC0872", "value": 0.42, "unit": None},
    }
    base.update(overrides)
    return EgressContext(**base)


# ---------------------------------------------------------------------------
# Isolation & Ground-Truth Separation Tests
# ---------------------------------------------------------------------------


def test_opssat_distinct_dataset_ids_documented_and_distinct() -> None:
    assert OPSSAT_MISSION_ID == "ops-sat"
    assert OPSSAT_AD_DATASET_ID != OPSSAT_REENTRY_UHF_DATASET_ID
    assert set(OPSSAT_DISTINCT_DATASET_IDS) == {
        OPSSAT_AD_DATASET_ID,
        OPSSAT_REENTRY_UHF_DATASET_ID,
    }


def test_investigation_query_returns_values_and_units_only_and_strips_labels() -> None:
    view = InvestigationTelemetryView(
        [
            {
                "event_id": "opssat-ad:CADC0872:2024-01-01T00:00:00Z",
                "ts": "2024-01-01T00:00:00Z",
                "channel": "CADC0872",
                "value": 12.5,
                "unit": "uT",
                "subsystem": "ADCS",
                "source": "telemetry",
                "anomaly": True,
                "train": 1,
                "ground_truth": "reaction_wheel_fault",
                "reference_answer": "do-not-expose",
                "metadata": {
                    "mission_id": OPSSAT_MISSION_ID,
                    "dataset_id": OPSSAT_AD_DATASET_ID,
                    "license": "CC-BY-4.0",
                    "sample_kind": "real",
                    "segment_id": "seg-1",
                    "is_anomaly": True,
                    "rare_nominal": False,
                },
            }
        ]
    )
    rows = view.query(
        time_range_start="2024-01-01T00:00:00Z",
        time_range_end="2024-01-01T01:00:00Z",
        mission_id=OPSSAT_MISSION_ID,
        dataset_ids=[OPSSAT_AD_DATASET_ID],
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["channel"] == "CADC0872"
    assert row["value"] == 12.5
    assert row["unit"] == "uT"
    for forbidden in ("anomaly", "train", "ground_truth", "reference_answer"):
        assert forbidden not in row
    assert "is_anomaly" not in row["metadata"]
    assert "rare_nominal" not in row["metadata"]
    assert row["metadata"]["dataset_id"] == OPSSAT_AD_DATASET_ID


def test_cross_dataset_and_mission_only_isolation_and_unscoped_safety() -> None:
    records = [
        {
            "ts": "2025-02-14T10:00:00Z",
            "channel": "temp_plate_1",
            "value": 42.1,
            "unit": "C",
        },
        {
            "ts": "2025-02-14T10:00:00Z",
            "channel": "CADC0872",
            "value": 1.2,
            "unit": None,
            "metadata": {
                "mission_id": OPSSAT_MISSION_ID,
                "dataset_id": OPSSAT_AD_DATASET_ID,
                "license": "CC-BY-4.0",
                "sample_kind": "real",
                "segment_id": "seg-1",
            },
        },
        {
            "ts": "2025-02-14T10:00:00Z",
            "channel": "batt_v",
            "value": 8.1,
            "unit": "V",
            "metadata": {
                "mission_id": OPSSAT_MISSION_ID,
                "dataset_id": OPSSAT_REENTRY_UHF_DATASET_ID,
                "license": "LicenseRef-Unresolved",
                "sample_kind": "real",
                "segment_id": "seg-1",
            },
        },
    ]
    view = InvestigationTelemetryView(records)

    # Unscoped query returns legacy synthetic fixture rows only; never real datasets.
    unscoped = view.query(
        time_range_start="2025-02-14T09:00:00Z",
        time_range_end="2025-02-14T11:00:00Z",
    )
    assert [r["channel"] for r in unscoped] == ["temp_plate_1"]

    # Mission name alone without dataset_ids returns empty.
    mission_only = view.query(
        time_range_start="2025-02-14T09:00:00Z",
        time_range_end="2025-02-14T11:00:00Z",
        mission_id=OPSSAT_MISSION_ID,
    )
    assert mission_only == []

    # Single dataset query sees only that dataset.
    ad_only = view.query(
        time_range_start="2025-02-14T09:00:00Z",
        time_range_end="2025-02-14T11:00:00Z",
        mission_id=OPSSAT_MISSION_ID,
        dataset_ids=[OPSSAT_AD_DATASET_ID],
    )
    assert [r["channel"] for r in ad_only] == ["CADC0872"]

    # Wrong-mission query returns empty even with valid dataset_id.
    wrong_mission = view.query(
        time_range_start="2025-02-14T09:00:00Z",
        time_range_end="2025-02-14T11:00:00Z",
        mission_id="other-mission",
        dataset_ids=[OPSSAT_AD_DATASET_ID],
    )
    assert wrong_mission == []

    # Cross-dataset query succeeds only when caller explicitly names both dataset ids.
    both = view.query(
        time_range_start="2025-02-14T09:00:00Z",
        time_range_end="2025-02-14T11:00:00Z",
        scopes=[
            DatasetScope(mission_id=OPSSAT_MISSION_ID, dataset_id=OPSSAT_AD_DATASET_ID),
            DatasetScope(
                mission_id=OPSSAT_MISSION_ID, dataset_id=OPSSAT_REENTRY_UHF_DATASET_ID
            ),
        ],
    )
    assert {r["channel"] for r in both} == {"CADC0872", "batt_v"}


def test_investigation_tool_cannot_read_ground_truth_and_scoring_requires_closed_run(
    tmp_path: Path,
) -> None:
    telemetry_dir = tmp_path / "telemetry"
    gt_dir = tmp_path / "ground_truth"
    telemetry_dir.mkdir()
    gt_dir.mkdir()

    # Ground-truth store refuses to share directory with telemetry store.
    with pytest.raises(IsolationError):
        GroundTruthStore(storage_dir=telemetry_dir, telemetry_dir=telemetry_dir)

    gt_store = GroundTruthStore(
        [
            GroundTruthRecord(
                mission_id=OPSSAT_MISSION_ID,
                dataset_id=OPSSAT_AD_DATASET_ID,
                segment_id="seg-42",
                label_kind="anomaly",
                label_value=True,
                split="test",
                annotation_source="opssat-ad-csv",
                provenance_version="1.0",
            )
        ],
        storage_dir=gt_dir,
        telemetry_dir=telemetry_dir,
    )

    # Negative test: investigation role cannot read ground truth or join labels.
    with pytest.raises(ToolAccessError):
        gt_store.read_labels(
            role="investigation",
            mission_id=OPSSAT_MISSION_ID,
            dataset_id=OPSSAT_AD_DATASET_ID,
        )
    with pytest.raises(ToolAccessError):
        require_tool_access("read_ground_truth", "investigation")

    pred_store = PredictionStore()
    pred_store.add(
        PredictionRecord(
            run_id="run-100",
            mission_id=OPSSAT_MISSION_ID,
            dataset_id=OPSSAT_AD_DATASET_ID,
            segment_id="seg-42",
            prediction={"score": 0.91},
            status="open",
        )
    )
    # Re-entry prediction sharing segment_id must never join OPSSAT-AD labels.
    pred_store.add(
        PredictionRecord(
            run_id="run-100",
            mission_id=OPSSAT_MISSION_ID,
            dataset_id=OPSSAT_REENTRY_UHF_DATASET_ID,
            segment_id="seg-42",
            prediction={"score": 0.12},
            status="open",
        )
    )

    # Scoring fails closed while run_id is open.
    with pytest.raises(IsolationError, match="still open"):
        gt_store.join_predictions_to_labels(
            role="evaluator",
            run_id="run-100",
            predictions=pred_store.for_run("run-100"),
        )

    # After closing run_id, evaluator joins strictly matching (mission_id, dataset_id).
    closed_preds = pred_store.close_run("run-100", closed_at="2026-11-26T09:00:00Z")
    joined = gt_store.join_predictions_to_labels(
        role="evaluator",
        run_id="run-100",
        predictions=closed_preds,
    )
    assert len(joined) == 1
    assert joined[0].dataset_id == OPSSAT_AD_DATASET_ID
    assert joined[0].ground_truth.label_value is True


def test_telemetry_mcp_delegates_to_isolated_view(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "mixed.ndjson").write_text(
        json.dumps(
            {
                "ts": "2025-02-14T10:00:00Z",
                "channel": "temp_plate_1",
                "value": 42.1,
                "unit": "C",
                "anomaly": True,
            }
        )
        + "\n"
        + json.dumps(
            {
                "ts": "2025-02-14T10:00:00Z",
                "channel": "CADC0872",
                "value": 0.5,
                "unit": None,
                "train": 0,
                "metadata": {
                    "mission_id": OPSSAT_MISSION_ID,
                    "dataset_id": OPSSAT_AD_DATASET_ID,
                    "license": "CC-BY-4.0",
                    "sample_kind": "real",
                    "segment_id": "seg-1",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(telemetry_mcp_main, "DATA_TELEMETRY", tmp_path)

    unscoped = telemetry_mcp_main.query_telemetry(
        "2025-02-14T09:00:00Z", "2025-02-14T11:00:00Z"
    )
    assert len(unscoped) == 1
    assert unscoped[0]["channel"] == "temp_plate_1"
    assert "anomaly" not in unscoped[0]

    scoped = telemetry_mcp_main.query_telemetry(
        "2025-02-14T09:00:00Z",
        "2025-02-14T11:00:00Z",
        mission_id=OPSSAT_MISSION_ID,
        dataset_ids=[OPSSAT_AD_DATASET_ID],
    )
    assert len(scoped) == 1
    assert scoped[0]["channel"] == "CADC0872"
    assert "train" not in scoped[0]


def test_registered_prompt_templates_do_not_interpolate_labels() -> None:
    for prompt_id in (TRIAGE_PROMPT_ID, DECIDE_PROMPT_ID):
        validate_prompt_template_no_labels(get_prompt(prompt_id).text)
    with pytest.raises(IsolationError):
        validate_prompt_template_no_labels("Inspect {channel} label={anomaly_label}")
    with pytest.raises(IsolationError):
        validate_prompt_template_no_labels("Hint: {record[ground_truth]}")


# ---------------------------------------------------------------------------
# Egress Policy, Local-Only Mode, Redaction, Fallback, and Bypass Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:8005/v1/chat/completions", True),
        ("http://127.0.0.1:8005/v1/health/ready", True),
        ("http://[::1]:8005/v1/chat/completions", True),
        ("https://api.openai.com/v1/chat/completions", False),
        ("http://localhost.evil.com/v1/chat/completions", False),
        ("http://localhost@evil.com/v1/chat/completions", False),
        ("http://0.0.0.0:8005/v1/chat/completions", False),
        ("file:///etc/passwd", False),
    ],
)
def test_loopback_endpoint_detection(url: str, expected: bool) -> None:
    assert is_loopback_endpoint(url) is expected


def test_default_egress_approvals_file_is_default_deny() -> None:
    registry = load_egress_approvals()
    ctx = _make_historical_context()
    req = ctx.to_request(
        provider="openai",
        model_id="gpt-4o-mini",
        endpoint_url="https://api.openai.com/v1/chat/completions",
        outbound_text="Analyze CADC0872 value=0.42",
        now_utc=datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc),
    )
    res = evaluate_egress(req, registry)
    assert res.decision.allowed is False
    assert res.decision.reason_code == "unapproved_dataset_or_target"


def test_approved_historical_public_request_and_redaction_pass() -> None:
    approval = _make_approval(
        redaction_required=True,
        redaction_rules=["mask_emails", "mask_absolute_paths"],
    )
    registry = _make_registry(approval)
    ctx = _make_historical_context(
        payload_fields={"channel": "CADC0872", "value": 0.42, "unit": None}
    )
    req = ctx.to_request(
        provider="openai",
        model_id="gpt-4o-mini",
        endpoint_url="https://api.openai.com/v1/chat/completions",
        outbound_text="Analyze CADC0872 note from ops@example.test at /var/log/sim.log",
        now_utc=datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc),
    )
    res = evaluate_egress(req, registry)
    assert res.decision.allowed is True
    assert res.decision.reason_code == "approved_historical_public"
    assert res.decision.redaction_applied is True
    assert "ops@example.test" not in res.sanitized_text
    assert "/var/log/sim.log" not in res.sanitized_text
    assert "[REDACTED_EMAIL]" in res.sanitized_text
    assert "[REDACTED_PATH]" in res.sanitized_text


def test_egress_negative_cases_fail_closed() -> None:
    registry = _make_registry(_make_approval())
    valid_now = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)

    # 1. Unapproved dataset / wrong version / empty dataset_ids
    for bad_ctx in (
        _make_historical_context(dataset_ids=[OPSSAT_REENTRY_UHF_DATASET_ID]),
        _make_historical_context(version_or_checksum="sha256:wrong"),
        _make_historical_context(dataset_ids=[]),
    ):
        req = bad_ctx.to_request(
            provider="openai",
            model_id="gpt-4o-mini",
            endpoint_url="https://api.openai.com/v1/chat/completions",
            outbound_text="Analyze channel",
            now_utc=valid_now,
        )
        assert evaluate_egress(req, registry).decision.allowed is False

    # 2. Expired policy
    expired_req = _make_historical_context().to_request(
        provider="openai",
        model_id="gpt-4o-mini",
        endpoint_url="https://api.openai.com/v1/chat/completions",
        outbound_text="Analyze channel",
        now_utc=datetime(2026, 12, 26, 0, 0, tzinfo=timezone.utc),
    )
    expired_res = evaluate_egress(expired_req, registry)
    assert expired_res.decision.allowed is False
    assert expired_res.decision.reason_code == "approval_expired"

    # 3. Wrong provider / wrong endpoint / wrong model / unapproved processing kind
    for provider, endpoint, model, proc_kind in (
        (
            "cursor_sh",
            "https://api.cursor.sh/v1/chat/completions",
            "gpt-4o-mini",
            "chat_completion",
        ),
        (
            "openai",
            "https://evil.example/v1/chat/completions",
            "gpt-4o-mini",
            "chat_completion",
        ),
        (
            "openai",
            "https://api.openai.com/v1/chat/completions",
            "gpt-4.1",
            "chat_completion",
        ),
        (
            "openai",
            "https://api.openai.com/v1/chat/completions",
            "gpt-4o-mini",
            "embeddings",
        ),
    ):
        req = _make_historical_context(processing_kind=proc_kind).to_request(
            provider=provider,
            model_id=model,
            endpoint_url=endpoint,
            outbound_text="Analyze channel",
            now_utc=valid_now,
        )
        assert evaluate_egress(req, registry).decision.allowed is False

    # 4. Forbidden/unapproved fields & sensitive payload
    unapproved_field_req = _make_historical_context(
        payload_fields={"channel": "CADC0872", "raw_orbit_ephemeris": "xyz"}
    ).to_request(
        provider="openai",
        model_id="gpt-4o-mini",
        endpoint_url="https://api.openai.com/v1/chat/completions",
        outbound_text="Analyze channel",
        now_utc=valid_now,
    )
    assert evaluate_egress(unapproved_field_req, registry).decision.reason_code == (
        "unapproved_payload_field"
    )

    secret_req = _make_historical_context().to_request(
        provider="openai",
        model_id="gpt-4o-mini",
        endpoint_url="https://api.openai.com/v1/chat/completions",
        outbound_text="key sk-" + "a" * 32,
        now_utc=valid_now,
    )
    assert evaluate_egress(secret_req, registry).decision.reason_code == (
        "sensitive_payload_detected"
    )

    # 5. Hidden reference / ground truth ALWAYS denied
    for gt_ctx, gt_text in (
        (_make_historical_context(contains_ground_truth=True), "Analyze channel"),
        (
            _make_historical_context(
                payload_fields={"channel": "CADC0872", "reference_answer": "fault"}
            ),
            "Analyze channel",
        ),
        (_make_historical_context(), "ground_truth: anomaly"),
    ):
        req = gt_ctx.to_request(
            provider="openai",
            model_id="gpt-4o-mini",
            endpoint_url="https://api.openai.com/v1/chat/completions",
            outbound_text=gt_text,
            now_utc=valid_now,
        )
        res = evaluate_egress(req, registry)
        assert res.decision.allowed is False
        assert res.decision.reason_code == "ground_truth_forbidden"

    # 6. Mixed source / derived summary inherits restriction and denies external
    derived = inherit_egress_classification(
        [
            EgressContext(
                data_class="synthetic_ci", dataset_ids=["lab-synthetic-telemetry"]
            ),
            _make_historical_context(),
        ]
    )
    assert derived.data_class == "mixed"
    mixed_req = derived.to_request(
        provider="openai",
        model_id="gpt-4o-mini",
        endpoint_url="https://api.openai.com/v1/chat/completions",
        outbound_text="Derived summary",
        now_utc=valid_now,
    )
    mixed_res = evaluate_egress(mixed_req, registry)
    assert mixed_res.decision.allowed is False
    assert mixed_res.decision.reason_code == "forbidden_data_class:mixed"

    # 7. Approval itself cannot allowlist ground-truth keys or expired review window
    with pytest.raises(ValidationError):
        _make_approval(approved_fields=["channel", "ground_truth"])
    with pytest.raises(ValidationError):
        _make_approval(
            review_date="2026-12-26T00:00:00Z", expires_at="2026-11-26T00:00:00Z"
        )


def test_gateway_blocks_fallback_in_local_only_and_logs_sanitized_audit(
    monkeypatch, caplog
) -> None:
    monkeypatch.setattr(settings, "llm_backend", "gpu")
    monkeypatch.setattr(settings, "gpu_llm_base_url", "http://localhost:8005")
    monkeypatch.setattr(settings, "gpu_llm_model_id", "local-slm")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key-should-not-be-used")
    monkeypatch.setattr(settings, "llm_local_only_mode", True)
    monkeypatch.setattr(
        llm_gateway, "can_use_gpu_backend", lambda: (False, "gpu_unhealthy")
    )

    called_openai = False

    def fail_if_called(**_kwargs):
        nonlocal called_openai
        called_openai = True
        raise AssertionError("openai fallback must never be called in local-only mode")

    monkeypatch.setattr(
        llm_gateway,
        "get_backend_generator",
        lambda name: fail_if_called if name == "openai" else fail_if_called,
    )

    secret_marker = "RAW_PROMPT_SENTINEL_DO_NOT_LOG"
    with caplog.at_level(logging.INFO, logger="apps.llm_gateway"):
        with pytest.raises(LLMEgressDeniedError):
            llm_gateway.generate(
                prompt=f"Analyze telemetry {secret_marker}",
                node="triage",
                egress_context=_make_historical_context(local_only=True),
            )
    assert called_openai is False
    assert secret_marker not in caplog.text
    assert "llm_egress_decision" in caplog.text


def test_gateway_blocks_unapproved_gpu_timeout_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_backend", "gpu")
    monkeypatch.setattr(settings, "gpu_llm_base_url", "http://localhost:8005")
    monkeypatch.setattr(settings, "gpu_llm_model_id", "local-slm")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key")
    monkeypatch.setattr(settings, "llm_local_only_mode", False)
    monkeypatch.setattr(llm_gateway, "can_use_gpu_backend", lambda: (True, "ok"))

    def timeout_gpu(**_kwargs):
        raise LLMGatewayTimeoutError("timed out")

    def fail_openai(**_kwargs):
        raise AssertionError("unapproved fallback to openai must not execute")

    monkeypatch.setattr(
        llm_gateway,
        "get_backend_generator",
        lambda name: timeout_gpu if name == "gpu" else fail_openai,
    )

    with pytest.raises(LLMEgressDeniedError, match="unapproved fallback"):
        llm_gateway.generate(
            prompt="Analyze CADC0872",
            node="triage",
            egress_context=_make_historical_context(allow_fallback=False),
        )


def test_direct_call_bypasses_embeddings_and_reranker_fail_closed(monkeypatch) -> None:
    # 1. Direct http_common.chat_completion bypass blocked in local-only mode.
    monkeypatch.setattr(settings, "llm_local_only_mode", True)
    with pytest.raises(LLMEgressDeniedError):
        http_common.chat_completion(
            endpoint="https://api.openai.com/v1/chat/completions",
            api_key="sk-test",
            model_id="gpt-4o-mini",
            prompt="hello",
            temperature=0,
            timeout_s=5.0,
        )

    # 2. Direct NIM health check to non-loopback blocked in local-only mode.
    with pytest.raises(LLMEgressDeniedError):
        nim_client.check_nim_health(base_url="https://remote-nim.example:8005")

    # 3. Direct call inside protected_egress_scope blocked even to loopback if gateway bypassed.
    monkeypatch.setattr(settings, "llm_local_only_mode", False)
    with protected_egress_scope(_make_historical_context()):
        with pytest.raises(LLMEgressDeniedError, match="bypassed gateway"):
            http_common.chat_completion(
                endpoint="http://localhost:8005/v1/chat/completions",
                api_key="",
                model_id="local-slm",
                prompt="hello",
                temperature=0,
                timeout_s=5.0,
            )

    # 4. Cached KB embeddings and index_kb blocked in local-only mode.
    monkeypatch.setattr(settings, "llm_local_only_mode", True)
    monkeypatch.setattr(kb_main, "_embeddings", object())
    with pytest.raises(LLMEgressDeniedError):
        kb_main._get_embeddings()
    with pytest.raises(LLMEgressDeniedError):
        kb_index.main()

    # 5. LLM reranker fails closed on egress denial (never silently fails open).
    monkeypatch.setattr(settings, "llm_backend", "openai")
    with pytest.raises(LLMEgressDeniedError):
        reranker.rerank_chunks(
            "voltage",
            [{"doc_id": "rb-1", "content": "check bus voltage"}],
            mode="llm",
        )


def test_protected_scope_cannot_be_bypassed_or_downgraded_via_gateway_or_reranker(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "llm_backend", "openai")
    monkeypatch.setattr(settings, "openai_base_url", "https://api.openai.com")
    monkeypatch.setattr(settings, "llm_local_only_mode", False)

    def fail_if_called(**_kwargs):
        raise AssertionError(
            "external backend must not run under denied protected scope"
        )

    monkeypatch.setattr(
        llm_gateway, "get_backend_generator", lambda _name: fail_if_called
    )

    # Protected scope with egress_context=None must still evaluate and deny external call.
    with protected_egress_scope(EgressContext(data_class="private")):
        with pytest.raises(LLMEgressDeniedError):
            llm_gateway.generate(prompt="Analyze private record", node="triage")
        # Inner synthetic_ci context must NOT downgrade outer private restriction.
        with pytest.raises(LLMEgressDeniedError):
            llm_gateway.generate(
                prompt="Analyze private record",
                node="triage",
                egress_context=EgressContext(data_class="synthetic_ci"),
            )
        # LLM reranker inside protected scope must also fail closed without explicit context.
        with pytest.raises(LLMEgressDeniedError):
            reranker.rerank_chunks(
                "voltage",
                [{"doc_id": "rb-1", "content": "check bus voltage"}],
                mode="llm",
            )


def test_approved_gpu_fallback_updates_egress_decision_and_redacts(
    tmp_path: Path, monkeypatch
) -> None:
    approvals_file = tmp_path / "approvals.json"
    approval = _make_approval(
        redaction_required=True,
        redaction_rules=["mask_emails"],
    )
    approvals_file.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "policy_revision": "2026-11-26.v1",
                "default_decision": "deny",
                "approvals": [approval.model_dump()],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(settings, "llm_backend", "gpu")
    monkeypatch.setattr(settings, "gpu_llm_base_url", "http://localhost:8005")
    monkeypatch.setattr(settings, "gpu_llm_model_id", "local-slm")
    monkeypatch.setattr(settings, "openai_base_url", "https://api.openai.com")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key")
    monkeypatch.setattr(settings, "llm_local_only_mode", False)
    monkeypatch.setattr(
        llm_gateway, "can_use_gpu_backend", lambda: (False, "gpu_unhealthy")
    )

    captured_prompt: list[str] = []

    def fake_openai(*, prompt: str, model_id: str, temperature: float):
        captured_prompt.append(prompt)
        return {
            "content": "ADCS low",
            "model_id": model_id,
            "backend_actual": "openai",
            "latency_ms": 12,
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setattr(llm_gateway, "get_backend_generator", lambda _name: fake_openai)

    result = llm_gateway.generate(
        prompt="Analyze CADC0872 contact ops@example.test",
        node="triage",
        model_id="gpt-4o-mini",
        egress_context=_make_historical_context(
            allow_fallback=True,
            approvals_path=str(approvals_file),
        ),
    )
    assert result["fallback_used"] is True
    assert result["backend_actual"] == "openai"
    assert "[REDACTED_EMAIL]" in captured_prompt[0]
    assert "ops@example.test" not in captured_prompt[0]
    decision = result["egress_decision"]
    assert decision["provider"] == "openai"
    assert decision["approval_id"] == approval.approval_id
    assert decision["redaction_applied"] is True


def test_isolation_and_inheritance_hardening_edge_cases(tmp_path: Path) -> None:
    view = InvestigationTelemetryView(
        [
            {
                "ts": "2025-02-14T10:00:00Z",
                "channel": "temp_plate_1",
                "value": 42.1,
                "unit": "C",
            },
            {
                "ts": "2025-02-14T10:00:00Z",
                "channel": "CADC0872",
                "value": 1.2,
                "metadata": {
                    "mission_id": OPSSAT_MISSION_ID,
                    "dataset_id": OPSSAT_AD_DATASET_ID,
                    "sample_kind": "REAL",
                },
            },
        ]
    )
    # Empty dataset_ids must not fall back to legacy unscoped records.
    assert (
        view.query(
            time_range_start="2025-02-14T09:00:00Z",
            time_range_end="2025-02-14T11:00:00Z",
            dataset_ids=[],
        )
        == []
    )
    # dataset_ids without mission_id returns empty (composite key enforced).
    assert (
        view.query(
            time_range_start="2025-02-14T09:00:00Z",
            time_range_end="2025-02-14T11:00:00Z",
            dataset_ids=[OPSSAT_AD_DATASET_ID],
        )
        == []
    )
    # Uppercase REAL sample_kind never leaks into unscoped query.
    unscoped = view.query(
        time_range_start="2025-02-14T09:00:00Z",
        time_range_end="2025-02-14T11:00:00Z",
    )
    assert [r["channel"] for r in unscoped] == ["temp_plate_1"]

    # Reverse parent containment in GroundTruthStore rejected.
    telemetry_dir = tmp_path / "telemetry"
    telemetry_dir.mkdir()
    with pytest.raises(IsolationError):
        GroundTruthStore(storage_dir=tmp_path, telemetry_dir=telemetry_dir)

    # inherit_egress_classification clears version when any source is unversioned
    # and propagates ground-truth taint from payload_fields.
    derived = inherit_egress_classification(
        [
            _make_historical_context(version_or_checksum="sha256:v1"),
            _make_historical_context(
                version_or_checksum=None,
                payload_fields={"ground_truth": "fault"},
            ),
        ]
    )
    assert derived.version_or_checksum is None
    assert derived.contains_ground_truth is True
