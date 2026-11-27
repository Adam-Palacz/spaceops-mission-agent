"""ESA-AD multi-mission slice reader (RD3.1).

The Zenodo archives stay out of git. CI streams a three-mission lookalike.
Mission3 is outside the published benchmark unless a report prints an override.
Real import refuses while checksums are unpinned.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel, ConfigDict, Field

from apps.contracts.v1 import TelemetryEventV1
from apps.mission_data.adapter import AdapterError
from apps.mission_data.isolation import FORBIDDEN_LABEL_KEYS
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
