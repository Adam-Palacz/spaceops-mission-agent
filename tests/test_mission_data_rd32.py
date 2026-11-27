"""RD3.2 annotation kinds on the ESA-AD lookalike slice."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from apps.mission_data.adapter import AdapterError
from apps.mission_data.esa_ad import (
    import_lookalike_annotations,
    iter_lookalike_categorical,
    lookalike_dataset_id,
    query_annotations,
)
from apps.mission_data.isolation import GroundTruthStore, ToolAccessError

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def test_annotation_kinds_are_counted_separately() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    report, records = import_lookalike_annotations()
    assert report.archives_downloaded is False
    assert "score" not in report.model_dump()
    assert report.anomaly_count == 3
    assert report.rare_nominal_count == 3
    assert report.telecommand_count == 2
    mission3 = next(
        item
        for item in report.missions
        if item.dataset_id == lookalike_dataset_id("esa-ad-mission3")
    )
    assert mission3.telecommand == 0
    anomalies = query_annotations(records, label_kind="anomaly")
    rare = query_annotations(records, label_kind="rare_nominal")
    telecommands = query_annotations(records, label_kind="telecommand")
    assert len(anomalies) == report.anomaly_count
    assert rare
    assert not any(item in anomalies for item in rare)
    assert all(item.label_kind == "telecommand" for item in telecommands)
    assert all(item.label_value is not True for item in telecommands)
    mission1_tc = next(
        item
        for item in telecommands
        if item.dataset_id == lookalike_dataset_id("esa-ad-mission1")
    )
    assert mission1_tc.label_value == "impact=low,priority=info"
    assert "execute" not in str(mission1_tc.label_value)
    anomaly_ranges = {
        (item.time_range_start, item.time_range_end) for item in anomalies
    }
    assert (
        mission1_tc.time_range_start,
        mission1_tc.time_range_end,
    ) not in anomaly_ranges
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_investigation_profile_cannot_read_annotations() -> None:
    _report, records = import_lookalike_annotations()
    store = GroundTruthStore(records)
    with pytest.raises(ToolAccessError):
        store.read_labels(
            role="investigation",
            mission_id="esa-ad",
            dataset_id=lookalike_dataset_id("esa-ad-mission1"),
        )


def test_categorical_channel_stays_text() -> None:
    event = next(iter_lookalike_categorical("mission1"))
    assert event.channel == "channel_status"
    assert event.value == "NOMINAL"
    assert isinstance(event.value, str)
    assert event.metadata["sample_kind"] == "synthetic"


def test_archive_in_the_slice_is_refused(tmp_path: Path) -> None:
    mission = tmp_path / "mission1"
    mission.mkdir()
    (mission / "notes.zip").write_bytes(b"not-an-archive")
    with pytest.raises(AdapterError, match="cannot contain archives"):
        import_lookalike_annotations(tmp_path)
