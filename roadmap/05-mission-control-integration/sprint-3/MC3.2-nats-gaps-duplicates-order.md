# MC3.2 - Gaps, duplicates, and out-of-order events

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The queue already deduplicates on `event_id` inside one ingest batch. A live stream needs a stated rule for late frames.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Batch ingest dedupes identical ids. It does not define lateness, reorder, or a gap alarm.

## Requirements

- Define lateness and duplicate behavior for the public stream.
- Gaps become visible events or metrics, not interpolated science values.
- Reordered frames do not rewrite an earlier benchmark dataset.
- Streaming detection from AV4 is optional and uses only this stream's dataset id.

## Functional and non-functional requirements

- Define lateness and duplicate behavior for the public stream.
- Gaps become visible events or metrics, not interpolated science values.
- Reordered frames do not rewrite an earlier benchmark dataset.
- Streaming detection from AV4 is optional and uses only this stream's dataset id.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- NATS consumer and telemetry table. AV4 incident path if enabled.

## Dependencies

- MC3.1

## Implementation checklist

- [ ] Specify the rules.
- [ ] Test duplicate, late, and gap fixtures.

## Test requirements

- A duplicate does not create a second row.
- A gap does not insert a synthetic measurement.

## Testing requirements

- A duplicate does not create a second row.
- A gap does not insert a synthetic measurement.

## Security and safety requirements

- Gap records are not labeled as spacecraft anomalies unless a detector says so under its own dataset id.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The runbook states how an operator tells live-public data from a benchmark replay.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
