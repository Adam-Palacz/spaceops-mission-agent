# RD1.2 - Mission, spacecraft, and channel registry

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Owner** | Unassigned |
| **Implements code** | Yes. `data/mission_registry/registry.json` names channels only. |

## Objective and rationale

Real channels have units, sample rates, and subsystems. The synthetic names `temp_plate_1` and `bus_voltage` are not a mission database.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- `subsystem` and `unit` are optional free strings.
- No registry maps a channel to a spacecraft, sensor, or calibration.

## Requirements

- Registry entries for mission, spacecraft, subsystem, and channel.
- Channel metadata records unit, sampling description, numeric or categorical kind, and the source name used by the dataset.
- Unknown channels fail closed at adapter time.
- The registry is versioned in git and cites its source. It is not scraped from a live mission control system.

## Functional and non-functional requirements

- Registry entries for mission, spacecraft, subsystem, and channel.
- Channel metadata records unit, sampling description, numeric or categorical kind, and the source name used by the dataset.
- Unknown channels fail closed at adapter time.
- The registry is versioned in git and cites its source. It is not scraped from a live mission control system.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- New versioned registry documents or tables. XTCE import is phase 05, not this task.
- Telemetry MCP `query_telemetry` must be able to filter by the registry's mission or dataset id once events carry it.

## Dependencies

- RD1.1 provenance keys.

## Implementation checklist

- [x] Define the registry schema with one synthetic mission marked `synthetic`.
- [x] Add the nine OPSSAT-AD channel names as registered channels without importing samples.
- [x] Reject a channel that is not in the registry.

## Test requirements

- Synthetic and OPSSAT-AD channel names do not collide.
- A query for one mission does not return another mission's channels.

## Testing requirements

- Synthetic and OPSSAT-AD channel names do not collide.
- A query for one mission does not return another mission's channels.

## Security and safety requirements

- Do not copy unpublished calibration curves into the repo.
- Registry text must not include operator names or contact details.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- RD2 can map both OPS-SAT products onto registered channels.
- The synthetic mission remains explicitly labeled synthetic.

## Required execution evidence

- Sanitized note: [evidence/RD1-adapter-registry-2026-11-24.json](evidence/RD1-adapter-registry-2026-11-24.json).
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

The checklist, tests, and sanitized evidence note are in place. This does not change the 2026-11-23 No-go decision.
