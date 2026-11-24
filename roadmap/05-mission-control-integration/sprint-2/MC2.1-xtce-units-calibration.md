# MC2.1 - XTCE subset, units, and calibration

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Engineering values need the definition that produced them. A raw count without a calibration is a different measurement.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The channel registry from RD1 has unit text. It does not parse XTCE.

## Requirements

- Accept the XTCE subset Yamcs exports for parameters used by the connector: name, unit, type, and calibration description.
- CCSDS packet decoding is in scope only for packets the local Yamcs tutorial already decodes. No new link protocol implementation is required to exit this task.
- Uncalibrated values stay marked uncalibrated.

## Functional and non-functional requirements

- Accept the XTCE subset Yamcs exports for parameters used by the connector: name, unit, type, and calibration description.
- CCSDS packet decoding is in scope only for packets the local Yamcs tutorial already decodes. No new link protocol implementation is required to exit this task.
- Uncalibrated values stay marked uncalibrated.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- RD1 registry and MC1.2 export.

## Dependencies

- MC1.2
- RD1.2

## Implementation checklist

- [ ] Parse a small XTCE fixture.
- [ ] Show a calibrated and an uncalibrated parameter.

## Test requirements

- The fixture's unit arrives in the registry.
- A missing calibration does not invent a scale factor.

## Testing requirements

- The fixture's unit arrives in the registry.
- A missing calibration does not invent a scale factor.

## Security and safety requirements

- Do not import a third-party mission's XTCE unless its license is recorded.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- RD1 channel entries can be generated from the fixture and from local Yamcs.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
