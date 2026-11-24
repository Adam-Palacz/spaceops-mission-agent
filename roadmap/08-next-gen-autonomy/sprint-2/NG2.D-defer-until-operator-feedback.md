# NG2.D - Defer collaborative planning until operator feedback exists

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Approve and reject are already implemented. Richer planning is a response to a recorded operator limit.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Approvals and the UI exist. NG2.1 through NG2.4 are Todo and describe plan edit, feedback schema, replan, and UI.

## Requirements

- Do not add a replan node before EV3 or MC4.2 records a case the current approval cannot represent.
- The historical specs stay authoritative.

## Functional and non-functional requirements

- Do not add a replan node before EV3 or MC4.2 records a case the current approval cannot represent.
- The historical specs stay authoritative.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Historical NG2 specs and the current approval API.

## Dependencies

- EV3.1 or MC4.2.

## Implementation checklist

- [ ] Point the board at the historical files.
- [ ] Leave the approval transaction unchanged.

## Test requirements

- Approval tests still describe the current behavior.
- No replan module is added by this restructuring.

## Testing requirements

- Approval tests still describe the current behavior.
- No replan module is added by this restructuring.

## Security and safety requirements

- A future replan must remain behind OPA. That rule is already in the historical spec.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- NG2 is still Todo after this roadmap change.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
