# PR4.9 - API authorization and data-isolation gaps

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Approval routes check a verified principal. Ingest and run routes do not. That is a different hole from PR4.1, and mission isolation does not exist yet.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- `Depends(_approval_auth)` protects approval mutations. `POST /ingest` and the run entrypoint do not use it.
- Telemetry rows have no mission id, so two future datasets would share one query surface.

## Requirements

- Document every public route and whether it authenticates.
- Unauthenticated ingest is either restricted to the lab profile or given a fail-closed check. The decision is recorded.
- State the isolation key RD1 will enforce. This task does not implement the mission registry.
- A negative test shows that a caller without the lab credential cannot ingest when the check is enabled.

## Functional and non-functional requirements

- Document every public route and whether it authenticates.
- Unauthenticated ingest is either restricted to the lab profile or given a fail-closed check. The decision is recorded.
- State the isolation key RD1 will enforce. This task does not implement the mission registry.
- A negative test shows that a caller without the lab credential cannot ingest when the check is enabled.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- `apps/api/main.py` and the future RD1 isolation rule.

## Dependencies

- PR4.1's identity decision is input. RD1.3 implements the mission key. This task records the gap and the lab-route decision.

## Implementation checklist

- [ ] Write the route table.
- [ ] Choose the lab-only or authenticated ingest behavior.
- [ ] Add the negative test for the chosen behavior.

## Test requirements

- The route table matches the code.
- Enabling the check rejects a missing credential.

## Testing requirements

- The route table matches the code.
- Enabling the check rejects a missing credential.

## Security and safety requirements

- Do not log bearer tokens while adding the check.
- Do not treat network location as authentication.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- PR4.7 sees a route table and either a test or a waiver.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
