"""OPS-SAT re-entry UHF adapter (RD2.2).

The public campaign has no machine-readable license in this repo, so real
rows are never read. CI maps a synthetic lookalike that cannot inherit
OPSSAT-AD labels. Timestamps are ground receipt time.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.contracts.v1 import TelemetryEventV1
from apps.mission_data.adapter import AdapterError
from apps.mission_data.isolation import FORBIDDEN_LABEL_KEYS, IsolationError
from apps.mission_data.opssat_ad import normalize_opssat_timestamp
from apps.mission_data.provenance import ProvenanceRecord, require_non_blank
from apps.mission_data.registry import (
    REPO_ROOT,
    MissionRegistry,
    load_registry,
)

OPSSAT_REENTRY_LOOKALIKE_DATASET_ID = "opssat-reentry-uhf-lookalike"
REENTRY_TIME_BASIS = "ground_receipt"
DEFAULT_REENTRY_MANIFEST = (
    REPO_ROOT / "data" / "mission_registry" / "opssat_reentry_manifest.json"
)
DEFAULT_REENTRY_LOOKALIKE_DIR = (
    REPO_ROOT / "tests" / "fixtures" / "opssat_reentry_lookalike"
)
DEFAULT_TELEMETRY_DIR = REPO_ROOT / "data" / "telemetry"
_AD_CHANNEL = re.compile(r"^CADC\d+$", re.IGNORECASE)
_TRAIN_FLAG = "train"


class ReentryColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str = Field(..., min_length=1)
    unit: str | None = None
    kind: Literal["numeric", "categorical"]
    role: Literal["sensor", "derived"]
    subsystem_id: str = Field(..., min_length=1)

    @field_validator("channel_id", "subsystem_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        return require_non_blank(value, "channel_id")


class ReentryManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"]
    mission_id: str
    dataset_id: str
    lookalike_dataset_id: str
    license_status: Literal["unrecorded", "recorded"]
    license_spdx: str | None = None
    license_note: str = Field(..., min_length=1)
    source_url: str
    timestamp_column: str
    time_basis: Literal["ground_receipt"]
    file_checksums: list[str] = Field(default_factory=list)
    columns: list[ReentryColumn] = Field(..., min_length=1)

    @field_validator("license_note", "timestamp_column")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        return require_non_blank(value, "field")


class ReentryImportReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["imported", "refused"]
    dataset_id: str
    license_status: str
    reason: str
    event_count: int = 0


def load_reentry_manifest(path: Path | None = None) -> ReentryManifest:
    manifest_path = path or DEFAULT_REENTRY_MANIFEST
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ReentryManifest.model_validate(payload)


def _dataset_source(registry: MissionRegistry, mission_id: str, dataset_id: str) -> str:
    for mission in registry.document.missions:
        if mission.mission_id != mission_id:
            continue
        for dataset in mission.datasets:
            if dataset.dataset_id == dataset_id:
                return dataset.source_url
    raise AdapterError(f"dataset {dataset_id} is not in the registry")


def _refuse_real(manifest: ReentryManifest) -> None:
    if manifest.license_status != "recorded" or not manifest.license_spdx:
        raise AdapterError(
            "real OPS-SAT re-entry import refused: "
            f"{manifest.license_note} license_status={manifest.license_status}."
        )
    if not manifest.file_checksums:
        raise AdapterError(
            "real OPS-SAT re-entry import refused: license_status is recorded "
            "but no file checksum is pinned, so rows are not read."
        )
    raise AdapterError(
        "real OPS-SAT re-entry import refused: checksum pinning is not "
        "implemented, so rows are not read."
    )


def _parse_cell(raw: str, column: ReentryColumn) -> float | str:
    cleaned = raw.strip()
    if column.kind == "categorical":
        if not cleaned:
            raise AdapterError(f"{column.channel_id} categorical value is blank")
        return cleaned
    if cleaned.lower() in {"true", "false"}:
        raise AdapterError(f"{column.channel_id} is numeric and cannot be a boolean")
    try:
        value = float(cleaned)
    except ValueError as exc:
        raise AdapterError(f"{column.channel_id} is not a finite number") from exc
    if not math.isfinite(value):
        raise AdapterError(f"{column.channel_id} is not a finite number")
    return value


def adapt_reentry_rows(
    rows: list[dict[str, str]],
    *,
    provenance: ProvenanceRecord,
    registry: MissionRegistry,
    manifest: ReentryManifest,
) -> list[TelemetryEventV1]:
    """Map a wide UHF table to telemetry. Labels are rejected, not stored."""
    allowed = {column.channel_id: column for column in manifest.columns}
    if len(allowed) != len(manifest.columns):
        raise AdapterError("re-entry manifest has a duplicate channel")
    events: list[TelemetryEventV1] = []
    for index, row in enumerate(rows):
        headers = {key.strip() for key in row}
        headers.discard(manifest.timestamp_column)
        forbidden = sorted(
            key
            for key in headers
            if key.lower() in FORBIDDEN_LABEL_KEYS or key.lower() == _TRAIN_FLAG
        )
        if forbidden:
            raise AdapterError(
                f"re-entry row cannot carry OPSSAT-AD labels or a train flag: {forbidden}"
            )
        ad_channels = sorted(key for key in headers if _AD_CHANNEL.match(key))
        if ad_channels:
            raise AdapterError(
                f"re-entry row cannot use OPSSAT-AD channel names: {ad_channels}"
            )
        unknown = sorted(key for key in headers if key not in allowed)
        if unknown:
            raise AdapterError(f"unexpected re-entry columns: {unknown}")
        timestamp = normalize_opssat_timestamp(row.get(manifest.timestamp_column, ""))
        produced = 0
        for name in sorted(headers):
            raw = row.get(name, "")
            if not str(raw).strip():
                continue
            column = allowed[name]
            registered = registry.require(
                manifest.mission_id, provenance.dataset_id, column.channel_id
            )
            if (
                registered.role != column.role
                or registered.kind != column.kind
                or registered.unit != column.unit
                or registered.subsystem_id != column.subsystem_id
            ):
                raise AdapterError(
                    f"registry disagrees with the re-entry manifest for {column.channel_id}"
                )
            events.append(
                TelemetryEventV1(
                    event_id=f"{provenance.dataset_id}:{column.channel_id}:{index}",
                    ts=timestamp,
                    channel=registered.channel_id,
                    value=_parse_cell(str(raw), column),
                    subsystem=registered.subsystem_id,
                    unit=registered.unit,
                    source="uhf-reentry",
                    metadata=provenance.metadata(
                        sampling=registered.sampling,
                        time_basis=manifest.time_basis,
                    ),
                )
            )
            produced += 1
        if produced == 0:
            raise AdapterError("re-entry row has a timestamp and no mapped values")
    if not events:
        raise AdapterError("re-entry table has no mapped rows")
    return events


def _read_lookalike_rows(
    source_dir: Path, timestamp_column: str
) -> list[dict[str, str]]:
    path = source_dir / "uhf_telemetry.csv"
    if not path.is_file():
        raise AdapterError("lookalike re-entry table is missing uhf_telemetry.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or timestamp_column not in reader.fieldnames:
            raise AdapterError("lookalike re-entry table has no Timestamp column")
        return [dict(row) for row in reader]


def import_opssat_reentry(
    source_dir: Path | None = None,
    *,
    mode: Literal["real", "lookalike"] = "real",
    manifest_path: Path | None = None,
    registry: MissionRegistry | None = None,
) -> tuple[ReentryImportReport, list[TelemetryEventV1]]:
    """Import a lookalike table, or refuse the real campaign without reading it."""
    manifest = load_reentry_manifest(manifest_path)
    active_registry = registry or load_registry()
    if mode == "real":
        _refuse_real(manifest)
    dataset_id = manifest.lookalike_dataset_id
    rows = _read_lookalike_rows(
        source_dir or DEFAULT_REENTRY_LOOKALIKE_DIR,
        manifest.timestamp_column,
    )
    battery = active_registry.require(
        manifest.mission_id, dataset_id, "Battery_Voltage"
    )
    provenance = ProvenanceRecord(
        mission_id=manifest.mission_id,
        dataset_id=dataset_id,
        license_spdx=battery.license_spdx,
        source_url=_dataset_source(active_registry, manifest.mission_id, dataset_id),
        sample_kind=battery.sample_kind,
        version="lookalike-v1",
    )
    if provenance.sample_kind != "synthetic":
        raise AdapterError("re-entry lookalike must stay synthetic")
    events = adapt_reentry_rows(
        rows,
        provenance=provenance,
        registry=active_registry,
        manifest=manifest,
    )
    report = ReentryImportReport(
        status="imported",
        dataset_id=dataset_id,
        license_status=manifest.license_status,
        reason="synthetic lookalike; real campaign was not read",
        event_count=len(events),
    )
    return report, events


def write_reentry_telemetry(
    events: list[TelemetryEventV1],
    out_dir: Path,
) -> Path:
    """Write telemetry only. This adapter does not create ground-truth files."""
    resolved = out_dir.resolve()
    telemetry_root = DEFAULT_TELEMETRY_DIR.resolve()
    if resolved == telemetry_root or telemetry_root in resolved.parents:
        raise IsolationError(
            "re-entry telemetry must not be written into data/telemetry"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "opssat_reentry_uhf_lookalike_telemetry.ndjson"
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event.model_dump(), sort_keys=True) + "\n")
    return path
