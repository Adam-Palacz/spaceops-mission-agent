# EA4.1 - Space-environment feasibility note

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Keep the hardware track honest. Jetson in a lab does not survive or qualify as a flight computer by being fast.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No feasibility note exists. The architecture documents describe ground software.

## Requirements

- Discuss radiation tolerance, thermal constraints, power budget, watchdogs, ECC or memory faults, and redundancy using cited public sources.
- Compare categories with published onboard-computer examples. Do not claim equivalence.
- Separate measured facts from literature.
- The note's last sentence states that this is not flight readiness and not part of the production-admission decision.

## Functional and non-functional requirements

- Discuss radiation tolerance, thermal constraints, power budget, watchdogs, ECC or memory faults, and redundancy using cited public sources.
- Compare categories with published onboard-computer examples. Do not claim equivalence.
- Separate measured facts from literature.
- The note's last sentence states that this is not flight readiness and not part of the production-admission decision.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- A document under `docs/`. No flight software and no hardware design.

## Dependencies

- EA3.1 so measured rows are not confused with literature.

## Implementation checklist

- [ ] Draft the note with citations.
- [ ] Mark every unmeasured claim as literature.

## Test requirements

- A reviewer can find the not-flight-readiness statement.
- No uncited numeric radiation claim.

## Testing requirements

- A reviewer can find the not-flight-readiness statement.
- No uncited numeric radiation claim.

## Security and safety requirements

- Do not describe how to bypass range safety, licensing, or spacecraft command protections.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- Phase 06 can exit with this note and the EA3 table, whether or not Thor was measured.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
