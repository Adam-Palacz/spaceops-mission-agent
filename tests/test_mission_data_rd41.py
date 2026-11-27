"""RD4.1 cited public-source registry."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from apps.mcp.kb_server.index_kb import load_cited_source_docs
from apps.mission_data.cited_sources import (
    CitedSource,
    CitedSourceError,
    CitedSourceRegistry,
    index_rows,
    load_cited_sources,
    validate_source,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def test_registry_explains_each_accepted_source() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    registry = load_cited_sources()
    accepted = [item for item in registry.sources if item.status == "accepted"]
    assert [item.source_id for item in accepted] == [
        "nasa-llis-2046",
        "esa-ad-zenodo-12528696",
    ]
    assert all(
        item.license_spdx.strip() and item.why_present.strip() for item in accepted
    )
    nasa = accepted[0]
    assert nasa.excerpt_allowed is False
    assert nasa.excerpt == ""
    rows = load_cited_source_docs()
    assert [row[0] for row in rows] == [item.source_id for item in accepted]
    assert all(row[0] in row[2] for row in rows)
    assert "source_id: nasa-llis-2046" in rows[0][2]
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_missing_license_fails_import() -> None:
    source = CitedSource(
        source_id="example-unlicensed",
        title="Untitled public note",
        publisher="Example",
        published_on="2020-01-01",
        url="https://example.test/report",
        license_spdx="",
        access="public",
        status="accepted",
        why_present="Would have been a citation target.",
    )
    with pytest.raises(CitedSourceError, match="missing a license"):
        validate_source(source)
    registry = CitedSourceRegistry(
        schema_version="rd4.cited-sources.v1",
        sources=[source.model_copy(update={"status": "rejected", "license_spdx": ""})],
    )
    assert index_rows(registry) == []
