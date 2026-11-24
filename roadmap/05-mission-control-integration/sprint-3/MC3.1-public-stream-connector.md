# MC3.1 - Public stream connector

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Live frames show gaps and delay. They are a different evaluation from OPSSAT-AD and ESA-AD.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Ingest already publishes telemetry to JetStream when `NATS_URL` is set. No public satellite client exists.

## Requirements

- Choose SatNOGS or another public API only after recording its terms.
- The stream's dataset id is distinct from every historical benchmark.
- Frames from the May 2024 OPS-SAT campaign are not replayed as if they were new live data.
- The connector is off in CI.

## Functional and non-functional requirements

- Choose SatNOGS or another public API only after recording its terms.
- The stream's dataset id is distinct from every historical benchmark.
- Frames from the May 2024 OPS-SAT campaign are not replayed as if they were new live data.
- The connector is off in CI.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing NATS ingest and RD1 adapter.

## Dependencies

- RD1.1
- MC2.1 for units when the source has them.

## Implementation checklist

- [ ] Record the source terms.
- [ ] Map one public frame type into `TelemetryEventV1` in a fixture test.
- [ ] Keep the client disabled by default.

## Test requirements

- The fixture does not join to OPSSAT-AD labels.
- Default configuration does not open a network socket.

## Testing requirements

- The fixture does not join to OPSSAT-AD labels.
- Default configuration does not open a network socket.

## Security and safety requirements

- Do not collect or store observer account identifiers.
- Stop the client when the terms are unclear.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A live capture, if run, is labeled live-public and is absent from the benchmark tables.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
