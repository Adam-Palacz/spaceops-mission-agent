"""Mission/dataset isolation and telemetry vs. ground-truth separation (RD1.3).

Design rules:
- Isolation key is ``(mission_id, dataset_id)``, never mission name alone.
- OPS-SAT labeled segments (``opssat-ad``) and the May 2024 re-entry UHF campaign
  (``opssat-reentry-uhf``) belong to the same mission (``ops-sat``) and MUST
  never share labels or cross-join.
- Investigation tools return engineering values, units, and non-label provenance
  only; they cannot read ground-truth stores or annotation fields.
- Evaluator tools can read ground truth and join predictions only after the
  prediction run is explicitly closed.
"""

from __future__ import annotations

import json
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from apps.contracts.v1 import ContractBase
from apps.mission_data.provenance import RESERVED_METADATA_KEYS, require_non_blank

OPSSAT_MISSION_ID = "ops-sat"
OPSSAT_AD_DATASET_ID = "opssat-ad"
OPSSAT_REENTRY_UHF_DATASET_ID = "opssat-reentry-uhf"
OPSSAT_DISTINCT_DATASET_IDS: tuple[str, str] = (
    OPSSAT_AD_DATASET_ID,
    OPSSAT_REENTRY_UHF_DATASET_ID,
)

ToolRole = Literal["investigation", "evaluator"]

INVESTIGATION_TOOL_ALLOWLIST: frozenset[str] = frozenset(
    {
        "query_telemetry",
        "search_runbooks",
        "search_postmortems",
    }
)
EVALUATION_TOOL_ALLOWLIST: frozenset[str] = frozenset(
    {
        "read_ground_truth",
        "join_predictions_to_labels",
    }
)

INVESTIGATION_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "event_id",
        "ts",
        "channel",
        "value",
        "unit",
        "subsystem",
        "source",
        "metadata",
    }
)

FORBIDDEN_LABEL_KEYS: frozenset[str] = frozenset(
    {
        "label",
        "labels",
        "anomaly",
        "is_anomaly",
        "anomaly_label",
        "ground_truth",
        "rare_nominal",
        "is_rare_nominal",
        "telecommand_label",
        "reference_answer",
        "hidden_reference",
        "expected_root_cause",
        "expected_label",
        "train",
        "is_train",
        "split",
        "target",
        "class",
        "class_label",
        "annotation",
        "annotations",
    }
)


class IsolationError(ValueError):
    """Raised when mission/dataset isolation or scoring closure rules are violated."""


class ToolAccessError(PermissionError):
    """Raised when a caller role invokes a tool outside its allowlist."""


def require_tool_access(tool_name: str, role: ToolRole) -> None:
    """Fail closed unless tool_name is allowlisted for the caller role."""
    cleaned = require_non_blank(tool_name, "tool_name")
    allowed = (
        INVESTIGATION_TOOL_ALLOWLIST
        if role == "investigation"
        else EVALUATION_TOOL_ALLOWLIST
    )
    if cleaned not in allowed:
        raise ToolAccessError(f"tool {cleaned!r} is not permitted for role {role!r}")


def find_forbidden_label_keys(obj: Any, *, prefix: str = "") -> list[str]:
    """Recursively return dotted paths of any forbidden ground-truth/label keys."""
    found: list[str] = []
    if isinstance(obj, Mapping):
        for raw_key, value in obj.items():
            key_str = str(raw_key)
            key_path = f"{prefix}.{key_str}" if prefix else key_str
            if key_str.strip().lower() in FORBIDDEN_LABEL_KEYS:
                found.append(key_path)
            found.extend(find_forbidden_label_keys(value, prefix=key_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(find_forbidden_label_keys(item, prefix=f"{prefix}[{idx}]"))
    return found


def validate_prompt_template_no_labels(template_text: str) -> None:
    """Reject prompt templates that interpolate any ground-truth or label field."""
    formatter = string.Formatter()
    forbidden_refs: list[str] = []
    for _literal, field_name, _format_spec, _conversion in formatter.parse(
        template_text
    ):
        if not field_name:
            continue
        segments = field_name.replace("[", ".").replace("]", "").strip().split(".")
        for seg in segments:
            cleaned = seg.strip().strip("'\"").lower()
            if cleaned in FORBIDDEN_LABEL_KEYS:
                forbidden_refs.append(field_name)
                break
    if forbidden_refs:
        raise IsolationError(
            f"prompt template must not interpolate label fields: {sorted(set(forbidden_refs))}"
        )


class DatasetScope(ContractBase):
    """Canonical isolation key: mission_id plus dataset_id."""

    mission_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)

    @field_validator("mission_id", "dataset_id")
    @classmethod
    def reject_blank(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    def key(self) -> tuple[str, str]:
        return (self.mission_id, self.dataset_id)


def _validate_record_locator(
    segment_id: str | None,
    time_range_start: str | None,
    time_range_end: str | None,
) -> None:
    has_segment = bool(segment_id)
    has_start = bool(time_range_start)
    has_end = bool(time_range_end)
    if has_start != has_end:
        raise ValueError(
            "time_range_start and time_range_end must both be set when using a time key"
        )
    if not has_segment and not (has_start and has_end):
        raise ValueError(
            "record requires segment_id or a (time_range_start, time_range_end) key"
        )
    if has_start and has_end and str(time_range_start) > str(time_range_end):
        raise ValueError("time_range_start must be <= time_range_end")


def _normalize_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class GroundTruthRecord(ContractBase):
    """Evaluator-only annotation record stored separately from telemetry values."""

    mission_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    segment_id: str | None = None
    time_range_start: str | None = None
    time_range_end: str | None = None
    label_kind: Literal["anomaly", "rare_nominal", "telecommand", "reference_answer"]
    label_value: bool | int | float | str
    split: Literal["train", "test"] | None = None
    annotation_source: str = Field(..., min_length=1)
    provenance_version: str = Field(..., min_length=1)

    @field_validator(
        "mission_id", "dataset_id", "annotation_source", "provenance_version"
    )
    @classmethod
    def reject_blank_required(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    @field_validator("segment_id", "time_range_start", "time_range_end")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        return _normalize_optional_str(value)

    @model_validator(mode="after")
    def validate_locator(self) -> GroundTruthRecord:
        _validate_record_locator(
            self.segment_id, self.time_range_start, self.time_range_end
        )
        return self

    def join_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.mission_id,
            self.dataset_id,
            self.segment_id or "",
            self.time_range_start or "",
            self.time_range_end or "",
        )


class PredictionRecord(ContractBase):
    """Stored prediction emitted by an investigation or detector run."""

    run_id: str = Field(..., min_length=1)
    mission_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    segment_id: str | None = None
    time_range_start: str | None = None
    time_range_end: str | None = None
    prediction: dict[str, Any] = Field(default_factory=dict)
    status: Literal["open", "closed"] = "open"
    closed_at: str | None = None

    @field_validator("run_id", "mission_id", "dataset_id")
    @classmethod
    def reject_blank_required(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    @field_validator("segment_id", "time_range_start", "time_range_end", "closed_at")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        return _normalize_optional_str(value)

    @model_validator(mode="after")
    def validate_locator_and_closure(self) -> PredictionRecord:
        _validate_record_locator(
            self.segment_id, self.time_range_start, self.time_range_end
        )
        if self.status == "closed" and not self.closed_at:
            raise ValueError("closed prediction requires non-blank closed_at")
        return self

    def join_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.mission_id,
            self.dataset_id,
            self.segment_id or "",
            self.time_range_start or "",
            self.time_range_end or "",
        )


class JoinedScoringRecord(ContractBase):
    """Post-run join between a closed prediction and its matching ground truth."""

    run_id: str
    mission_id: str
    dataset_id: str
    prediction: PredictionRecord
    ground_truth: GroundTruthRecord


def sanitize_telemetry_for_investigation(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Return strictly allowlisted telemetry values, units, and non-label provenance."""
    out: dict[str, Any] = {}
    raw_ts = record.get("ts") if "ts" in record else record.get("timestamp")
    raw_channel = (
        record.get("channel") if "channel" in record else record.get("channel_id")
    )
    if raw_ts is not None:
        out["ts"] = raw_ts
    if raw_channel is not None:
        out["channel"] = raw_channel
    for key in ("event_id", "value", "unit", "subsystem", "source"):
        if key in record:
            val = record[key]
            if key == "value" and find_forbidden_label_keys(val):
                continue
            out[key] = val
    raw_meta = record.get("metadata")
    if isinstance(raw_meta, Mapping):
        clean_meta = {
            k: raw_meta[k]
            for k in RESERVED_METADATA_KEYS
            if k in raw_meta and isinstance(raw_meta[k], (str, int, float, bool))
        }
        if clean_meta:
            out["metadata"] = clean_meta
    return out


def _record_scope(
    record: Mapping[str, Any],
) -> tuple[str | None, str | None, str | None]:
    meta = record.get("metadata")
    if not isinstance(meta, Mapping):
        return (None, None, None)
    mission = _normalize_optional_str(
        str(meta["mission_id"]) if meta.get("mission_id") is not None else None
    )
    dataset = _normalize_optional_str(
        str(meta["dataset_id"]) if meta.get("dataset_id") is not None else None
    )
    sample_kind = _normalize_optional_str(
        str(meta["sample_kind"]) if meta.get("sample_kind") is not None else None
    )
    return (mission, dataset, sample_kind)


def _is_legacy_unscoped_record(record: Mapping[str, Any]) -> bool:
    """True for committed synthetic fixture rows without isolated real-dataset scope."""
    mission, dataset, sample_kind = _record_scope(record)
    lowered_kind = (sample_kind or "").lower()
    if lowered_kind == "real":
        return False
    if mission is not None and lowered_kind != "synthetic":
        return False
    if dataset is None:
        return True
    return lowered_kind == "synthetic"


class InvestigationTelemetryView:
    """Read-only telemetry view used by investigation tools.

    Never holds or accesses ground-truth records. Enforces ``(mission_id, dataset_id)``
    isolation and strips any non-allowlisted fields before returning measurements.
    """

    def __init__(self, records: Sequence[Mapping[str, Any]]) -> None:
        self._records: list[dict[str, Any]] = [
            dict(r) for r in records if isinstance(r, Mapping)
        ]

    @classmethod
    def from_ndjson_dir(cls, data_dir: Path) -> InvestigationTelemetryView:
        records: list[dict[str, Any]] = []
        if data_dir.exists():
            for path in sorted(data_dir.glob("*.ndjson")):
                with path.open(encoding="utf-8") as handle:
                    for line in handle:
                        stripped = line.strip()
                        if not stripped:
                            continue
                        try:
                            parsed = json.loads(stripped)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(parsed, dict):
                            records.append(parsed)
        return cls(records)

    def query(
        self,
        *,
        time_range_start: str,
        time_range_end: str,
        channels: Sequence[str] | None = None,
        mission_id: str | None = None,
        dataset_ids: Sequence[str] | None = None,
        scopes: Sequence[DatasetScope] | None = None,
        role: ToolRole = "investigation",
    ) -> list[dict[str, Any]]:
        require_tool_access("query_telemetry", role)
        start = _normalize_optional_str(time_range_start)
        end = _normalize_optional_str(time_range_end)
        if not start or not end or start > end:
            return []

        norm_mission = _normalize_optional_str(mission_id)
        norm_datasets = [
            d for d in (_normalize_optional_str(x) for x in (dataset_ids or ())) if d
        ]
        explicit_scopes: set[tuple[str, str]] | None = None
        if scopes is not None:
            explicit_scopes = {scope.key() for scope in scopes}
            if not explicit_scopes:
                return []
        elif dataset_ids is not None:
            # Composite isolation key requires both mission_id and non-empty dataset_ids.
            if not norm_mission or not norm_datasets:
                return []
        elif norm_mission is not None:
            # Mission name alone is never sufficient; caller must name dataset_id(s).
            return []

        channel_filter = set(channels) if channels else None
        out: list[dict[str, Any]] = []
        for record in self._records:
            ts = _normalize_optional_str(
                str(record.get("ts") or record.get("timestamp") or "")
            )
            if not ts or ts < start or ts > end:
                continue
            ch = record.get("channel") or record.get("channel_id")
            if channel_filter is not None and ch not in channel_filter:
                continue
            rec_mission, rec_dataset, _sample_kind = _record_scope(record)

            if explicit_scopes is not None:
                if (rec_mission, rec_dataset) not in explicit_scopes:
                    continue
            elif norm_datasets:
                if rec_dataset not in norm_datasets:
                    continue
                if norm_mission is not None and rec_mission != norm_mission:
                    continue
            else:
                if not _is_legacy_unscoped_record(record):
                    continue

            out.append(sanitize_telemetry_for_investigation(record))
        return out


class PredictionStore:
    """Store for run predictions with explicit run-closure semantics."""

    def __init__(self) -> None:
        self._records: list[PredictionRecord] = []

    def add(self, record: PredictionRecord) -> None:
        self._records.append(record)

    def close_run(
        self, run_id: str, *, closed_at: str | None = None
    ) -> list[PredictionRecord]:
        cleaned_run = require_non_blank(run_id, "run_id")
        ts = _normalize_optional_str(closed_at) or (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        updated: list[PredictionRecord] = []
        matched = False
        for item in self._records:
            if item.run_id == cleaned_run:
                matched = True
                closed_item = item.model_copy(
                    update={"status": "closed", "closed_at": ts}
                )
                updated.append(closed_item)
            else:
                updated.append(item)
        if not matched:
            raise IsolationError(f"no predictions found for run_id {cleaned_run!r}")
        self._records = updated
        return self.for_run(cleaned_run)

    def for_run(self, run_id: str) -> list[PredictionRecord]:
        cleaned_run = require_non_blank(run_id, "run_id")
        return [item for item in self._records if item.run_id == cleaned_run]


class GroundTruthStore:
    """Evaluator-only ground-truth store strictly isolated from telemetry."""

    def __init__(
        self,
        records: Sequence[GroundTruthRecord] = (),
        *,
        storage_dir: Path | None = None,
        telemetry_dir: Path | None = None,
    ) -> None:
        if storage_dir is not None and telemetry_dir is not None:
            gt_resolved = storage_dir.resolve()
            tm_resolved = telemetry_dir.resolve()
            if (
                gt_resolved == tm_resolved
                or tm_resolved in gt_resolved.parents
                or gt_resolved in tm_resolved.parents
            ):
                raise IsolationError(
                    "ground-truth store directory must be separate from telemetry directory"
                )
        self._storage_dir = storage_dir
        self._records: list[GroundTruthRecord] = list(records)

    @property
    def storage_dir(self) -> Path | None:
        return self._storage_dir

    def add(self, record: GroundTruthRecord) -> None:
        self._records.append(record)

    def read_labels(
        self,
        *,
        role: ToolRole,
        mission_id: str,
        dataset_id: str,
    ) -> list[GroundTruthRecord]:
        require_tool_access("read_ground_truth", role)
        scope = DatasetScope(mission_id=mission_id, dataset_id=dataset_id)
        return [
            item
            for item in self._records
            if item.mission_id == scope.mission_id
            and item.dataset_id == scope.dataset_id
        ]

    def join_predictions_to_labels(
        self,
        *,
        role: ToolRole,
        run_id: str,
        predictions: Sequence[PredictionRecord],
        mission_id: str | None = None,
        dataset_ids: Sequence[str] | None = None,
    ) -> list[JoinedScoringRecord]:
        require_tool_access("join_predictions_to_labels", role)
        cleaned_run = require_non_blank(run_id, "run_id")
        run_predictions = [p for p in predictions if p.run_id == cleaned_run]
        if not run_predictions:
            raise IsolationError(
                f"no predictions available to score for run_id {cleaned_run!r}"
            )
        if any(p.status != "closed" or not p.closed_at for p in run_predictions):
            raise IsolationError(
                f"cannot join ground truth while run_id {cleaned_run!r} is still open"
            )

        norm_mission = _normalize_optional_str(mission_id)
        norm_datasets = (
            {d for d in (_normalize_optional_str(x) for x in dataset_ids) if d}
            if dataset_ids is not None
            else None
        )
        if norm_mission is not None and norm_datasets is None:
            return []

        labels_by_key: dict[
            tuple[str, str, str, str, str], list[GroundTruthRecord]
        ] = {}
        for label in self._records:
            labels_by_key.setdefault(label.join_key(), []).append(label)

        joined: list[JoinedScoringRecord] = []
        for pred in run_predictions:
            if norm_mission is not None and pred.mission_id != norm_mission:
                continue
            if norm_datasets is not None and pred.dataset_id not in norm_datasets:
                continue
            for label in labels_by_key.get(pred.join_key(), ()):
                joined.append(
                    JoinedScoringRecord(
                        run_id=cleaned_run,
                        mission_id=pred.mission_id,
                        dataset_id=pred.dataset_id,
                        prediction=pred,
                        ground_truth=label,
                    )
                )
        return joined
