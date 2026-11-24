# EA2.2 - Connectivity loss without cloud fallback

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A fallback that quietly uses the cloud is not an offline mode.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Gateway fallback behavior exists for configured backends. It is not a tested air-gap.

## Requirements

- When offline mode is on, a failed local model returns a degraded result or an escalation. It does not open a cloud socket.
- The test blocks outbound model hosts and expects no connection attempt.
- Degraded quality is measured with the AV5 metrics on the synthetic fixture, not asserted in prose.

## Functional and non-functional requirements

- When offline mode is on, a failed local model returns a degraded result or an escalation. It does not open a cloud socket.
- The test blocks outbound model hosts and expects no connection attempt.
- Degraded quality is measured with the AV5 metrics on the synthetic fixture, not asserted in prose.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Gateway configuration and EA2.1 adapter.

## Dependencies

- EA2.1

## Implementation checklist

- [ ] Add the offline switch.
- [ ] Test it with model hosts blocked.

## Test requirements

- The blocked-host test passes only if no cloud attempt is made.

## Testing requirements

- The blocked-host test passes only if no cloud attempt is made.

## Security and safety requirements

- Do not log prompts from a real dataset in the fallback error.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The runbook says what the operator sees when the local model fails.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
