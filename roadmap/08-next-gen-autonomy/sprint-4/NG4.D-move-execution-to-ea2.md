# NG4.D - Move offline SLM execution to EA2

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

One offline-model design should have one execution sprint. EA2 is that sprint.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- NG4.1, NG4.2, and NG4.3 are Todo and describe dual mode, a local adapter, and a degraded runbook.

## Requirements

- EA2.1 maps those requirements. This disposition does not implement them.
- The historical board stays Todo until an EA2 completion updates it. This change does not update it to Done.

## Functional and non-functional requirements

- EA2.1 maps those requirements. This disposition does not implement them.
- The historical board stays Todo until an EA2 completion updates it. This change does not update it to Done.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Historical NG4 specs and EA2.

## Dependencies

- EA2 for implementation. This disposition has no code dependency.

## Implementation checklist

- [ ] Link EA2 from this sprint.
- [ ] Leave the historical status Todo.

## Test requirements

- No second local-adapter design is introduced.

## Testing requirements

- No second local-adapter design is introduced.

## Security and safety requirements

- Offline mode still means no silent cloud fallback, as EA2.2 requires.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A search for the local SLM finds both the historical spec and EA2.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
