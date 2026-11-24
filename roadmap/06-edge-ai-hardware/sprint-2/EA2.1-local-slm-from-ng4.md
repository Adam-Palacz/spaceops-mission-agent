# EA2.1 - Local SLM using the NG4 specification

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Offline investigation is an edge requirement. The design stays the NG4 documents. The work is not a reason to start the multi-agent phase.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- NG4.1, NG4.2, and NG4.3 are Todo specifications. The gateway has backends, but no local SLM adapter and no degraded-mode guarantee.

## Requirements

- Implement only what NG4 already requires: a local backend, a quantized or small local model, local retrieval, and a degraded-mode description.
- Do not add Flight Director routing in this task.
- Model weights are downloaded under their license and are not committed.

## Functional and non-functional requirements

- Implement only what NG4 already requires: a local backend, a quantized or small local model, local retrieval, and a degraded-mode description.
- Do not add Flight Director routing in this task.
- Model weights are downloaded under their license and are not committed.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- LLM gateway and the NG4 specs. KB retrieval that already runs locally.

## Dependencies

- The NG4 task files. AV5 is useful input and is not a blocker for a local smoke test.

## Implementation checklist

- [ ] Map each NG4 requirement onto this task or mark it out of scope with a reason.
- [ ] Run a local smoke test without a network backend.

## Test requirements

- The smoke test's recorded backend is the local one.
- NG1 files remain unimplemented.

## Testing requirements

- The smoke test's recorded backend is the local one.
- NG1 files remain unimplemented.

## Security and safety requirements

- The local model must not call a cloud endpoint when offline mode is selected.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reader can see which NG4 requirements were moved here and which remain open.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
