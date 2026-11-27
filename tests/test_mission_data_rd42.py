"""RD4.2 cited failure modes stay text and stay searchable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from apps.mission_data.cited_sources import CitedSource, CitedSourceRegistry
from apps.mission_data.failure_modes import (
    CORRECTIVE_ACTION_NOT_STORED,
    FailureMode,
    FailureModeCatalog,
    FailureModeError,
    load_failure_modes,
    retrieve_failure_modes,
    search_failure_modes,
    validate_catalog,
)
from apps.mission_data.isolation import ToolAccessError

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def test_search_returns_the_cited_battery_mode_without_a_write_tool() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    catalog = load_failure_modes()
    mode = catalog.modes[0]
    assert mode.source_id == "nasa-llis-2046"
    assert mode.symptoms == []
    assert mode.corrective_action == CORRECTIVE_ACTION_NOT_STORED
    rows = retrieve_failure_modes("battery", role="investigation")
    assert rows[0]["source_id"] == "nasa-llis-2046"
    blob = json.dumps(rows)
    assert "change_config" not in blob
    assert "restart_service" not in blob
    assert "proposed_actions" not in rows[0]
    assert "action_type" not in rows[0]
    with pytest.raises(ToolAccessError):
        retrieve_failure_modes("battery", role="evaluator")
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_conflicting_sources_stay_separate() -> None:
    registry = CitedSourceRegistry(
        schema_version="rd4.cited-sources.v1",
        sources=[
            _source("src-vent"),
            _source("src-bias"),
        ],
    )
    catalog = FailureModeCatalog(
        schema_version="rd4.failure-modes.v1",
        modes=[
            _mode("vent", "src-vent", "cell vent path", conflicts_with=["bias"]),
            _mode("bias", "src-bias", "sensor bias path", conflicts_with=["vent"]),
        ],
    )
    validate_catalog(catalog, registry)
    rows = {
        row["mode_id"]: row["failure_mode"]
        for row in search_failure_modes("battery", catalog)
    }
    assert rows == {"vent": "cell vent path", "bias": "sensor bias path"}
    one_sided = catalog.model_copy(deep=True)
    one_sided.modes[1].conflicts_with = []
    with pytest.raises(FailureModeError, match="not recorded on both"):
        validate_catalog(one_sided, registry)


def test_executable_action_name_is_refused() -> None:
    registry = CitedSourceRegistry(
        schema_version="rd4.cited-sources.v1",
        sources=[_source("src-vent")],
    )
    mode = _mode("vent", "src-vent", "cell vent path")
    mode.corrective_action = "Run change_config on the pack."
    with pytest.raises(FailureModeError, match="executable action"):
        validate_catalog(
            FailureModeCatalog(schema_version="rd4.failure-modes.v1", modes=[mode]),
            registry,
        )


def _source(source_id: str) -> CitedSource:
    return CitedSource(
        source_id=source_id,
        title=f"Public note {source_id}",
        publisher="Example",
        published_on="2020-01-01",
        url=f"https://example.test/{source_id}",
        license_spdx="CC-BY-4.0",
        excerpt_allowed=True,
        excerpt="A short public note.",
        access="public",
        status="accepted",
        why_present="Conflict fixture.",
    )


def _mode(
    mode_id: str,
    source_id: str,
    failure_mode: str,
    conflicts_with: list[str] | None = None,
) -> FailureMode:
    return FailureMode(
        mode_id=mode_id,
        source_id=source_id,
        failure_mode=failure_mode,
        subsystem="battery",
        symptoms=["public symptom"],
        corrective_action="Operator reads the public note. No command is issued.",
        conflicts_with=conflicts_with or [],
    )
