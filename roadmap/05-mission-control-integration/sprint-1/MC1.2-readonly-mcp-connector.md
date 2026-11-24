# MC1.2 - Read-only Parameter Archive, alarms, and MDB connector

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Expose Yamcs history to the existing agent tools without adding a method that can change the spacecraft or the Yamcs command stack.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Telemetry MCP reads lab files or Postgres. It has no Yamcs client.
- Yamcs exposes command APIs. Those routes must not be wrapped.

## Requirements

- Read Parameter Archive values, alarm history, and mission-database or XTCE parameter definitions.
- Map them into `TelemetryEventV1` and the channel registry through the RD1 adapter.
- The client allowlist is GET-only and has no command, queue, or processor-control URL.
- Alarm text is evidence, not an authorization.

## Functional and non-functional requirements

- Read Parameter Archive values, alarm history, and mission-database or XTCE parameter definitions.
- Map them into `TelemetryEventV1` and the channel registry through the RD1 adapter.
- The client allowlist is GET-only and has no command, queue, or processor-control URL.
- Alarm text is evidence, not an authorization.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Telemetry MCP or a sibling read-only MCP. OPA remains on write tools the agent already has.

## Dependencies

- MC1.1
- RD1.1

## Implementation checklist

- [ ] Implement the three read methods against the local instance.
- [ ] Add a test that command URL patterns are absent from the client.
- [ ] Map one tutorial parameter into a telemetry event.

## Test requirements

- A parameter sample keeps its Yamcs name, unit, and generation time.
- The client module has no command route.

## Testing requirements

- A parameter sample keeps its Yamcs name, unit, and generation time.
- The client module has no command route.

## Security and safety requirements

- Credentials for Yamcs stay in the environment, not in git.
- The connector runs with a read-only Yamcs user when the local setup supports one.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- An investigation can cite a Yamcs parameter that the connector returned, and it cannot uplink.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
