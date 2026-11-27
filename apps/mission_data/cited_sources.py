"""Curated public-source registry for historical KB citations (RD4.1).

The list is hand-maintained. Nothing here scrapes a site or stores a report body
unless that source explicitly allows an excerpt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.mission_data.provenance import require_non_blank
from apps.mission_data.registry import REPO_ROOT

DEFAULT_CITED_SOURCES = REPO_ROOT / "data" / "mission_registry" / "cited_sources.json"

SourceAccess = Literal[
    "public", "paywalled", "export_controlled", "operational_procedure"
]
SourceStatus = Literal["accepted", "rejected"]


class CitedSourceError(ValueError):
    """A cited source record breaks the registry rules."""


class CitedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    publisher: str = Field(..., min_length=1)
    published_on: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    license_spdx: str = ""
    license_note: str = ""
    excerpt_allowed: bool = False
    excerpt: str = ""
    access: SourceAccess = "public"
    status: SourceStatus
    why_present: str = Field(..., min_length=1)

    @field_validator(
        "source_id", "title", "publisher", "published_on", "url", "why_present"
    )
    @classmethod
    def reject_blank(cls, value: str, info: object) -> str:
        name = getattr(info, "field_name", None) or "field"
        return require_non_blank(value, name)


class CitedSourceRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd4.cited-sources.v1"]
    sources: list[CitedSource] = Field(..., min_length=1)


def load_cited_sources(path: Path | None = None) -> CitedSourceRegistry:
    payload = json.loads((path or DEFAULT_CITED_SOURCES).read_text(encoding="utf-8"))
    registry = CitedSourceRegistry.model_validate(payload)
    for source in registry.sources:
        validate_source(source)
    return registry


def validate_source(source: CitedSource) -> None:
    """Accept a source only with a license, public access, and a justified excerpt."""
    if source.status != "accepted":
        return
    if source.access != "public":
        raise CitedSourceError(f"{source.source_id} is not a public source")
    if not source.license_spdx.strip():
        raise CitedSourceError(f"{source.source_id} is missing a license")
    if source.excerpt_allowed:
        if not source.excerpt.strip():
            raise CitedSourceError(
                f"{source.source_id} allows an excerpt but stores none"
            )
    elif source.excerpt.strip():
        raise CitedSourceError(
            f"{source.source_id} stores an excerpt its license does not allow"
        )


def index_rows(registry: CitedSourceRegistry | None = None) -> list[dict[str, str]]:
    """Indexer rows. Each accepted source is cited by its registry id."""
    active = registry or load_cited_sources()
    rows: list[dict[str, str]] = []
    for source in active.sources:
        if source.status != "accepted":
            continue
        validate_source(source)
        parts = [
            f"source_id: {source.source_id}",
            source.title,
            source.publisher,
            source.published_on,
            source.url,
            source.license_spdx,
            source.why_present,
        ]
        if source.excerpt_allowed:
            parts.append(source.excerpt.strip())
        rows.append(
            {
                "doc_id": source.source_id,
                "source_id": source.source_id,
                "content": "\n".join(parts),
            }
        )
    return rows
