"""Cited failure modes for investigation (RD4.2).

Corrective action is operator text. It is not a proposed action and it is not
an OPA allowlist entry. A source that forbids excerpts keeps its public title
and stores no procedure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.mission_data.cited_sources import CitedSourceRegistry, load_cited_sources
from apps.mission_data.isolation import ToolRole, require_tool_access
from apps.mission_data.provenance import require_non_blank
from apps.mission_data.registry import REPO_ROOT

DEFAULT_FAILURE_MODES = REPO_ROOT / "data" / "mission_registry" / "failure_modes.json"

CORRECTIVE_ACTION_NOT_STORED = (
    "No public corrective action is stored. This record is not an executable plan."
)
FORBIDDEN_ACTION_TOKENS = (
    "change_config",
    "restart_service",
    "proposed_actions",
)


class FailureModeError(ValueError):
    """A failure-mode record breaks the citation or action rules."""


class FailureMode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    failure_mode: str = Field(..., min_length=1)
    subsystem: str = Field(..., min_length=1)
    symptoms: list[str] = Field(default_factory=list)
    corrective_action: str = Field(..., min_length=1)
    conflicts_with: list[str] = Field(default_factory=list)

    @field_validator(
        "mode_id", "source_id", "failure_mode", "subsystem", "corrective_action"
    )
    @classmethod
    def reject_blank(cls, value: str, info: object) -> str:
        name = getattr(info, "field_name", None) or "field"
        return require_non_blank(value, name)


class FailureModeCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd4.failure-modes.v1"]
    modes: list[FailureMode] = Field(..., min_length=1)


def load_failure_modes(
    path: Path | None = None,
    registry: CitedSourceRegistry | None = None,
) -> FailureModeCatalog:
    payload = json.loads((path or DEFAULT_FAILURE_MODES).read_text(encoding="utf-8"))
    catalog = FailureModeCatalog.model_validate(payload)
    validate_catalog(catalog, registry or load_cited_sources())
    return catalog


def validate_catalog(
    catalog: FailureModeCatalog, registry: CitedSourceRegistry
) -> None:
    """Keep conflicting sources apart and refuse executable action names."""
    accepted = {
        source.source_id: source
        for source in registry.sources
        if source.status == "accepted"
    }
    by_id = {mode.mode_id: mode for mode in catalog.modes}
    if len(by_id) != len(catalog.modes):
        raise FailureModeError("duplicate failure-mode id")
    for mode in catalog.modes:
        source = accepted.get(mode.source_id)
        if source is None:
            raise FailureModeError(f"{mode.mode_id} cites an unknown source")
        _reject_action_tokens(mode)
        if source.excerpt_allowed:
            continue
        if mode.failure_mode != source.title:
            raise FailureModeError(
                f"{mode.mode_id} stores text its source does not allow"
            )
        if mode.symptoms:
            raise FailureModeError(
                f"{mode.mode_id} stores symptoms its source does not allow"
            )
        if mode.corrective_action != CORRECTIVE_ACTION_NOT_STORED:
            raise FailureModeError(
                f"{mode.mode_id} stores a procedure its source does not allow"
            )
    for mode in catalog.modes:
        for other_id in mode.conflicts_with:
            other = by_id.get(other_id)
            if other is None or other.mode_id == mode.mode_id:
                raise FailureModeError(f"{mode.mode_id} names a missing conflict")
            if mode.mode_id not in other.conflicts_with:
                raise FailureModeError(
                    f"{mode.mode_id} conflict is not recorded on both"
                )
            if mode.failure_mode == other.failure_mode:
                raise FailureModeError(f"{mode.mode_id} merges conflicting causes")


def search_failure_modes(
    query: str,
    catalog: FailureModeCatalog | None = None,
) -> list[dict[str, Any]]:
    """Return cited modes whose text matches. Results carry source ids, not tools."""
    needle = require_non_blank(query, "query").casefold()
    active = catalog or load_failure_modes()
    rows: list[dict[str, Any]] = []
    for mode in active.modes:
        haystack = "\n".join(
            [
                mode.mode_id,
                mode.source_id,
                mode.failure_mode,
                mode.subsystem,
                mode.corrective_action,
                *mode.symptoms,
            ]
        ).casefold()
        if needle not in haystack:
            continue
        rows.append(
            {
                "mode_id": mode.mode_id,
                "source_id": mode.source_id,
                "failure_mode": mode.failure_mode,
                "subsystem": mode.subsystem,
                "symptoms": list(mode.symptoms),
                "corrective_action": mode.corrective_action,
                "conflicts_with": list(mode.conflicts_with),
            }
        )
    return rows


def retrieve_failure_modes(query: str, *, role: ToolRole) -> list[dict[str, Any]]:
    """Investigation read. This does not add a write tool."""
    require_tool_access("search_failure_modes", role)
    return search_failure_modes(query)


def _reject_action_tokens(mode: FailureMode) -> None:
    blob = " ".join(
        [
            mode.mode_id,
            mode.source_id,
            mode.failure_mode,
            mode.subsystem,
            mode.corrective_action,
            *mode.symptoms,
            *mode.conflicts_with,
        ]
    ).casefold()
    for token in FORBIDDEN_ACTION_TOKENS:
        if token in blob:
            raise FailureModeError(f"{mode.mode_id} names an executable action")
