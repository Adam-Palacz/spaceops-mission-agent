# NG1.D - Defer Flight Director until a measured gap exists

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A single agent is the system under test. A second architecture needs a miss that the current one cannot fix.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Historical specs: NG1.1 through NG1.4, all Todo, under `roadmap/deprecated-03-next-gen-autonomy/sprint-1/`.
- An implementation was started locally and removed so it would not change the running graph.

## Requirements

- Do not add a feature flag, specialist node, or audit field for this phase.
- Re-entry is the AV6.2 paragraph that names the failed cases and why a specialist split would address them.
- OPA, approval, and the single-graph evals stay the default.

## Functional and non-functional requirements

- Do not add a feature flag, specialist node, or audit field for this phase.
- Re-entry is the AV6.2 paragraph that names the failed cases and why a specialist split would address them.
- OPA, approval, and the single-graph evals stay the default.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Historical NG1 specs. Current `apps/agent/graph.py`.

## Dependencies

- AV6.2. Until that report exists this task stays Todo and blocked in practice.

## Implementation checklist

- [ ] Link the historical specs from the board.
- [ ] Do not copy their checklists into new code.

## Test requirements

- The running graph's node list stays the single-agent list.
- Historical NG1 files still exist.

## Testing requirements

- The running graph's node list stays the single-agent list.
- Historical NG1 files still exist.

## Security and safety requirements

- No new agent may call a write tool without the current OPA path. This task adds no agent.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reviewer can find both the preserved spec and the reason it is not in the code.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
