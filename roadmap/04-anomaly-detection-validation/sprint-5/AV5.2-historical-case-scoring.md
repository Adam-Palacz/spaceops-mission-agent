# AV5.2 - Score historical cases without using anomaly labels as causes

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A binary anomaly flag does not identify a subsystem fault. Diagnosis claims need the RD4 case files.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- OPSSAT-AD labels mean the segment should notify an operator. They do not name a root cause.

## Requirements

- Run the agent metric suite on RD4 cases that have a known cause, and separately list cases with unknown cause.
- Do not compute root-cause accuracy on OPSSAT-AD or ESA-AD anomaly flags.
- The prediction is stored before the hidden reference is opened.

## Functional and non-functional requirements

- Run the agent metric suite on RD4 cases that have a known cause, and separately list cases with unknown cause.
- Do not compute root-cause accuracy on OPSSAT-AD or ESA-AD anomaly flags.
- The prediction is stored before the hidden reference is opened.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- AV5.1 scorer and RD4.3 files.

## Dependencies

- AV5.1
- RD4.3

## Implementation checklist

- [ ] Execute the order: predict, store, then score.
- [ ] Publish counts of known-cause and unknown-cause cases.

## Test requirements

- Opening the hidden file before the prediction is stored fails the test.
- An OPSSAT-AD label cannot satisfy the root-cause metric.

## Testing requirements

- Opening the hidden file before the prediction is stored fails the test.
- An OPSSAT-AD label cannot satisfy the root-cause metric.

## Security and safety requirements

- External LLM calls on real cases remain disabled unless a reviewed redaction control exists.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The phase report has an agent table that a reader cannot confuse with the detector table.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
