# EV4.1 - Bounded read-only pilot gate

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A roadmap phase does not admit a pilot. PR4.7 is the only document that can change No-go.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The 2026-11-23 decision is No-go. PR4.1, PR4.2, PR4.3, PR4.5, and PR4.6 are not Done. PR4.7 is Todo.
- The pilot plan already limits data and authority. Those limits stay.

## Requirements

- This task may not start implementation while the decision is No-go.
- A future pilot is read-only toward the spacecraft and uses the data class the new decision names.
- Go or Conditional go from PR4.7 is a required input, not a product of this task.

## Functional and non-functional requirements

- This task may not start implementation while the decision is No-go.
- A future pilot is read-only toward the spacecraft and uses the data class the new decision names.
- Go or Conditional go from PR4.7 is a required input, not a product of this task.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- PR3.3 pilot plan and PR4.7.

## Dependencies

- PR4.7 decision other than No-go. That dependency is intentionally unsatisfied.

## Implementation checklist

- [ ] Restate the blocker in the sprint board.
- [ ] Do not create pilot credentials, cloud projects, or data shares from this task.

## Test requirements

- The spec remains Todo while the decision line stays No-go.

## Testing requirements

- The spec remains Todo while the decision line stays No-go.

## Security and safety requirements

- No pilot data is copied into the repo under this task.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reader cannot mistake phase 07 for admission.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
