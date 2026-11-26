"""RD2.2 re-entry column map and license gate."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from apps.mission_data import (
    AdapterError,
    GroundTruthRecord,
    GroundTruthStore,
    IsolationError,
    OPSSAT_AD_DATASET_ID,
    OPSSAT_AD_LOOKALIKE_DATASET_ID,
    OPSSAT_MISSION_ID,
    OPSSAT_REENTRY_UHF_DATASET_ID,
    PredictionRecord,
    RESERVED_METADATA_KEYS,
    find_forbidden_label_keys,
    load_registry,
)
from apps.mission_data.opssat_reentry import (
    DEFAULT_REENTRY_LOOKALIKE_DIR,
    DEFAULT_TELEMETRY_DIR,
    OPSSAT_REENTRY_LOOKALIKE_DATASET_ID,
    REENTRY_TIME_BASIS,
    import_opssat_reentry,
    load_reentry_manifest,
    write_reentry_telemetry,
)
from scripts import import_opssat_reentry as import_cli

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def test_manifest_columns_match_registry_and_stay_off_opssat_ad() -> None:
    manifest = load_reentry_manifest()
    registry = load_registry()
    assert manifest.dataset_id == OPSSAT_REENTRY_UHF_DATASET_ID
    assert manifest.license_status == "unrecorded"
    assert manifest.license_spdx is None
    assert manifest.time_basis == REENTRY_TIME_BASIS
    assert manifest.file_checksums == []
    declared = {column.channel_id for column in manifest.columns}
    assert declared == set(registry.channels_for_dataset(manifest.dataset_id))
    assert declared == set(registry.channels_for_dataset(manifest.lookalike_dataset_id))
    assert "PD1_CSS_theta" in declared
    assert "PD1_CSS_theta" not in registry.channels_for_dataset(OPSSAT_AD_DATASET_ID)
    assert "CADC0884" not in declared
    for column in manifest.columns:
        registered = registry.require(
            manifest.mission_id,
            manifest.lookalike_dataset_id,
            column.channel_id,
        )
        assert registered.role == column.role
        assert registered.unit == column.unit
        assert registered.kind == column.kind
        assert "ground receipt time" in registered.sampling
        if column.role == "derived":
            assert "not a spacecraft sensor" in registered.sampling


def test_real_import_names_the_missing_license_and_does_not_read_rows(
    tmp_path: Path,
) -> None:
    source = tmp_path / "campaign"
    source.mkdir()
    (source / "uhf_telemetry.csv").write_text("not,a,table\n", encoding="utf-8")
    with pytest.raises(AdapterError, match="license_status=unrecorded") as exc:
        import_opssat_reentry(source, mode="real")
    message = str(exc.value)
    assert "machine-readable license" in message
    assert str(source) not in message

    manifest = load_reentry_manifest()
    recorded = manifest.model_copy(
        update={"license_status": "recorded", "license_spdx": "CC-BY-4.0"}
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(recorded.model_dump(mode="json")),
        encoding="utf-8",
    )
    with pytest.raises(AdapterError, match="rows are not read") as recorded_exc:
        import_opssat_reentry(source, mode="real", manifest_path=manifest_path)
    assert "checksum" in str(recorded_exc.value)
    assert str(source) not in str(recorded_exc.value)


def test_lookalike_maps_battery_voltage_without_labels() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    report, events = import_opssat_reentry(mode="lookalike")
    assert report.status == "imported"
    assert report.dataset_id == OPSSAT_REENTRY_LOOKALIKE_DATASET_ID
    by_channel = {event.channel: event for event in events}
    battery = by_channel["Battery_Voltage"]
    altitude = by_channel["Altitude"]
    assert battery.value == 8.1
    assert battery.unit == "V"
    assert battery.metadata["dataset_id"] == OPSSAT_REENTRY_LOOKALIKE_DATASET_ID
    assert battery.metadata["sample_kind"] == "synthetic"
    assert battery.metadata["time_basis"] == REENTRY_TIME_BASIS
    assert battery.ts.endswith("Z")
    assert set(RESERVED_METADATA_KEYS).issuperset(battery.metadata)
    assert find_forbidden_label_keys(battery.model_dump()) == []
    assert "segment_id" not in battery.metadata
    assert altitude.unit is None
    assert "not a spacecraft sensor" in altitude.metadata["sampling"]
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_reentry_row_cannot_take_an_opssat_ad_label(tmp_path: Path) -> None:
    source = tmp_path / "rows"
    source.mkdir()
    (source / "uhf_telemetry.csv").write_text(
        "Timestamp,Battery_Voltage,anomaly\n2024-05-22 22:30:00,8.1,1\n",
        encoding="utf-8",
    )
    with pytest.raises(AdapterError, match="OPSSAT-AD labels"):
        import_opssat_reentry(source, mode="lookalike")

    (source / "uhf_telemetry.csv").write_text(
        "Timestamp,CADC0884\n2024-05-22 22:30:00,1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(AdapterError, match="OPSSAT-AD channel"):
        import_opssat_reentry(source, mode="lookalike")

    _report, events = import_opssat_reentry(mode="lookalike")
    labels = GroundTruthStore(
        [
            GroundTruthRecord(
                mission_id=OPSSAT_MISSION_ID,
                dataset_id=OPSSAT_AD_LOOKALIKE_DATASET_ID,
                segment_id="0",
                label_kind="anomaly",
                label_value=True,
                split="train",
                annotation_source="opssat-ad",
                provenance_version="lookalike-v1",
            )
        ]
    )
    prediction = PredictionRecord(
        run_id="run-reentry",
        mission_id=OPSSAT_MISSION_ID,
        dataset_id=OPSSAT_REENTRY_LOOKALIKE_DATASET_ID,
        segment_id="0",
        prediction={"read_only": True},
        status="closed",
        closed_at=events[0].ts,
    )
    assert (
        labels.join_predictions_to_labels(
            role="evaluator",
            run_id="run-reentry",
            predictions=[prediction],
        )
        == []
    )
    assert (
        labels.read_labels(
            role="evaluator",
            mission_id=OPSSAT_MISSION_ID,
            dataset_id=OPSSAT_REENTRY_LOOKALIKE_DATASET_ID,
        )
        == []
    )


def test_writer_refuses_the_synthetic_fixture_tree_and_cli_writes_telemetry_only(
    tmp_path: Path,
) -> None:
    _report, events = import_opssat_reentry(mode="lookalike")
    with pytest.raises(IsolationError, match="data/telemetry"):
        write_reentry_telemetry(events, DEFAULT_TELEMETRY_DIR / "nested_reentry")
    assert not (DEFAULT_TELEMETRY_DIR / "nested_reentry").exists()

    assert import_cli.main(["--source-dir", str(tmp_path)]) == 1
    out = tmp_path / "out"
    assert import_cli.main(["--lookalike", "--telemetry-out", str(out)]) == 0
    written = list(out.glob("*.ndjson"))
    assert len(written) == 1
    assert "ground_truth" not in written[0].name
    payload = json.loads(written[0].read_text(encoding="utf-8").splitlines()[0])
    assert payload["channel"] == "Altitude"
    assert payload["metadata"]["dataset_id"] == OPSSAT_REENTRY_LOOKALIKE_DATASET_ID


def test_reentry_sources_do_not_import_network_modules() -> None:
    for path in (
        ROOT / "apps" / "mission_data" / "opssat_reentry.py",
        ROOT / "scripts" / "import_opssat_reentry.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.names[0].name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        }
        imported.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        assert imported.isdisjoint({"requests", "httpx", "urllib", "socket"})
    assert (DEFAULT_REENTRY_LOOKALIKE_DIR / "uhf_telemetry.csv").is_file()
