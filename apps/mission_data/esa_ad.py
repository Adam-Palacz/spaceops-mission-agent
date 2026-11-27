"""ESA-AD multi-mission slice reader (RD3.1).

The Zenodo archives stay out of git. CI streams a three-mission lookalike.
Mission3 is outside the published benchmark unless a report prints an override.
Real import refuses while checksums are unpinned.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.contracts.v1 import TelemetryEventV1
from apps.mission_data.adapter import AdapterError
from apps.mission_data.isolation import FORBIDDEN_LABEL_KEYS, GroundTruthRecord
from apps.mission_data.opssat_ad import normalize_opssat_timestamp
from apps.mission_data.provenance import ProvenanceRecord
from apps.mission_data.registry import REPO_ROOT, MissionRegistry, load_registry

DEFAULT_ESA_AD_MANIFEST = (
    REPO_ROOT / "data" / "mission_registry" / "esa_ad_manifest.json"
)
DEFAULT_ESA_AD_LOOKALIKE_DIR = REPO_ROOT / "tests" / "fixtures" / "esa_ad_lookalike"
SLICE_CHANNEL = "channel_1"
MISSION3_OVERRIDE = "override: Mission3 included in benchmark score"


class EsaMissionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    dataset_id: str
    folder_name: str | None = None
    archive_name: str | None = None
    layout_confirmed: bool
    in_published_benchmark: bool


class EsaAdManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    mission_id: str
    license_spdx: str
    license_note: str
    source_url: str
    code_url: str
    code_license_spdx: str
    checksums_pinned: bool
    full_import_allowed: bool
    experiment_artifacts_gib: int = Field(..., gt=0)
    minimum_ram_gib: int = Field(..., gt=0)
    disk_budget_note: str
    layout_note: str
    missions: list[EsaMissionEntry] = Field(..., min_length=3)


class BenchmarkSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_ids: list[str]
    report_text: str
    includes_mission3: bool


def load_esa_ad_manifest(path: Path | None = None) -> EsaAdManifest:
    payload = json.loads((path or DEFAULT_ESA_AD_MANIFEST).read_text(encoding="utf-8"))
    return EsaAdManifest.model_validate(payload)


def lookalike_dataset_id(dataset_id: str) -> str:
    return f"{dataset_id}-lookalike"


def refuse_real_import(manifest: EsaAdManifest | None = None) -> None:
    """Refuse the Zenodo archives. Checksums are not pinned and files are not read."""
    active = manifest or load_esa_ad_manifest()
    if active.checksums_pinned or active.full_import_allowed:
        raise AdapterError(
            "real ESA-AD import refused: checksum pinning is not implemented, "
            "so archives are not read."
        )
    raise AdapterError(
        "real ESA-AD import refused: file checksums are not pinned and the full "
        f"archive was not downloaded. Published experiment disk budget is "
        f"{active.experiment_artifacts_gib} GiB."
    )


def benchmark_selection(
    *,
    include_mission3: bool = False,
    manifest: EsaAdManifest | None = None,
) -> BenchmarkSelection:
    active = manifest or load_esa_ad_manifest()
    members = [
        item.dataset_id for item in active.missions if item.in_published_benchmark
    ]
    held_out = [
        item.dataset_id for item in active.missions if not item.in_published_benchmark
    ]
    if include_mission3:
        return BenchmarkSelection(
            dataset_ids=[*members, *held_out],
            report_text=MISSION3_OVERRIDE,
            includes_mission3=True,
        )
    return BenchmarkSelection(
        dataset_ids=members,
        report_text="published benchmark: " + ", ".join(members),
        includes_mission3=False,
    )


def _mission(manifest: EsaAdManifest, key: str) -> EsaMissionEntry:
    for item in manifest.missions:
        if item.key == key:
            return item
    raise AdapterError(f"unknown ESA-AD mission key {key}")


def iter_lookalike_events(
    mission_key: str,
    *,
    source_dir: Path | None = None,
    manifest: EsaAdManifest | None = None,
    registry: MissionRegistry | None = None,
) -> Iterator[TelemetryEventV1]:
    """Stream one lookalike mission. Labels never become telemetry fields."""
    active = manifest or load_esa_ad_manifest()
    mission = _mission(active, mission_key)
    dataset_id = lookalike_dataset_id(mission.dataset_id)
    active_registry = registry or load_registry()
    registered = active_registry.require(active.mission_id, dataset_id, SLICE_CHANNEL)
    provenance = ProvenanceRecord(
        mission_id=active.mission_id,
        dataset_id=dataset_id,
        license_spdx=registered.license_spdx,
        source_url=f"fixture:tests/fixtures/esa_ad_lookalike/{mission_key}",
        sample_kind=registered.sample_kind,
        version="lookalike-v1",
    )
    if provenance.sample_kind != "synthetic":
        raise AdapterError("ESA-AD lookalike must stay synthetic")
    path = (source_dir or DEFAULT_ESA_AD_LOOKALIKE_DIR) / mission_key / "telemetry.csv"
    if not path.is_file():
        raise AdapterError(f"lookalike slice {mission_key} has no telemetry.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AdapterError(f"lookalike slice {mission_key} has no header")
        forbidden = sorted(
            name for name in reader.fieldnames if name.lower() in FORBIDDEN_LABEL_KEYS
        )
        if forbidden:
            raise AdapterError(f"ESA-AD telemetry cannot carry labels: {forbidden}")
        for index, row in enumerate(reader):
            channel = (row.get("channel") or "").strip()
            if channel != SLICE_CHANNEL:
                raise AdapterError(f"unexpected ESA-AD slice channel {channel}")
            yield TelemetryEventV1(
                event_id=f"{dataset_id}:{channel}:{index}",
                ts=normalize_opssat_timestamp(row.get("timestamp") or ""),
                channel=channel,
                value=float(row["value"]),
                subsystem=registered.subsystem_id,
                unit=registered.unit,
                source="esa-ad-lookalike",
                metadata=provenance.metadata(sampling=registered.sampling),
            )


_TELECOMMAND_TEXT_RE = re.compile(r"^[a-z0-9_-]{0,32}$")
_FORBIDDEN_TELECOMMAND_TEXT = ("execute", "command", "uplink", "gitops", "kubectl")


class EsaAnnotationCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    anomaly: int = 0
    rare_nominal: int = 0
    telecommand: int = 0


class EsaAnnotationReport(BaseModel):
    """Separate counts. This sprint does not compute a detection score."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd3.annotations.v1"] = "rd3.annotations.v1"
    status: Literal["imported"] = "imported"
    sample_kind: Literal["synthetic"] = "synthetic"
    archives_downloaded: Literal[False] = False
    anomaly_count: int
    rare_nominal_count: int
    telecommand_count: int
    missions: list[EsaAnnotationCounts]


def query_annotations(
    records: list[GroundTruthRecord],
    *,
    label_kind: Literal["anomaly", "rare_nominal", "telecommand"],
) -> list[GroundTruthRecord]:
    """Return one annotation kind. A rare nominal event is not an anomaly."""
    return [item for item in records if item.label_kind == label_kind]


def _telecommand_value(impact: str, priority: str) -> str:
    """Keep impact and priority as data. Never turn them into an instruction."""
    parts: list[str] = []
    for name, raw in (("impact", impact), ("priority", priority)):
        cleaned = raw.strip().lower()
        if not cleaned:
            continue
        if not _TELECOMMAND_TEXT_RE.fullmatch(cleaned):
            raise AdapterError(f"telecommand {name} is not plain data")
        if any(token in cleaned for token in _FORBIDDEN_TELECOMMAND_TEXT):
            raise AdapterError(f"telecommand {name} must not be an instruction")
        parts.append(f"{name}={cleaned}")
    return ",".join(parts) if parts else "timestamp-only"


def _annotation_record(
    *,
    mission_id: str,
    dataset_id: str,
    kind: str,
    channel: str,
    start: str,
    end: str,
    impact: str,
    priority: str,
) -> GroundTruthRecord:
    if kind == "anomaly":
        label_kind: Literal["anomaly", "rare_nominal", "telecommand"] = "anomaly"
    elif kind == "rare_nominal":
        label_kind = "rare_nominal"
    elif kind == "telecommand":
        label_kind = "telecommand"
    else:
        raise AdapterError(f"unknown ESA-AD annotation kind {kind}")
    if kind == "telecommand":
        label_value: bool | str = _telecommand_value(impact, priority)
    else:
        if impact.strip() or priority.strip():
            raise AdapterError("impact and priority belong only on telecommands")
        label_value = True
    return GroundTruthRecord(
        mission_id=mission_id,
        dataset_id=dataset_id,
        time_range_start=start,
        time_range_end=end,
        label_kind=label_kind,
        label_value=label_value,
        annotation_source="esa-ad-lookalike:annotations.csv",
        provenance_version="lookalike-v1",
    )


def import_lookalike_annotations(
    source_dir: Path | None = None,
    *,
    manifest: EsaAdManifest | None = None,
    registry: MissionRegistry | None = None,
) -> tuple[EsaAnnotationReport, list[GroundTruthRecord]]:
    """Map the three annotation kinds on the synthetic slice. Archives stay unread."""
    active = manifest or load_esa_ad_manifest()
    root = source_dir or DEFAULT_ESA_AD_LOOKALIKE_DIR
    if any(root.rglob("*.zip")):
        raise AdapterError("ESA-AD lookalike slice cannot contain archives")
    active_registry = registry or load_registry()
    records: list[GroundTruthRecord] = []
    missions: list[EsaAnnotationCounts] = []
    for mission in active.missions:
        dataset_id = lookalike_dataset_id(mission.dataset_id)
        path = root / mission.key / "annotations.csv"
        if not path.is_file():
            raise AdapterError(f"lookalike slice {mission.key} has no annotations.csv")
        counts = {"anomaly": 0, "rare_nominal": 0, "telecommand": 0}
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            expected = {
                "kind",
                "channel",
                "time_start",
                "time_end",
                "impact",
                "priority",
            }
            if set(reader.fieldnames or []) != expected:
                raise AdapterError(f"unexpected annotation columns for {mission.key}")
            for row in reader:
                kind = (row.get("kind") or "").strip()
                channel = (row.get("channel") or "").strip()
                active_registry.require(active.mission_id, dataset_id, channel)
                start = normalize_opssat_timestamp(row.get("time_start") or "")
                end = normalize_opssat_timestamp(row.get("time_end") or "")
                record = _annotation_record(
                    mission_id=active.mission_id,
                    dataset_id=dataset_id,
                    kind=kind,
                    channel=channel,
                    start=start,
                    end=end,
                    impact=row.get("impact") or "",
                    priority=row.get("priority") or "",
                )
                if record.label_kind == "telecommand" and record.label_value is True:
                    raise AdapterError(
                        "a telecommand timestamp is not an anomaly label"
                    )
                records.append(record)
                counts[kind] += 1
        missions.append(
            EsaAnnotationCounts(
                dataset_id=dataset_id,
                anomaly=counts["anomaly"],
                rare_nominal=counts["rare_nominal"],
                telecommand=counts["telecommand"],
            )
        )
    return (
        EsaAnnotationReport(
            anomaly_count=sum(item.anomaly for item in missions),
            rare_nominal_count=sum(item.rare_nominal for item in missions),
            telecommand_count=sum(item.telecommand for item in missions),
            missions=missions,
        ),
        records,
    )


def iter_lookalike_categorical(
    mission_key: str,
    *,
    source_dir: Path | None = None,
    manifest: EsaAdManifest | None = None,
    registry: MissionRegistry | None = None,
) -> Iterator[TelemetryEventV1]:
    """Stream categorical samples as text. No encoding means no float cast."""
    active = manifest or load_esa_ad_manifest()
    mission = _mission(active, mission_key)
    dataset_id = lookalike_dataset_id(mission.dataset_id)
    active_registry = registry or load_registry()
    path = (
        (source_dir or DEFAULT_ESA_AD_LOOKALIKE_DIR) / mission_key / "categorical.csv"
    )
    if not path.is_file():
        raise AdapterError(f"lookalike slice {mission_key} has no categorical.csv")
    provenance = None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AdapterError(
                f"lookalike slice {mission_key} has no categorical header"
            )
        for index, row in enumerate(reader):
            channel_id = (row.get("channel") or "").strip()
            registered = active_registry.require(
                active.mission_id, dataset_id, channel_id
            )
            if registered.kind != "categorical":
                raise AdapterError(f"{channel_id} is not a categorical channel")
            if registered.encoding:
                raise AdapterError(
                    "categorical encoding is recorded but this slice does not apply it"
                )
            raw = (row.get("value") or "").strip()
            if not raw:
                raise AdapterError("categorical sample is empty")
            if provenance is None:
                provenance = ProvenanceRecord(
                    mission_id=active.mission_id,
                    dataset_id=dataset_id,
                    license_spdx=registered.license_spdx,
                    source_url=f"fixture:tests/fixtures/esa_ad_lookalike/{mission_key}",
                    sample_kind=registered.sample_kind,
                    version="lookalike-v1",
                )
            yield TelemetryEventV1(
                event_id=f"{dataset_id}:{channel_id}:{index}",
                ts=normalize_opssat_timestamp(row.get("timestamp") or ""),
                channel=channel_id,
                value=raw,
                subsystem=registered.subsystem_id,
                unit=registered.unit,
                source="esa-ad-lookalike",
                metadata=provenance.metadata(sampling=registered.sampling),
            )


class SliceFileRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relative_path: str
    md5: str
    row_count: int = Field(..., ge=0)
    byte_count: int = Field(..., ge=0)


class SliceImportManifest(BaseModel):
    """Checksums and counts for one slice. Sample values stay out of this record."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd3.slice-manifest.v1"] = "rd3.slice-manifest.v1"
    code_revision: str = Field(..., min_length=1)
    mission_id: str
    dataset_ids: list[str] = Field(..., min_length=1)
    files: list[SliceFileRecord] = Field(..., min_length=1)
    row_count: int = Field(..., ge=0)
    byte_budget: int = Field(..., ge=0)
    bytes_planned: int = Field(..., ge=0)


class SliceReplayManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd3.slice-replay.v1"] = "rd3.slice-replay.v1"
    code_revision: str = Field(..., min_length=1)
    import_md5: str = Field(..., min_length=32, max_length=32)
    mission_id: str
    dataset_ids: list[str] = Field(..., min_length=1)
    time_range_start: str
    time_range_end: str


def _slice_csv_files(root: Path) -> list[Path]:
    if any(root.rglob("*.zip")):
        raise AdapterError("ESA-AD slice cannot contain archives")
    files = sorted(path for path in root.rglob("*.csv") if path.is_file())
    if not files:
        raise AdapterError("ESA-AD slice has no csv files")
    return files


def _file_record(root: Path, path: Path) -> SliceFileRecord:
    payload = path.read_bytes()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        row_count = sum(1 for row in reader if any(cell.strip() for cell in row))
    return SliceFileRecord(
        relative_path=path.relative_to(root).as_posix(),
        md5=hashlib.md5(payload).hexdigest(),
        row_count=row_count,
        byte_count=len(payload),
    )


def canonical_import_md5(manifest: SliceImportManifest) -> str:
    body = json.dumps(
        manifest.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.md5(body.encode("utf-8")).hexdigest()


def commit_slice_import(
    source_dir: Path,
    dest: Path,
    *,
    code_revision: str,
    byte_budget: int,
    manifest: EsaAdManifest | None = None,
) -> SliceImportManifest:
    """Write the slice manifest only after the byte budget accepts the inputs."""
    if byte_budget < 0:
        raise AdapterError("byte budget must be zero or positive")
    active = manifest or load_esa_ad_manifest()
    files = _slice_csv_files(source_dir)
    planned = sum(path.stat().st_size for path in files)
    if planned > byte_budget:
        raise AdapterError(
            f"slice import exceeds the byte budget: planned {planned}, budget {byte_budget}"
        )
    records = [_file_record(source_dir, path) for path in files]
    document = SliceImportManifest(
        code_revision=code_revision.strip(),
        mission_id=active.mission_id,
        dataset_ids=[lookalike_dataset_id(item.dataset_id) for item in active.missions],
        files=records,
        row_count=sum(item.row_count for item in records),
        byte_budget=byte_budget,
        bytes_planned=planned,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(document.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return document


def verify_slice_import(manifest: SliceImportManifest, source_dir: Path) -> None:
    """Fail when a recorded file checksum no longer matches the slice."""
    for record in manifest.files:
        path = source_dir / record.relative_path
        if not path.is_file():
            raise AdapterError(f"slice file missing: {record.relative_path}")
        actual = hashlib.md5(path.read_bytes()).hexdigest()
        if actual != record.md5:
            raise AdapterError(f"checksum mismatch for {record.relative_path}")


def replay_slice_event_ids(
    manifest: SliceImportManifest,
    replay: SliceReplayManifest,
    source_dir: Path,
) -> list[str]:
    """Return stable event ids for the recorded time slice."""
    if replay.code_revision != manifest.code_revision:
        raise AdapterError("replay code revision does not match the import manifest")
    if replay.import_md5 != canonical_import_md5(manifest):
        raise AdapterError("replay does not match the import manifest checksum")
    if replay.mission_id != manifest.mission_id:
        raise AdapterError("replay mission does not match the import manifest")
    verify_slice_import(manifest, source_dir)
    start = normalize_opssat_timestamp(replay.time_range_start)
    end = normalize_opssat_timestamp(replay.time_range_end)
    if start > end:
        raise AdapterError("replay time range is reversed")
    event_ids: list[str] = []
    for dataset_id in replay.dataset_ids:
        mission_key = dataset_id.removeprefix("esa-ad-").removesuffix("-lookalike")
        for event in iter_lookalike_events(mission_key, source_dir=source_dir):
            if start <= event.ts <= end:
                event_ids.append(event.event_id)
        categorical = source_dir / mission_key / "categorical.csv"
        if categorical.is_file():
            for event in iter_lookalike_categorical(mission_key, source_dir=source_dir):
                if start <= event.ts <= end:
                    event_ids.append(event.event_id)
    return event_ids
