# EV1.1 - Paper draft bound to the benchmark registry

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Publication is how the measurement leaves the repo. It cannot invent a result the registry does not have.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- There is no paper directory. The engineering book is a system narrative, not a benchmark paper.

## Requirements

- Every number cites an AV1 registry id.
- If AV6 is unfinished, the only allowed draft is a methods note with no performance claim.
- Limitations are copied from AV6.2, not softened.
- Dataset citations include OPSSAT-AD, ESA-AD, and any other set that was actually used.

## Functional and non-functional requirements

- Every number cites an AV1 registry id.
- If AV6 is unfinished, the only allowed draft is a methods note with no performance claim.
- Limitations are copied from AV6.2, not softened.
- Dataset citations include OPSSAT-AD, ESA-AD, and any other set that was actually used.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- A document under `docs/` or a paper folder. Not a change to the agent.

## Dependencies

- AV6.2 for a results paper. No dependency for a methods note that states it has no results.

## Implementation checklist

- [ ] Draft the note.
- [ ] Cross-check every number against the registry.

## Test requirements

- A number without a registry id fails the checklist.

## Testing requirements

- A number without a registry id fails the checklist.

## Security and safety requirements

- No unpublished mission sample and no credential in the draft.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reader can tell whether the draft reports results or only a method.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
