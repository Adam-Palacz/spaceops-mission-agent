"""OPSSAT-AD labeled-segment adapter and offline importer (RD2.1).

Maps OPSSAT-AD point telemetry (``segments.csv``) to ``TelemetryEventV1`` and
segment labels plus the official ``train`` flag (``dataset.csv`` / ``segments.csv``)
into evaluator-only ``GroundTruthRecord`` objects.

Download is strictly manual. This module performs zero network access and never
stores local absolute paths in emitted records or reports.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Literal, Mapping

from pydantic import Field, field_validator

from apps.contracts.v1 import ContractBase, TelemetryEventV1
from apps.mission_data.adapter import AdapterError, _require_registered
from apps.mission_data.isolation import (
    GroundTruthRecord,
    GroundTruthStore,
    IsolationError,
    OPSSAT_AD_DATASET_ID,
    OPSSAT_MISSION_ID,
    find_forbidden_label_keys,
)
from apps.mission_data.provenance import (
    ProvenanceRecord,
    require_non_blank,
    validate_source_url,
)
from apps.mission_data.registry import MissionRegistry, load_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPSSAT_AD_MANIFEST = (
    REPO_ROOT / "data" / "mission_registry" / "opssat_ad_manifest.json"
)
DEFAULT_TELEMETRY_DIR = REPO_ROOT / "data" / "telemetry"
OPSSAT_AD_LOOKALIKE_DATASET_ID = "opssat-ad-lookalike"
DEFAULT_LOOKALIKE_DIR = REPO_ROOT / "tests" / "fixtures" / "opssat_ad_lookalike"

ALLOWED_SEGMENT_COLUMNS: frozenset[str] = frozenset(
    {
        "segment",
        "channel",
        "timestamp",
        "value",
        "sampling",
        "anomaly",
        "label",
        "train",
        "sample_index",
    }
)

_REENTRY_EXACT_COLUMNS: frozenset[str] = frozenset(
    {
        "battery_voltage",
        "battery_temp",
        "rssi",
        "altitude",
        "latitude",
        "longitude",
        "coarse_spin",
        "spin_rate",
    }
)
_REENTRY_PATTERN_COLUMNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^pd\d+_css_theta$", re.IGNORECASE),
    re.compile(r"^uhf_", re.IGNORECASE),
)

_CHUNK_BYTES = 64 * 1024


class FileChecksumEntry(ContractBase):
    md5: str = Field(..., min_length=32, max_length=32)

    @field_validator("md5")
    @classmethod
    def check_hex(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{32}", cleaned):
            raise ValueError("md5 must be a 32-character hex digest")
        return cleaned


class ExpectedAuditCounts(ContractBase):
    total_segments: int = Field(..., ge=1)
    train_segments: int = Field(..., ge=0)
    train_nominal: int = Field(..., ge=0)
    train_anomalous: int = Field(..., ge=0)
    test_segments: int = Field(..., ge=0)
    split_note: str = Field(..., min_length=1)


class OPSSATADManifest(ContractBase):
    schema_version: Literal["1"]
    mission_id: Literal["ops-sat"]
    dataset_id: Literal["opssat-ad"]
    lookalike_dataset_id: Literal["opssat-ad-lookalike"]
    license_spdx: Literal["CC-BY-4.0"]
    zenodo_record_id: str = Field(..., min_length=1)
    zenodo_doi: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    paper_doi: str = Field(..., min_length=1)
    citation: str = Field(..., min_length=1)
    checksum_scope_note: str = Field(..., min_length=1)
    expected_files: dict[str, FileChecksumEntry]
    expected_audit: ExpectedAuditCounts
    channels: list[str] = Field(..., min_length=9, max_length=9)

    @field_validator("source_url")
    @classmethod
    def check_source_url(cls, value: str) -> str:
        return validate_source_url(value)


def load_opssat_ad_manifest(path: Path | None = None) -> OPSSATADManifest:
    manifest_path = path or DEFAULT_OPSSAT_AD_MANIFEST
    payload: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    return OPSSATADManifest.model_validate(payload)


def _streaming_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _is_reentry_column(name: str) -> bool:
    lowered = name.strip().lower()
    if lowered in _REENTRY_EXACT_COLUMNS:
        return True
    return any(pattern.match(lowered) for pattern in _REENTRY_PATTERN_COLUMNS)


def _reject_reentry_columns(columns: Mapping[str, Any] | list[str]) -> None:
    names = list(columns.keys()) if isinstance(columns, Mapping) else list(columns)
    offending = [name for name in names if _is_reentry_column(str(name))]
    if offending:
        raise AdapterError(
            f"re-entry campaign columns are forbidden in {OPSSAT_AD_DATASET_ID}: {sorted(offending)}"
        )


def _parse_segment_id(raw: Any) -> str:
    if raw is None or isinstance(raw, bool):
        raise AdapterError("OPSSAT-AD row requires a non-blank segment id")
    cleaned = str(raw).strip()
    if not cleaned:
        raise AdapterError("OPSSAT-AD row requires a non-blank segment id")
    return cleaned


def _parse_sampling(raw: Any) -> str:
    if raw is None or isinstance(raw, bool):
        raise AdapterError("OPSSAT-AD row requires a non-blank sampling value")
    cleaned = str(raw).strip()
    if not cleaned:
        raise AdapterError("OPSSAT-AD row requires a non-blank sampling value")
    return cleaned


def _parse_finite_float(raw: Any) -> float:
    if raw is None or isinstance(raw, bool):
        raise AdapterError("OPSSAT-AD row requires a finite numeric value")
    if isinstance(raw, str):
        cleaned = raw.strip()
        if not cleaned:
            raise AdapterError("OPSSAT-AD row requires a finite numeric value")
        raw = cleaned
    try:
        numeric = float(raw)
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"OPSSAT-AD value is not numeric: {raw!r}") from exc
    if not math.isfinite(numeric):
        raise AdapterError(f"OPSSAT-AD value must be finite: {raw!r}")
    return numeric


def _parse_binary_flag(raw: Any, field_name: str) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, int):
        if raw in (0, 1):
            return bool(raw)
        raise AdapterError(f"invalid binary {field_name} flag: {raw!r}")
    if isinstance(raw, float):
        if raw in (0.0, 1.0):
            return bool(int(raw))
        raise AdapterError(f"invalid binary {field_name} flag: {raw!r}")
    if isinstance(raw, str):
        cleaned = raw.strip().lower()
        if cleaned in {"1", "1.0", "true"}:
            return True
        if cleaned in {"0", "0.0", "false"}:
            return False
    raise AdapterError(f"invalid binary {field_name} flag: {raw!r}")


def _extract_anomaly_flag(record: Mapping[str, Any]) -> bool | None:
    has_anomaly = "anomaly" in record and str(record.get("anomaly") or "").strip() != ""
    has_label = "label" in record and str(record.get("label") or "").strip() != ""
    if not has_anomaly and not has_label:
        return None
    val_anomaly = (
        _parse_binary_flag(record["anomaly"], "anomaly") if has_anomaly else None
    )
    val_label = _parse_binary_flag(record["label"], "label") if has_label else None
    if val_anomaly is not None and val_label is not None and val_anomaly != val_label:
        raise AdapterError("conflicting 'anomaly' and 'label' values in OPSSAT-AD row")
    return val_anomaly if val_anomaly is not None else val_label


def _extract_train_split(record: Mapping[str, Any]) -> Literal["train", "test"] | None:
    if "train" not in record or str(record.get("train") or "").strip() == "":
        return None
    is_train = _parse_binary_flag(record["train"], "train")
    return "train" if is_train else "test"


def normalize_opssat_timestamp(raw: Any) -> str:
    """Normalize OPSSAT-AD UTC timestamps to canonical ISO8601 without resampling."""
    if not isinstance(raw, str) or not raw.strip():
        raise AdapterError("OPSSAT-AD row requires a non-blank timestamp")
    cleaned = raw.strip()
    iso_candidate = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    try:
        parsed = datetime.fromisoformat(iso_candidate)
    except ValueError as exc:
        raise AdapterError(f"invalid OPSSAT-AD timestamp: {raw!r}") from exc
    if parsed.tzinfo is None:
        utc_dt = parsed.replace(tzinfo=timezone.utc)
    else:
        utc_dt = parsed.astimezone(timezone.utc)
    if utc_dt.microsecond:
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_event_id(
    *,
    dataset_id: str,
    segment_id: str,
    channel_id: str,
    ts: str,
    value: float,
    sampling: str,
    sample_index: int | None,
) -> str:
    if sample_index is not None:
        return f"{dataset_id}:seg-{segment_id}:{channel_id}:{sample_index}"
    canonical = f"{segment_id}|{channel_id}|{ts}|{value!r}|{sampling}"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{dataset_id}:seg-{segment_id}:{channel_id}:{digest}"


class OPSSATADAdapter:
    """Pure adapter for OPSSAT-AD labeled univariate segments (RD2.1).

    Emits ``TelemetryEventV1`` values without labels or ``train`` flags, and
    separately extracts evaluator-only ``GroundTruthRecord`` items.
    """

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry

    def _validate_provenance_scope(self, provenance: ProvenanceRecord) -> None:
        if provenance.mission_id != OPSSAT_MISSION_ID:
            raise AdapterError(
                f"OPSSATADAdapter requires mission_id={OPSSAT_MISSION_ID!r}, "
                f"got {provenance.mission_id!r}"
            )
        if provenance.dataset_id not in {
            OPSSAT_AD_DATASET_ID,
            OPSSAT_AD_LOOKALIKE_DATASET_ID,
        }:
            raise AdapterError(
                f"OPSSATADAdapter rejects dataset_id={provenance.dataset_id!r}"
            )

    def adapt(
        self,
        record: Mapping[str, Any],
        provenance: ProvenanceRecord,
        *,
        sample_index: int | None = None,
    ) -> list[TelemetryEventV1]:
        self._validate_provenance_scope(provenance)
        _reject_reentry_columns(record)
        unknown_cols = [
            str(key)
            for key in record.keys()
            if str(key).strip() not in ALLOWED_SEGMENT_COLUMNS
        ]
        if unknown_cols:
            raise AdapterError(
                f"unexpected columns in OPSSAT-AD segment row: {sorted(unknown_cols)}"
            )

        segment_id = _parse_segment_id(record.get("segment"))
        channel_id = require_non_blank(str(record.get("channel") or ""), "channel")
        registered = _require_registered(self._registry, provenance, channel_id)
        ts = normalize_opssat_timestamp(record.get("timestamp"))
        value = _parse_finite_float(record.get("value"))
        sampling = _parse_sampling(record.get("sampling"))

        idx = sample_index
        if idx is None and record.get("sample_index") is not None:
            raw_idx = record["sample_index"]
            if isinstance(raw_idx, bool) or not isinstance(raw_idx, int) or raw_idx < 0:
                raise AdapterError(f"invalid sample_index: {raw_idx!r}")
            idx = raw_idx

        event = TelemetryEventV1(
            event_id=_build_event_id(
                dataset_id=provenance.dataset_id,
                segment_id=segment_id,
                channel_id=channel_id,
                ts=ts,
                value=value,
                sampling=sampling,
                sample_index=idx,
            ),
            ts=ts,
            channel=channel_id,
            value=value,
            subsystem=registered.subsystem_id,
            unit=registered.unit,
            source="telemetry",
            metadata=provenance.metadata(segment_id=segment_id, sampling=sampling),
        )
        # Defense-in-depth: labels and train flags must never enter TelemetryEventV1.
        if find_forbidden_label_keys(event.model_dump()):
            raise AdapterError(
                "forbidden label key detected in emitted telemetry event"
            )
        return [event]

    def extract_ground_truth(
        self,
        record: Mapping[str, Any],
        provenance: ProvenanceRecord,
        *,
        annotation_source: str = "opssat-ad:dataset.csv",
    ) -> GroundTruthRecord:
        self._validate_provenance_scope(provenance)
        _reject_reentry_columns(record)
        segment_id = _parse_segment_id(record.get("segment"))
        if "channel" in record and str(record.get("channel") or "").strip():
            channel_id = str(record["channel"]).strip()
            _require_registered(self._registry, provenance, channel_id)
        anomaly = _extract_anomaly_flag(record)
        if anomaly is None:
            raise AdapterError(
                f"OPSSAT-AD segment {segment_id!r} missing required anomaly label"
            )
        split = _extract_train_split(record)
        if split is None:
            raise AdapterError(
                f"OPSSAT-AD segment {segment_id!r} missing required train split flag"
            )
        version = provenance.version or provenance.checksum or "1"
        return GroundTruthRecord(
            mission_id=provenance.mission_id,
            dataset_id=provenance.dataset_id,
            segment_id=segment_id,
            label_kind="anomaly",
            label_value=anomaly,
            split=split,
            annotation_source=annotation_source,
            provenance_version=version,
        )


class OPSSATADAudit(ContractBase):
    total_segments: int = 0
    train_segments: int = 0
    test_segments: int = 0
    train_nominal: int = 0
    train_anomalous: int = 0
    test_nominal: int = 0
    test_anomalous: int = 0
    telemetry_rows: int = 0
    channels_seen: list[str] = Field(default_factory=list)
    matches_official_counts: bool = False


class OPSSATADImportReport(ContractBase):
    schema_version: Literal["rd2.opssat-ad-import.v1"] = "rd2.opssat-ad-import.v1"
    status: Literal["imported", "skipped"]
    mode: Literal["real", "lookalike"]
    mission_id: str
    dataset_id: str
    license_spdx: str
    zenodo_doi: str
    paper_doi: str
    checksums_verified: bool
    file_md5s: dict[str, str] = Field(default_factory=dict)
    missing_files: list[str] = Field(default_factory=list)
    skip_reason: str | None = None
    audit: OPSSATADAudit = Field(default_factory=OPSSATADAudit)


class OPSSATADImportBundle:
    """In-memory result of an offline OPSSAT-AD import: report + separated stores."""

    def __init__(
        self,
        *,
        report: OPSSATADImportReport,
        telemetry_events: list[TelemetryEventV1],
        ground_truth: list[GroundTruthRecord],
    ) -> None:
        self.report = report
        self.telemetry_events = telemetry_events
        self.ground_truth = ground_truth


def import_opssat_ad(
    source_dir: Path,
    *,
    mode: Literal["real", "lookalike"] = "real",
    registry: MissionRegistry | None = None,
    manifest: OPSSATADManifest | None = None,
    verify_checksums: bool | None = None,
) -> OPSSATADImportBundle:
    """Import OPSSAT-AD CSV files offline into separated telemetry and ground-truth lists.

    Returns an explicit ``status="skipped"`` report when ``segments.csv`` or
    ``dataset.csv`` is absent. Fails closed on checksum mismatch, re-entry
    columns, unregistered channels, or cross-file inconsistencies.
    """
    reg = registry or load_registry()
    mf = manifest or load_opssat_ad_manifest()

    dataset_id: str
    license_spdx: str
    source_url: str
    sample_kind: Literal["real", "synthetic"]
    if mode == "real":
        dataset_id = mf.dataset_id
        license_spdx = mf.license_spdx
        source_url = mf.source_url
        sample_kind = "real"
        should_verify = True if verify_checksums is None else verify_checksums
        annotation_source = f"zenodo:{mf.zenodo_record_id}:dataset.csv"
    else:
        dataset_id = mf.lookalike_dataset_id
        license_spdx = "LicenseRef-SpaceOps-Synthetic"
        source_url = "fixture:tests/fixtures/opssat_ad_lookalike"
        sample_kind = "synthetic"
        should_verify = False if verify_checksums is None else verify_checksums
        annotation_source = "lookalike:dataset.csv"

    segments_path = source_dir / "segments.csv"
    dataset_path = source_dir / "dataset.csv"
    missing = [
        name
        for name, candidate in (
            ("dataset.csv", dataset_path),
            ("segments.csv", segments_path),
        )
        if not candidate.is_file()
    ]
    if missing:
        report = OPSSATADImportReport(
            status="skipped",
            mode=mode,
            mission_id=mf.mission_id,
            dataset_id=dataset_id,
            license_spdx=license_spdx,
            zenodo_doi=mf.zenodo_doi,
            paper_doi=mf.paper_doi,
            checksums_verified=False,
            missing_files=missing,
            skip_reason=(
                "OPSSAT-AD CSV files not present locally; manual download from "
                f"Zenodo {mf.zenodo_doi} (CC BY 4.0) is required."
            ),
        )
        return OPSSATADImportBundle(
            report=report,
            telemetry_events=[],
            ground_truth=[],
        )

    actual_md5s = {
        "dataset.csv": _streaming_md5(dataset_path),
        "segments.csv": _streaming_md5(segments_path),
    }
    if should_verify:
        for filename, expected_entry in mf.expected_files.items():
            actual = actual_md5s.get(filename)
            if actual != expected_entry.md5:
                raise AdapterError(
                    f"checksum mismatch for {filename}: expected {expected_entry.md5}, got {actual}"
                )

    provenance = ProvenanceRecord(
        dataset_id=dataset_id,
        mission_id=mf.mission_id,
        version=f"zenodo-{mf.zenodo_record_id}" if mode == "real" else "lookalike-v1",
        checksum=f"md5:{actual_md5s['segments.csv']}",
        license_spdx=license_spdx,
        source_url=source_url,
        sample_kind=sample_kind,
    )
    adapter = OPSSATADAdapter(reg)

    # 1. Read dataset.csv (one row per segment: ground truth + official train flag).
    ground_truth_by_seg: dict[str, GroundTruthRecord] = {}
    dataset_meta_by_seg: dict[str, tuple[str | None, str | None]] = {}
    with dataset_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise AdapterError("dataset.csv has no header row")
        _reject_reentry_columns(list(reader.fieldnames))
        for raw_row in reader:
            gt = adapter.extract_ground_truth(
                raw_row, provenance, annotation_source=annotation_source
            )
            seg_id = str(gt.segment_id)
            if seg_id in ground_truth_by_seg:
                raise AdapterError(f"duplicate segment {seg_id!r} in dataset.csv")
            ground_truth_by_seg[seg_id] = gt
            ds_channel = str(raw_row.get("channel") or "").strip() or None
            ds_sampling = str(raw_row.get("sampling") or "").strip() or None
            dataset_meta_by_seg[seg_id] = (ds_channel, ds_sampling)

    # 2. Read segments.csv (point-level telemetry, no resampling, zero labels emitted).
    telemetry_events: list[TelemetryEventV1] = []
    per_segment_counts: dict[str, int] = {}
    seg_consistency: dict[str, tuple[str, str, bool | None, str | None]] = {}
    channels_seen: set[str] = set()

    with segments_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise AdapterError("segments.csv has no header row")
        _reject_reentry_columns(list(reader.fieldnames))
        for raw_row in reader:
            seg_id = _parse_segment_id(raw_row.get("segment"))
            sample_idx = per_segment_counts.get(seg_id, 0)
            per_segment_counts[seg_id] = sample_idx + 1

            emitted = adapter.adapt(raw_row, provenance, sample_index=sample_idx)
            event = emitted[0]
            telemetry_events.append(event)
            channels_seen.add(event.channel)

            row_sampling = str(event.metadata.get("sampling") or "")
            row_anomaly = _extract_anomaly_flag(raw_row)
            row_split = _extract_train_split(raw_row)
            sig = (event.channel, row_sampling, row_anomaly, row_split)
            prev = seg_consistency.get(seg_id)
            if prev is None:
                seg_consistency[seg_id] = sig
            elif prev != sig:
                raise AdapterError(
                    f"inconsistent channel/sampling/label/train within segment {seg_id!r}"
                )

    # 3. Cross-file consistency check between dataset.csv and segments.csv.
    seg_ids_dataset = set(ground_truth_by_seg.keys())
    seg_ids_points = set(per_segment_counts.keys())
    if seg_ids_dataset != seg_ids_points:
        raise AdapterError(
            "segment ids in dataset.csv and segments.csv do not match 1-to-1"
        )
    for seg_id, gt in ground_truth_by_seg.items():
        seg_ch, seg_sampling, seg_anom, seg_split = seg_consistency[seg_id]
        ds_ch, ds_sampling = dataset_meta_by_seg[seg_id]
        if ds_ch is not None and ds_ch != seg_ch:
            raise AdapterError(
                f"channel mismatch for segment {seg_id!r}: dataset.csv={ds_ch!r}, segments.csv={seg_ch!r}"
            )
        if ds_sampling is not None and ds_sampling != seg_sampling:
            raise AdapterError(
                f"sampling mismatch for segment {seg_id!r}: dataset.csv={ds_sampling!r}, segments.csv={seg_sampling!r}"
            )
        if seg_anom is not None and seg_anom != bool(gt.label_value):
            raise AdapterError(
                f"anomaly label mismatch for segment {seg_id!r} between dataset.csv and segments.csv"
            )
        if seg_split is not None and seg_split != gt.split:
            raise AdapterError(
                f"train split mismatch for segment {seg_id!r} between dataset.csv and segments.csv"
            )

    ground_truth_list = list(ground_truth_by_seg.values())
    train_nominal = sum(
        1
        for gt in ground_truth_list
        if gt.split == "train" and not bool(gt.label_value)
    )
    train_anomalous = sum(
        1 for gt in ground_truth_list if gt.split == "train" and bool(gt.label_value)
    )
    test_nominal = sum(
        1 for gt in ground_truth_list if gt.split == "test" and not bool(gt.label_value)
    )
    test_anomalous = sum(
        1 for gt in ground_truth_list if gt.split == "test" and bool(gt.label_value)
    )
    train_segments = train_nominal + train_anomalous
    test_segments = test_nominal + test_anomalous
    total_segments = len(ground_truth_list)

    expected = mf.expected_audit
    matches_official = (
        total_segments == expected.total_segments
        and train_segments == expected.train_segments
        and test_segments == expected.test_segments
        and train_nominal == expected.train_nominal
        and train_anomalous == expected.train_anomalous
    )

    audit = OPSSATADAudit(
        total_segments=total_segments,
        train_segments=train_segments,
        test_segments=test_segments,
        train_nominal=train_nominal,
        train_anomalous=train_anomalous,
        test_nominal=test_nominal,
        test_anomalous=test_anomalous,
        telemetry_rows=len(telemetry_events),
        channels_seen=sorted(channels_seen),
        matches_official_counts=matches_official,
    )
    report = OPSSATADImportReport(
        status="imported",
        mode=mode,
        mission_id=mf.mission_id,
        dataset_id=dataset_id,
        license_spdx=license_spdx,
        zenodo_doi=mf.zenodo_doi,
        paper_doi=mf.paper_doi,
        checksums_verified=should_verify,
        file_md5s=actual_md5s,
        audit=audit,
    )
    return OPSSATADImportBundle(
        report=report,
        telemetry_events=telemetry_events,
        ground_truth=ground_truth_list,
    )


def write_opssat_ad_outputs(
    bundle: OPSSATADImportBundle,
    *,
    telemetry_out_dir: Path,
    ground_truth_out_dir: Path,
) -> tuple[Path, Path]:
    """Write telemetry and ground truth to strictly separated NDJSON directories."""
    if bundle.report.status != "imported":
        raise IsolationError("cannot write outputs for a skipped OPSSAT-AD import")

    # Enforce strict separation between telemetry and ground-truth directories,
    # and prevent ground-truth files from ever landing inside repo data/telemetry/.
    GroundTruthStore(
        storage_dir=ground_truth_out_dir,
        telemetry_dir=telemetry_out_dir,
    )
    GroundTruthStore(
        storage_dir=ground_truth_out_dir,
        telemetry_dir=DEFAULT_TELEMETRY_DIR,
    )

    telemetry_out_dir.mkdir(parents=True, exist_ok=True)
    ground_truth_out_dir.mkdir(parents=True, exist_ok=True)

    prefix = bundle.report.dataset_id.replace("-", "_")
    telemetry_path = telemetry_out_dir / f"{prefix}_telemetry.ndjson"
    ground_truth_path = ground_truth_out_dir / f"{prefix}_ground_truth.ndjson"

    with telemetry_path.open("w", encoding="utf-8") as handle:
        for event in bundle.telemetry_events:
            handle.write(json.dumps(event.model_dump(), sort_keys=True) + "\n")
    with ground_truth_path.open("w", encoding="utf-8") as handle:
        for label in bundle.ground_truth:
            handle.write(json.dumps(label.model_dump(), sort_keys=True) + "\n")

    return telemetry_path, ground_truth_path
