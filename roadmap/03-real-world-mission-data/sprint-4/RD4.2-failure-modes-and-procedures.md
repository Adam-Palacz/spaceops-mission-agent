# RD4.2 - Failure modes and public procedures

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Owner** | Unassigned |
| **Implements code** | Yes. One cited battery mode. No procedure text is stored. |

## Objective and rationale

Subsystem failure modes help investigation only when they are tied to a cited source and are not written as commands.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The agent already retrieves runbooks during investigation. Those runbooks describe the lab scenario, not a spacecraft subsystem taxonomy.

## Requirements

- Represent failure mode, affected subsystem, symptoms, and public corrective action as KB fields with citations.
- Corrective actions are text for the operator. They are not `proposed_actions` and they are not OPA allowlist entries.
- If a public source conflicts with another, keep both and record the conflict. Do not merge them into one cause.

## Functional and non-functional requirements

- Represent failure mode, affected subsystem, symptoms, and public corrective action as KB fields with citations.
- Corrective actions are text for the operator. They are not `proposed_actions` and they are not OPA allowlist entries.
- If a public source conflicts with another, keep both and record the conflict. Do not merge them into one cause.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- KB schema and search. Agent prompts stay unchanged in this task.

## Dependencies

- RD4.1

## Implementation checklist

- [x] Add the schema and one cited example, or an explicit empty accepted set.
- [x] Test that a failure-mode record is searchable and carries its citation.

## Test requirements

- Search result includes the source id.
- The record has no tool name such as `change_config` or `restart_service`.

## Testing requirements

- Search result includes the source id.
- The record has no tool name such as `change_config` or `restart_service`.

## Security and safety requirements

- Do not convert a historical action into an executable plan.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- Investigation can retrieve a cited mode without gaining a new write tool.

## Required execution evidence

- Sanitized note: [evidence/RD4.2-failure-modes-2026-11-27.json](evidence/RD4.2-failure-modes-2026-11-27.json).
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

The catalog has one mode, `nasa-llis-2046-battery-protection`. It cites NASA LLIS 2046, repeats that source's public title, and stores no symptoms and no procedure. Conflicting records stay separate. Investigation can search the mode. The search result has no `change_config` or `restart_service` tool. Agent prompts are unchanged. This does not change the 2026-11-23 No-go decision.
