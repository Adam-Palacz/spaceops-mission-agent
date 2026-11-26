"""Read-only OPS-SAT replay (RD2.3).

CI runs the OPSSAT-AD lookalike through the existing telemetry view and a
channel table. It does not call a model, does not call write tools, and does
not read the re-entry campaign. A model-backed report on licensed real data
is still required before this task is Done.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from apps.mission_data.egress import load_egress_approvals
from apps.mission_data.isolation import (
    InvestigationTelemetryView,
    OPSSAT_AD_DATASET_ID,
    OPSSAT_MISSION_ID,
    OPSSAT_REENTRY_UHF_DATASET_ID,
)
from apps.mission_data.opssat_ad import (
    DEFAULT_LOOKALIKE_DIR,
    OPSSAT_AD_LOOKALIKE_DATASET_ID,
    import_opssat_ad,
)
from apps.mission_data.registry import MissionRegistry, load_registry

LOOKALIKE_TIME_START = "2021-06-14T08:00:00Z"
LOOKALIKE_TIME_END = "2021-06-14T08:31:00Z"
REENTRY_EXCLUSION = "opssat-reentry-uhf is excluded because its license is unrecorded"


class CitationError(ValueError):
    """Raised when a report names a channel the telemetry tool did not return."""


class ReadonlyPassReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "plumbing_only"
    model_backed: bool = False
    model: None = None
    mission_id: str
    dataset_id: str
    policy_revision: str
    channels_queried: list[str] = Field(default_factory=list)
    write_tool_calls: int = 0
    excluded: str
    table_markdown: str
    report_text: str


def require_report_channels(
    report_text: str,
    *,
    queried_channels: set[str],
    known_channels: set[str],
) -> None:
    """Fail when the report names a registered channel outside the query result."""
    extra = sorted(
        channel
        for channel in known_channels
        if channel not in queried_channels
        and re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(channel)}(?![A-Za-z0-9_])", report_text
        )
    )
    if extra:
        raise CitationError(
            f"report cites channels the telemetry tool did not return: {extra}"
        )


def _markdown_table(rows: list[dict]) -> str:
    lines = ["| channel | ts | value | unit |", "| --- | --- | --- | --- |"]
    for row in rows:
        unit = row.get("unit")
        unit_text = "" if unit is None else str(unit)
        lines.append(
            f"| {row.get('channel')} | {row.get('ts')} | {row.get('value')} | {unit_text} |"
        )
    return "\n".join(lines)


def run_opssat_ad_lookalike_pass(
    *,
    registry: MissionRegistry | None = None,
) -> ReadonlyPassReport:
    """Query the lookalike and cite only those channels. No model and no writes."""
    bundle = import_opssat_ad(DEFAULT_LOOKALIKE_DIR, mode="lookalike")
    view = InvestigationTelemetryView(
        [event.model_dump() for event in bundle.telemetry_events]
    )
    rows = view.query(
        time_range_start=LOOKALIKE_TIME_START,
        time_range_end=LOOKALIKE_TIME_END,
        mission_id=OPSSAT_MISSION_ID,
        dataset_ids=[OPSSAT_AD_LOOKALIKE_DATASET_ID],
    )
    channels = sorted({str(row["channel"]) for row in rows})
    active_registry = registry or load_registry()
    table = _markdown_table(rows)
    report_text = (
        f"Dataset {OPSSAT_AD_LOOKALIKE_DATASET_ID} on mission {OPSSAT_MISSION_ID}. "
        f"Queried channels: {', '.join(channels)}. "
        f"{REENTRY_EXCLUSION}. "
        "No model was called. Write tools were not called."
    )
    require_report_channels(
        report_text,
        queried_channels=set(channels),
        known_channels=set(active_registry.channels_for_mission(OPSSAT_MISSION_ID)),
    )
    if OPSSAT_AD_DATASET_ID == OPSSAT_AD_LOOKALIKE_DATASET_ID:
        raise CitationError("lookalike dataset id must stay distinct from opssat-ad")
    return ReadonlyPassReport(
        mission_id=OPSSAT_MISSION_ID,
        dataset_id=OPSSAT_AD_LOOKALIKE_DATASET_ID,
        policy_revision=load_egress_approvals().policy_revision,
        channels_queried=channels,
        write_tool_calls=0,
        excluded=f"{OPSSAT_REENTRY_UHF_DATASET_ID}: {REENTRY_EXCLUSION}",
        table_markdown=table,
        report_text=report_text,
    )
