"""RD1 adapter, registry, and TelemetryEventV1 compatibility."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.api.main import _normalize_telemetry_record
from apps.contracts.v1 import TelemetryEventV1
from apps.mission_data import (
    AdapterError,
    MissionRegistry,
    ProvenanceRecord,
    RESERVED_METADATA_KEYS,
    RegistryError,
    SyntheticFixtureAdapter,
    load_registry,
)
from apps.mission_data.registry import DEFAULT_REGISTRY, RegistryDocument

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"
OPSSAT_CHANNELS = {
    "CADC0872",
    "CADC0873",
    "CADC0874",
    "CADC0884",
    "CADC0886",
    "CADC0888",
    "CADC0890",
    "CADC0892",
    "CADC0894",
}


def _synthetic_provenance() -> ProvenanceRecord:
    return ProvenanceRecord(
        dataset_id="lab-synthetic-telemetry",
        mission_id="lab-synthetic",
        version="1",
        license_spdx="LicenseRef-SpaceOps-Synthetic",
        source_url="fixture:data/telemetry/telemetry.ndjson",
        sample_kind="synthetic",
    )


def _registry_payload() -> dict:
    return json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))


def test_all_synthetic_fixture_rows_round_trip_without_rewriting_the_fixture() -> None:
    before = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    adapter = SyntheticFixtureAdapter(load_registry())
    rows = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) >= 1
    events = [adapter.adapt(raw, _synthetic_provenance())[0] for raw in rows]
    first = events[0]
    assert first.channel == "temp_plate_1"
    assert first.value == 42.1
    assert first.unit == "C"
    assert first.ts == "2025-02-14T10:00:00Z"
    assert first.metadata["dataset_id"] == "lab-synthetic-telemetry"
    assert first.metadata["sample_kind"] == "synthetic"
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == before


def test_missing_or_blank_provenance_fields_are_rejected() -> None:
    for kwargs in (
        {"license_spdx": ""},
        {"license_spdx": "   "},
        {"dataset_id": ""},
        {"dataset_id": "   "},
        {"mission_id": "   "},
        {"version": None, "checksum": None},
        {"version": "   ", "checksum": "   "},
    ):
        base = {
            "dataset_id": "lab-synthetic-telemetry",
            "mission_id": "lab-synthetic",
            "version": "1",
            "license_spdx": "LicenseRef-SpaceOps-Synthetic",
            "source_url": "fixture:data/telemetry/telemetry.ndjson",
            "sample_kind": "synthetic",
        }
        base.update(kwargs)
        with pytest.raises(ValidationError):
            ProvenanceRecord(**base)


@pytest.mark.parametrize(
    "bad_source",
    [
        r"C:\data\telemetry.ndjson",
        r"  C:\data\telemetry.ndjson",
        "/etc/passwd",
        " /etc/passwd",
        "file:///etc/passwd",
        "FILE:///C:/data/telemetry.ndjson",
        "https://user:secret@example.test/file",
        "HTTPS://user:secret@example.test/file",
        "  https://user:secret@example.test/file",
        "https://example.test/file?token=abc",
        "https://example.test/file?password=abc",
        "https://example.test/file?secret=abc",
        "https://example.test/file?sig=abc",
        "   ",
    ],
)
def test_provenance_rejects_paths_and_credentials(bad_source: str) -> None:
    with pytest.raises(ValidationError):
        ProvenanceRecord(
            dataset_id="lab-synthetic-telemetry",
            mission_id="lab-synthetic",
            version="1",
            license_spdx="LicenseRef-SpaceOps-Synthetic",
            source_url=bad_source,
            sample_kind="synthetic",
        )


def test_unknown_channel_fails_closed() -> None:
    raw = {
        "ts": "2025-02-14T10:00:00Z",
        "channel": "CADC0872",
        "value": 1,
        "unit": None,
    }
    with pytest.raises(RegistryError):
        SyntheticFixtureAdapter(load_registry()).adapt(raw, _synthetic_provenance())


def test_cross_mission_sample_kind_and_license_spoofing_fail_closed() -> None:
    raw = {
        "ts": "2025-02-14T10:00:00Z",
        "channel": "CADC0872",
        "value": 1.0,
    }
    spoofed_real_as_synthetic = ProvenanceRecord(
        dataset_id="opssat-ad",
        mission_id="ops-sat",
        version="1",
        license_spdx="CC-BY-4.0",
        source_url="https://doi.org/10.5281/zenodo.12588359",
        sample_kind="synthetic",
    )
    with pytest.raises(AdapterError):
        SyntheticFixtureAdapter(load_registry()).adapt(raw, spoofed_real_as_synthetic)

    wrong_license = _synthetic_provenance().model_copy(
        update={"license_spdx": "CC-BY-4.0"}
    )
    fixture_row = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])
    with pytest.raises(AdapterError):
        SyntheticFixtureAdapter(load_registry()).adapt(fixture_row, wrong_license)


def test_adapter_enforces_unit_subsystem_and_preserves_zero_segment_id() -> None:
    adapter = SyntheticFixtureAdapter(load_registry())
    base_row = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])

    with pytest.raises(AdapterError):
        adapter.adapt({**base_row, "unit": "K"}, _synthetic_provenance())

    with pytest.raises(AdapterError):
        adapter.adapt({**base_row, "subsystem": "Power"}, _synthetic_provenance())

    event = adapter.adapt({**base_row, "segment_id": 0}, _synthetic_provenance())[0]
    assert event.metadata["segment_id"] == "0"


def test_synthetic_and_opssat_channels_do_not_collide() -> None:
    registry = load_registry()
    synthetic = registry.channels_for_mission("lab-synthetic")
    opssat = registry.channels_for_mission("ops-sat")
    assert synthetic.isdisjoint(opssat)
    reentry = registry.channels_for_dataset("opssat-reentry-uhf")
    assert registry.channels_for_dataset("opssat-ad") == OPSSAT_CHANNELS
    assert reentry.isdisjoint(OPSSAT_CHANNELS)
    assert opssat == OPSSAT_CHANNELS | reentry
    assert "temp_plate_1" not in registry.channels_for_dataset("opssat-ad")
    assert "CADC0872" not in registry.channels_for_dataset("lab-synthetic-telemetry")
    lab = registry.require("lab-synthetic", "lab-synthetic-telemetry", "temp_plate_1")
    assert lab.sample_kind == "synthetic"
    opssat_channel = registry.require("ops-sat", "opssat-ad", "CADC0872")
    assert opssat_channel.subsystem_id == "ADCS"
    assert opssat_channel.sample_kind == "real"


def test_registry_rejects_duplicates_missing_channels_and_bad_urls() -> None:
    dup_mission = _registry_payload()
    dup_mission["missions"].append(copy.deepcopy(dup_mission["missions"][0]))
    with pytest.raises(RegistryError):
        MissionRegistry(RegistryDocument.model_validate(dup_mission))

    dup_dataset = _registry_payload()
    dup_dataset["missions"][1]["datasets"][0]["dataset_id"] = "lab-synthetic-telemetry"
    with pytest.raises(RegistryError):
        MissionRegistry(RegistryDocument.model_validate(dup_dataset))

    dup_channel = _registry_payload()
    first_channels = dup_channel["missions"][0]["spacecraft"][0]["subsystems"][0][
        "channels"
    ]
    first_channels.append(copy.deepcopy(first_channels[0]))
    with pytest.raises(RegistryError):
        MissionRegistry(RegistryDocument.model_validate(dup_channel))

    undeclared = _registry_payload()
    undeclared["missions"][0]["datasets"][0]["channel_ids"].append("ghost_channel")
    with pytest.raises(RegistryError):
        MissionRegistry(RegistryDocument.model_validate(undeclared))

    bad_url = _registry_payload()
    bad_url["missions"][0]["datasets"][0]["source_url"] = "file:///etc/passwd"
    with pytest.raises(ValidationError):
        RegistryDocument.model_validate(bad_url)


def test_mission_data_package_does_not_fetch() -> None:
    banned = {"requests", "httpx", "urllib", "socket", "http", "aiohttp", "subprocess"}
    for path in (ROOT / "apps" / "mission_data").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(banned), f"{path}: {imported & banned}"


def test_real_provenance_is_rejected_by_the_synthetic_adapter() -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])
    provenance = _synthetic_provenance().model_copy(update={"sample_kind": "real"})
    with pytest.raises(AdapterError):
        SyntheticFixtureAdapter(load_registry()).adapt(raw, provenance)


def test_existing_fixture_still_validates_and_extra_fields_fail() -> None:
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            _normalize_telemetry_record(json.loads(line), "telemetry")
    event = SyntheticFixtureAdapter(load_registry()).adapt(
        json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0]),
        _synthetic_provenance(),
    )[0]
    TelemetryEventV1.model_validate(event.model_dump())
    assert set(RESERVED_METADATA_KEYS).issuperset(event.metadata)
    with pytest.raises(ValidationError):
        TelemetryEventV1.model_validate({**event.model_dump(), "anomaly": True})
