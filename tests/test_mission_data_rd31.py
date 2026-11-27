"""RD3.1 ESA-AD contexts, slice isolation, and the Mission3 benchmark holdout."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from apps.mission_data.adapter import AdapterError
from apps.mission_data.esa_ad import (
    MISSION3_OVERRIDE,
    benchmark_selection,
    iter_lookalike_events,
    load_esa_ad_manifest,
    lookalike_dataset_id,
    refuse_real_import,
)
from apps.mission_data.isolation import InvestigationTelemetryView

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def test_three_contexts_and_published_benchmark_holdout() -> None:
    manifest = load_esa_ad_manifest()
    assert manifest.license_spdx == "CC-BY-3.0-IGO"
    assert manifest.code_license_spdx == "MIT"
    assert manifest.checksums_pinned is False
    assert manifest.full_import_allowed is False
    assert manifest.experiment_artifacts_gib == 512
    keys = [item.key for item in manifest.missions]
    assert keys == ["mission1", "mission2", "mission3"]
    selection = benchmark_selection()
    assert selection.dataset_ids == ["esa-ad-mission1", "esa-ad-mission2"]
    assert selection.includes_mission3 is False
    assert "esa-ad-mission3" not in selection.report_text
    override = benchmark_selection(include_mission3=True)
    assert override.dataset_ids[-1] == "esa-ad-mission3"
    assert override.report_text == MISSION3_OVERRIDE
    with pytest.raises(AdapterError, match="checksums are not pinned"):
        refuse_real_import()


def test_mission_slice_is_invisible_to_the_other_mission() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    mission1 = list(iter_lookalike_events("mission1"))
    mission2 = list(iter_lookalike_events("mission2"))
    assert len(mission1) == 1
    assert mission1[0].value == 1.5
    assert mission1[0].metadata["dataset_id"] == lookalike_dataset_id("esa-ad-mission1")
    assert mission1[0].metadata["sample_kind"] == "synthetic"
    view = InvestigationTelemetryView(
        [event.model_dump() for event in (*mission1, *mission2)]
    )
    seen = view.query(
        time_range_start="2020-01-01T00:00:00Z",
        time_range_end="2020-01-03T00:00:00Z",
        mission_id="esa-ad",
        dataset_ids=[lookalike_dataset_id("esa-ad-mission1")],
    )
    assert [row["value"] for row in seen] == [1.5]
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_full_archives_and_network_imports_are_absent(tmp_path: Path) -> None:
    (tmp_path / "ESA-Mission1.zip").write_bytes(b"not-a-real-archive")
    with pytest.raises(AdapterError, match="not downloaded"):
        refuse_real_import()
    fixture = ROOT / "tests" / "fixtures" / "esa_ad_lookalike"
    assert list(fixture.rglob("*.zip")) == []
    tree = ast.parse(
        (ROOT / "apps" / "mission_data" / "esa_ad.py").read_text(encoding="utf-8")
    )
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
    assert imported.isdisjoint({"requests", "httpx", "urllib", "socket", "zipfile"})


def test_label_column_on_a_slice_is_rejected(tmp_path: Path) -> None:
    mission_dir = tmp_path / "mission1"
    mission_dir.mkdir()
    (mission_dir / "telemetry.csv").write_text(
        "timestamp,channel,value,anomaly\n2020-01-01 00:00:00,channel_1,1.0,1\n",
        encoding="utf-8",
    )
    with pytest.raises(AdapterError, match="cannot carry labels"):
        next(iter_lookalike_events("mission1", source_dir=tmp_path))
