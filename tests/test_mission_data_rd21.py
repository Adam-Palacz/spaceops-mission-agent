"""RD2.1 OPSSAT-AD labeled-segment adapter, manifest, and offline importer tests."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from apps.contracts.v1 import TelemetryEventV1
from apps.mission_data import (
    AdapterError,
    DEFAULT_LOOKALIKE_DIR,
    GroundTruthStore,
    InvestigationTelemetryView,
    IsolationError,
    OPSSATADAdapter,
    OPSSAT_AD_DATASET_ID,
    OPSSAT_AD_LOOKALIKE_DATASET_ID,
    OPSSAT_MISSION_ID,
    OPSSAT_REENTRY_UHF_DATASET_ID,
    PredictionRecord,
    PredictionStore,
    ProvenanceRecord,
    RESERVED_METADATA_KEYS,
    RegistryError,
    find_forbidden_label_keys,
    import_opssat_ad,
    load_opssat_ad_manifest,
    load_registry,
    normalize_opssat_timestamp,
    write_opssat_ad_outputs,
)
from apps.mission_data.opssat_ad import FileChecksumEntry
from scripts import import_opssat_ad as import_cli

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def _copy_lookalike(dst: Path) -> Path:
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("segments.csv", "dataset.csv"):
        shutil.copyfile(DEFAULT_LOOKALIKE_DIR / name, dst / name)
    return dst


def test_manifest_records_cc_by_4_checksums_citation_and_official_counts() -> None:
    manifest = load_opssat_ad_manifest()
    assert manifest.mission_id == OPSSAT_MISSION_ID
    assert manifest.dataset_id == OPSSAT_AD_DATASET_ID
    assert manifest.lookalike_dataset_id == OPSSAT_AD_LOOKALIKE_DATASET_ID
    assert manifest.license_spdx == "CC-BY-4.0"
    assert manifest.zenodo_doi == "10.5281/zenodo.12588359"
    assert manifest.paper_doi == "10.1038/s41597-025-05035-3"
    assert "Ruszczak" in manifest.citation
    assert "Kotowski" in manifest.citation
    assert "Evans" in manifest.citation
    assert "Nalepa" in manifest.citation
    assert manifest.expected_files["dataset.csv"].md5 == (
        "c12fb83863afa4463dec07303a20bb14"
    )
    assert manifest.expected_files["segments.csv"].md5 == (
        "1f4b6ffd0359efac96a6698ff557e0f9"
    )
    assert manifest.expected_audit.total_segments == 2123
    assert manifest.expected_audit.train_segments == 1594
    assert manifest.expected_audit.train_nominal == 1273
    assert manifest.expected_audit.train_anomalous == 321
    assert manifest.expected_audit.test_segments == 529
    assert len(manifest.channels) == 9


def test_lookalike_import_maps_values_to_telemetry_and_labels_to_ground_truth() -> None:
    before_fixture = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    bundle = import_opssat_ad(DEFAULT_LOOKALIKE_DIR, mode="lookalike")
    assert bundle.report.status == "imported"
    assert bundle.report.mode == "lookalike"
    assert bundle.report.dataset_id == OPSSAT_AD_LOOKALIKE_DATASET_ID
    assert bundle.report.license_spdx == "LicenseRef-SpaceOps-Synthetic"
    assert bundle.report.audit.total_segments == 4
    assert bundle.report.audit.train_segments == 2
    assert bundle.report.audit.test_segments == 2
    assert bundle.report.audit.train_nominal == 1
    assert bundle.report.audit.train_anomalous == 1
    assert bundle.report.audit.test_nominal == 1
    assert bundle.report.audit.test_anomalous == 1
    assert bundle.report.audit.telemetry_rows == 9
    assert bundle.report.audit.matches_official_counts is False
    assert bundle.report.audit.channels_seen == ["CADC0872", "CADC0873", "CADC0884"]

    # Every emitted TelemetryEventV1 validates strictly, preserves segment_id/sampling/ts,
    # has unique event_id even on duplicate timestamps, and contains zero labels or train flags.
    event_ids = set()
    for event in bundle.telemetry_events:
        dumped = event.model_dump()
        TelemetryEventV1.model_validate(dumped)
        assert not find_forbidden_label_keys(dumped)
        assert set(RESERVED_METADATA_KEYS).issuperset(event.metadata)
        assert event.metadata["mission_id"] == OPSSAT_MISSION_ID
        assert event.metadata["dataset_id"] == OPSSAT_AD_LOOKALIKE_DATASET_ID
        assert event.metadata["sample_kind"] == "synthetic"
        assert "segment_id" in event.metadata
        assert "sampling" in event.metadata
        assert event.ts.endswith("Z") and "T" in event.ts
        event_ids.add(event.event_id)
    assert len(event_ids) == 9

    # Segment 0 preserves integer-zero segment_id and both duplicate-timestamp rows.
    seg0_events = [
        e for e in bundle.telemetry_events if e.metadata["segment_id"] == "0"
    ]
    assert len(seg0_events) == 3
    assert [e.ts for e in seg0_events] == [
        "2021-06-14T08:00:00Z",
        "2021-06-14T08:00:01Z",
        "2021-06-14T08:00:01Z",
    ]
    assert seg0_events[0].metadata["sampling"] == "1"

    # Ground truth strictly preserves source train/test flag and anomaly boolean,
    # keyed by segment_id with time_range_start/end left None for exact evaluator join.
    gt_by_seg = {str(gt.segment_id): gt for gt in bundle.ground_truth}
    assert set(gt_by_seg) == {"0", "1", "2", "3"}
    assert gt_by_seg["0"].split == "train" and gt_by_seg["0"].label_value is False
    assert gt_by_seg["1"].split == "train" and gt_by_seg["1"].label_value is True
    assert gt_by_seg["2"].split == "test" and gt_by_seg["2"].label_value is False
    assert gt_by_seg["3"].split == "test" and gt_by_seg["3"].label_value is True
    for gt in bundle.ground_truth:
        assert gt.time_range_start is None and gt.time_range_end is None

    # Synthetic CI fixture remains untouched.
    assert (
        hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before_fixture
    )


def test_lookalike_does_not_leak_into_unscoped_query_and_joins_closed_run() -> None:
    bundle = import_opssat_ad(DEFAULT_LOOKALIKE_DIR, mode="lookalike")
    telemetry_dicts = [e.model_dump() for e in bundle.telemetry_events]
    view = InvestigationTelemetryView(telemetry_dicts)

    # Must NEVER appear in unscoped queries (reserved for lab-synthetic CI fixture).
    assert (
        view.query(
            time_range_start="2021-06-14T00:00:00Z",
            time_range_end="2021-06-15T00:00:00Z",
        )
        == []
    )

    # Scoped query returns sanitized measurements including sampling & segment_id.
    scoped = view.query(
        time_range_start="2021-06-14T08:00:00Z",
        time_range_end="2021-06-14T08:15:00Z",
        mission_id=OPSSAT_MISSION_ID,
        dataset_ids=[OPSSAT_AD_LOOKALIKE_DATASET_ID],
    )
    assert len(scoped) == 5
    assert all(not find_forbidden_label_keys(row) for row in scoped)
    assert all("sampling" in row["metadata"] for row in scoped)

    # Evaluator join on closed segment-keyed prediction matches exact dataset only.
    gt_store = GroundTruthStore(bundle.ground_truth)
    preds = PredictionStore()
    preds.add(
        PredictionRecord(
            run_id="run-opssat-1",
            mission_id=OPSSAT_MISSION_ID,
            dataset_id=OPSSAT_AD_LOOKALIKE_DATASET_ID,
            segment_id="3",
            prediction={"anomaly_score": 0.95},
            status="open",
        )
    )
    preds.add(
        PredictionRecord(
            run_id="run-opssat-1",
            mission_id=OPSSAT_MISSION_ID,
            dataset_id=OPSSAT_REENTRY_UHF_DATASET_ID,
            segment_id="3",
            prediction={"anomaly_score": 0.50},
            status="open",
        )
    )
    closed = preds.close_run("run-opssat-1", closed_at="2026-11-26T11:30:00Z")
    joined = gt_store.join_predictions_to_labels(
        role="evaluator", run_id="run-opssat-1", predictions=closed
    )
    assert len(joined) == 1
    assert joined[0].dataset_id == OPSSAT_AD_LOOKALIKE_DATASET_ID
    assert joined[0].ground_truth.split == "test"
    assert joined[0].ground_truth.label_value is True


def test_missing_real_files_return_explicit_skipped_without_local_paths(
    tmp_path: Path,
) -> None:
    empty_dir = tmp_path / "no_zenodo_here"
    bundle = import_opssat_ad(empty_dir, mode="real")
    assert bundle.report.status == "skipped"
    assert bundle.report.checksums_verified is False
    assert set(bundle.report.missing_files) == {"dataset.csv", "segments.csv"}
    assert bundle.telemetry_events == []
    assert bundle.ground_truth == []
    serialized = json.dumps(bundle.report.model_dump())
    assert str(tmp_path) not in serialized
    assert "10.5281/zenodo.12588359" in serialized


def test_real_mode_checksum_verification_and_spoofing_fail_closed(
    tmp_path: Path,
) -> None:
    src = _copy_lookalike(tmp_path / "fake_real")
    # Default real mode verifies official Zenodo MD5s -> lookalike files fail closed.
    with pytest.raises(AdapterError, match="checksum mismatch"):
        import_opssat_ad(src, mode="real", verify_checksums=True)

    # When manifest MD5s match the local files, real import succeeds with sample_kind="real".
    manifest = load_opssat_ad_manifest()
    custom_manifest = manifest.model_copy(
        update={
            "expected_files": {
                "dataset.csv": FileChecksumEntry(
                    md5=hashlib.md5((src / "dataset.csv").read_bytes()).hexdigest()
                ),
                "segments.csv": FileChecksumEntry(
                    md5=hashlib.md5((src / "segments.csv").read_bytes()).hexdigest()
                ),
            }
        }
    )
    bundle = import_opssat_ad(
        src, mode="real", manifest=custom_manifest, verify_checksums=True
    )
    assert bundle.report.status == "imported"
    assert bundle.report.checksums_verified is True
    assert bundle.report.dataset_id == OPSSAT_AD_DATASET_ID
    assert bundle.telemetry_events[0].metadata["sample_kind"] == "real"

    # Spoofing lookalike as real or real as synthetic fails closed in OPSSATADAdapter.
    adapter = OPSSATADAdapter(load_registry())
    row = {
        "segment": "0",
        "channel": "CADC0872",
        "timestamp": "2021-06-14T08:00:00Z",
        "value": 0.1,
        "sampling": "1",
    }
    spoof_lookalike_real = ProvenanceRecord(
        dataset_id=OPSSAT_AD_LOOKALIKE_DATASET_ID,
        mission_id=OPSSAT_MISSION_ID,
        version="1",
        license_spdx="LicenseRef-SpaceOps-Synthetic",
        source_url="fixture:tests/fixtures/opssat_ad_lookalike",
        sample_kind="real",
    )
    with pytest.raises(AdapterError):
        adapter.adapt(row, spoof_lookalike_real)


def test_reentry_columns_invalid_values_and_cross_file_mismatch_fail_closed(
    tmp_path: Path,
) -> None:
    adapter = OPSSATADAdapter(load_registry())
    prov = ProvenanceRecord(
        dataset_id=OPSSAT_AD_LOOKALIKE_DATASET_ID,
        mission_id=OPSSAT_MISSION_ID,
        version="1",
        license_spdx="LicenseRef-SpaceOps-Synthetic",
        source_url="fixture:tests/fixtures/opssat_ad_lookalike",
        sample_kind="synthetic",
    )
    base_row = {
        "segment": "0",
        "channel": "CADC0872",
        "timestamp": "2021-06-14 08:00:00",
        "value": 0.1,
        "sampling": "1",
    }

    # Re-entry columns rejected on both telemetry and ground-truth extraction.
    for col in ("Battery_Voltage", "Battery_Temp", "PD1_CSS_theta", "RSSI", "altitude"):
        with pytest.raises(AdapterError, match="re-entry"):
            adapter.adapt({**base_row, col: 1.0}, prov)
        with pytest.raises(AdapterError, match="re-entry"):
            adapter.extract_ground_truth(
                {"segment": "0", "anomaly": "0", "train": "1", col: 1.0}, prov
            )

    # Non-finite, boolean value, unregistered channel, or bad binary flag fail closed.
    with pytest.raises(AdapterError):
        adapter.adapt({**base_row, "value": float("nan")}, prov)
    with pytest.raises(AdapterError):
        adapter.adapt({**base_row, "value": True}, prov)
    with pytest.raises(RegistryError):
        adapter.adapt({**base_row, "channel": "UNKNOWN_CH"}, prov)
    with pytest.raises(AdapterError):
        adapter.extract_ground_truth(
            {"segment": "0", "anomaly": "2", "train": "1"}, prov
        )

    # Cross-file label disagreement fails closed.
    bad_dir = _copy_lookalike(tmp_path / "mismatch")
    ds_text = (bad_dir / "dataset.csv").read_text(encoding="utf-8")
    (bad_dir / "dataset.csv").write_text(
        ds_text.replace("0,CADC0872,1,0,1,", "0,CADC0872,1,1,1,"), encoding="utf-8"
    )
    with pytest.raises(AdapterError, match="anomaly label mismatch"):
        import_opssat_ad(bad_dir, mode="lookalike")


def test_write_outputs_enforces_directory_separation_and_cli_works_offline(
    tmp_path: Path, capsys
) -> None:
    tm_dir = tmp_path / "telemetry_out"
    gt_dir = tmp_path / "ground_truth_out"

    rc = import_cli.main(
        [
            "--lookalike",
            "--telemetry-out",
            str(tm_dir),
            "--ground-truth-out",
            str(gt_dir),
        ]
    )
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "imported"
    assert report["audit"]["total_segments"] == 4
    assert str(tmp_path) not in json.dumps(report)

    tm_file = tm_dir / "opssat_ad_lookalike_telemetry.ndjson"
    gt_file = gt_dir / "opssat_ad_lookalike_ground_truth.ndjson"
    assert tm_file.is_file()
    assert gt_file.is_file()
    assert len(tm_file.read_text(encoding="utf-8").splitlines()) == 9
    assert len(gt_file.read_text(encoding="utf-8").splitlines()) == 4

    # Overlapping directories fail closed before writing.
    bundle = import_opssat_ad(DEFAULT_LOOKALIKE_DIR, mode="lookalike")
    with pytest.raises(IsolationError):
        write_opssat_ad_outputs(
            bundle, telemetry_out_dir=tm_dir, ground_truth_out_dir=tm_dir
        )
    with pytest.raises(IsolationError):
        write_opssat_ad_outputs(
            bundle,
            telemetry_out_dir=tm_dir,
            ground_truth_out_dir=ROOT / "data" / "telemetry" / "nested_gt",
        )


def test_timestamp_normalization_and_cli_no_network_imports() -> None:
    assert normalize_opssat_timestamp("2021-06-14 08:00:00") == "2021-06-14T08:00:00Z"
    assert (
        normalize_opssat_timestamp("2021-06-14 08:00:00.250000")
        == "2021-06-14T08:00:00.250000Z"
    )
    assert (
        normalize_opssat_timestamp("2021-06-14T10:00:00+02:00")
        == "2021-06-14T08:00:00Z"
    )

    banned = {"requests", "httpx", "urllib", "socket", "http", "aiohttp", "subprocess"}
    cli_path = ROOT / "scripts" / "import_opssat_ad.py"
    tree = ast.parse(cli_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(banned), f"{cli_path}: {imported & banned}"
