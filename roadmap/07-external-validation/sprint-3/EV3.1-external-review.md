# EV3.1 - External expert review

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Outside comments are the input NG2 would later need. They are not a partnership announcement.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No external review record exists. MC4.2 is the future store for operator feedback.

## Requirements

- Record role, date, scope, and comments. Names stay out of git unless the person asks to be credited.
- Comments do not change benchmark labels.
- Possible communities include operators, universities, and companies. Listing them is not an approach or an agreement.

## Functional and non-functional requirements

- Record role, date, scope, and comments. Names stay out of git unless the person asks to be credited.
- Comments do not change benchmark labels.
- Possible communities include operators, universities, and companies. Listing them is not an approach or an agreement.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- MC4.2 once it exists. Before that, a standalone note is enough.

## Dependencies

- A person willing to review. Not blocked on AV6, but the reviewer must be told what is and is not measured.

## Implementation checklist

- [ ] Prepare the scope statement.
- [ ] File the comments or an explicit not-yet-reviewed waiver.

## Test requirements

- The note does not say a named organization endorsed the system unless a public statement is cited.

## Testing requirements

- The note does not say a named organization endorsed the system unless a public statement is cited.

## Security and safety requirements

- No confidential mission data is sent to a reviewer without a written allowance.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- NG2's entry note can point at this record or at the waiver.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
