"""Read-only OPS-SAT replay (RD2.3).

CI runs the OPSSAT-AD lookalike through the existing telemetry view and a
channel table. It does not call a model, does not call write tools, and does
not read the re-entry campaign. A licensed real pass may call only a loopback
model after the egress check, and it never includes ground-truth labels.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from apps.mission_data.egress import (
    EgressRequest,
    evaluate_egress,
    is_loopback_endpoint,
    load_egress_approvals,
)
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


LOCAL_OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
_PROMPT_ROW_LIMIT = 12


class LicensedLocalModelReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "model_backed"
    model_backed: bool = True
    model: str
    mission_id: str
    dataset_id: str
    license_spdx: str
    policy_revision: str
    channels_queried: list[str]
    write_tool_calls: int = 0
    excluded: str
    citation_check: str
    report_text: str


def run_opssat_ad_licensed_local_pass(
    source_dir: Path,
    *,
    model: str,
    complete: Callable[[str, str, str], str],
    endpoint: str = LOCAL_OLLAMA_CHAT,
    registry: MissionRegistry | None = None,
) -> LicensedLocalModelReport:
    """One read-only model report on checksum-verified OPSSAT-AD files.

    Ground truth stays out of the prompt. The call is refused unless egress
    allows a loopback target. Write tools are not invoked.
    """
    if not is_loopback_endpoint(endpoint):
        raise CitationError("licensed pass refuses a non-loopback model endpoint")
    bundle = import_opssat_ad(source_dir, mode="real")
    if bundle.report.status != "imported":
        raise CitationError(
            bundle.report.skip_reason or "OPSSAT-AD import did not complete"
        )
    events = [event.model_dump() for event in bundle.telemetry_events]
    if not events:
        raise CitationError("imported OPSSAT-AD telemetry is empty")
    ordered = sorted(events, key=lambda row: str(row.get("ts") or ""))
    window = ordered[:_PROMPT_ROW_LIMIT]
    start = str(window[0]["ts"])
    end = str(window[-1]["ts"])
    view = InvestigationTelemetryView(events)
    rows = view.query(
        time_range_start=start,
        time_range_end=end,
        mission_id=OPSSAT_MISSION_ID,
        dataset_ids=[OPSSAT_AD_DATASET_ID],
    )
    shown = rows[:_PROMPT_ROW_LIMIT]
    channels = sorted({str(row["channel"]) for row in shown})
    if not channels:
        raise CitationError("telemetry tool returned no rows for the licensed window")
    table = _markdown_table(shown)
    prompt = (
        "You are investigating satellite telemetry. Use only the table below. "
        "Name only channels that appear in the table. Do not recommend a command, "
        "a ticket, or a pull request. Do not invent labels or root causes.\n\n"
        f"Dataset {OPSSAT_AD_DATASET_ID}. Mission {OPSSAT_MISSION_ID}. "
        f"{REENTRY_EXCLUSION}.\n\n{table}"
    )
    if re.search(r"\b(anomaly|train|label|nominal)\b", prompt, flags=re.IGNORECASE):
        raise CitationError("prompt must not carry ground-truth words")
    active_registry = registry or load_registry()
    policy = load_egress_approvals()
    decision = evaluate_egress(
        EgressRequest(
            data_class="historical_public",
            dataset_ids=[OPSSAT_AD_DATASET_ID],
            version_or_checksum=f"zenodo-{bundle.report.zenodo_doi}",
            purpose="rd2.3-readonly-local-pass",
            provider="local",
            endpoint_url=endpoint,
            model_id=model,
            processing_kind="chat_completion",
            payload_fields={"channel": True, "ts": True, "value": True, "unit": True},
            outbound_text=prompt,
            contains_ground_truth=False,
            local_only=True,
        )
    )
    if not decision.decision.allowed:
        raise CitationError(
            f"egress denied the local model call: {decision.decision.reason_code}"
        )
    report_text = complete(endpoint, model, prompt)
    if not isinstance(report_text, str) or not report_text.strip():
        raise CitationError("local model returned an empty report")
    report_text = report_text.strip()
    require_report_channels(
        report_text,
        queried_channels=set(channels),
        known_channels=set(active_registry.channels_for_mission(OPSSAT_MISSION_ID)),
    )
    return LicensedLocalModelReport(
        model=model,
        mission_id=OPSSAT_MISSION_ID,
        dataset_id=OPSSAT_AD_DATASET_ID,
        license_spdx=bundle.report.license_spdx,
        policy_revision=policy.policy_revision,
        channels_queried=channels,
        write_tool_calls=0,
        excluded=f"{OPSSAT_REENTRY_UHF_DATASET_ID}: {REENTRY_EXCLUSION}",
        citation_check="pass",
        report_text=report_text,
    )
