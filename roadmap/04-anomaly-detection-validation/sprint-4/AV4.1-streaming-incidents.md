# AV4.1 - Windows, incidents, severity, and deduplication

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The agent already investigates incidents. Detection should enter through that door instead of a second agent.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Incidents can be posted to the API. Nothing generates them from a detector window, and nothing deduplicates overlapping windows.

## Requirements

- Sliding windows and late or missing points are explicit.
- An incident payload carries detector name, model id, severity, channel, time range, and dataset id.
- Overlapping windows for the same channel collapse into one open incident.
- The incident triggers the existing agent. The detector does not call OPA or GitOps.

## Functional and non-functional requirements

- Sliding windows and late or missing points are explicit.
- An incident payload carries detector name, model id, severity, channel, time range, and dataset id.
- Overlapping windows for the same channel collapse into one open incident.
- The incident triggers the existing agent. The detector does not call OPA or GitOps.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing incident and agent run path. NATS if the stream already carries the channel.

## Dependencies

- AV2.1. A selected AV3 model is optional input, not a blocker.

## Implementation checklist

- [ ] Define the incident payload.
- [ ] Deduplicate overlapping synthetic windows.
- [ ] Show one agent run started from a detector incident in the read-only profile.

## Test requirements

- Two overlapping windows create one incident.
- The detector process has no GitOps client.

## Testing requirements

- Two overlapping windows create one incident.
- The detector process has no GitOps client.

## Security and safety requirements

- Severity is not itself an authorization to act.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A trace shows detector to incident to agent, with the model id attached.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
