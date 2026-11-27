"""RD3.3 slice manifest and bounded replay on the ESA-AD lookalike."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from apps.mission_data.adapter import AdapterError
from apps.mission_data.esa_ad import (
    DEFAULT_ESA_AD_LOOKALIKE_DIR,
    SliceReplayManifest,
    canonical_import_md5,
    commit_slice_import,
    replay_slice_event_ids,
    verify_slice_import,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"
CODE_REVISION = "rd3.3-lookalike"
WINDOW_START = "2020-01-01T00:00:00Z"
WINDOW_END = "2020-01-03T00:00:00Z"


def _replay(manifest):
    return SliceReplayManifest(
        code_revision=manifest.code_revision,
        import_md5=canonical_import_md5(manifest),
        mission_id=manifest.mission_id,
        dataset_ids=list(manifest.dataset_ids),
        time_range_start=WINDOW_START,
        time_range_end=WINDOW_END,
    )


def test_two_replays_return_the_same_ids(tmp_path: Path) -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    dest = tmp_path / "manifest.json"
    manifest = commit_slice_import(
        DEFAULT_ESA_AD_LOOKALIKE_DIR,
        dest,
        code_revision=CODE_REVISION,
        byte_budget=1_000_000,
    )
    text = dest.read_text(encoding="utf-8")
    assert "1.5" not in text
    assert "NOMINAL" not in text
    assert manifest.byte_budget == 1_000_000
    assert manifest.bytes_planned < manifest.byte_budget
    assert manifest.mission_id == "esa-ad"
    assert manifest.dataset_ids == [
        "esa-ad-mission1-lookalike",
        "esa-ad-mission2-lookalike",
        "esa-ad-mission3-lookalike",
    ]
    replay = _replay(manifest)
    first = replay_slice_event_ids(manifest, replay, DEFAULT_ESA_AD_LOOKALIKE_DIR)
    second = replay_slice_event_ids(manifest, replay, DEFAULT_ESA_AD_LOOKALIKE_DIR)
    assert first == second
    assert first[0] == "esa-ad-mission1-lookalike:channel_1:0"
    assert len(first) == 4
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_changed_checksum_fails(tmp_path: Path) -> None:
    source = tmp_path / "slice"
    source.mkdir()
    original = DEFAULT_ESA_AD_LOOKALIKE_DIR
    for path in original.rglob("*.csv"):
        target = source / path.relative_to(original)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    manifest = commit_slice_import(
        source,
        tmp_path / "ok.json",
        code_revision=CODE_REVISION,
        byte_budget=1_000_000,
    )
    telemetry = source / "mission1" / "telemetry.csv"
    telemetry.write_bytes(telemetry.read_bytes() + b"\n")
    with pytest.raises(AdapterError, match="checksum mismatch"):
        verify_slice_import(manifest, source)


def test_over_budget_writes_nothing(tmp_path: Path) -> None:
    dest = tmp_path / "nested" / "manifest.json"
    with pytest.raises(AdapterError, match="exceeds the byte budget"):
        commit_slice_import(
            DEFAULT_ESA_AD_LOOKALIKE_DIR,
            dest,
            code_revision=CODE_REVISION,
            byte_budget=1,
        )
    assert not dest.exists()
    assert not dest.parent.exists()
