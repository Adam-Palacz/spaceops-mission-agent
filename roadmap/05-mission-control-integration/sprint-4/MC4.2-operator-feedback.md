# MC4.2 - Operator feedback separate from ground truth

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Comments from an operator are useful and biased. They must not silently become the benchmark answer.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Approvals record allow or reject for restricted actions. They are not a general investigation comment.

## Requirements

- Feedback has author role, case id, timestamp, and text.
- It is stored apart from RD4 hidden references and from anomaly labels.
- Using feedback as a label requires a later, explicit dataset version.

## Functional and non-functional requirements

- Feedback has author role, case id, timestamp, and text.
- It is stored apart from RD4 hidden references and from anomaly labels.
- Using feedback as a label requires a later, explicit dataset version.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- A small API and a UI form. Not the approval transaction.

## Dependencies

- MC4.1

## Implementation checklist

- [ ] Store and retrieve a feedback row.
- [ ] Assert the scorer does not read it unless a test opts in.

## Test requirements

- Feedback does not change an OPSSAT-AD label.
- The hidden-reference file is untouched.

## Testing requirements

- Feedback does not change an OPSSAT-AD label.
- The hidden-reference file is untouched.

## Security and safety requirements

- Do not require an operator's personal identity in the repo. A role and a local id are enough.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- EV3 can export comments without contaminating AV scores.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
