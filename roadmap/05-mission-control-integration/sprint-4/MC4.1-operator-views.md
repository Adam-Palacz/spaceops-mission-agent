# MC4.1 - Mission selection, charts, timeline, and evidence

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The UI already exists for the lab. This task adds the views a mission dataset needs, and no uplink controls.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The Next.js UI covers lab runs and approvals. It has no mission selector or telemetry chart bound to the registry.

## Requirements

- Views: mission select, channel chart, anomaly or incident timeline, correlated channels, evidence list, and historical replay.
- Replay calls the existing run path in the read-only profile.
- No button submits a telecommand or a Yamcs command.

## Functional and non-functional requirements

- Views: mission select, channel chart, anomaly or incident timeline, correlated channels, evidence list, and historical replay.
- Replay calls the existing run path in the read-only profile.
- No button submits a telecommand or a Yamcs command.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing frontend and the read APIs from MC1 and RD1.

## Dependencies

- MC1.2
- RD2.3 or a synthetic mission that uses the same API.

## Implementation checklist

- [ ] Add the views against the synthetic mission first.
- [ ] Verify in the browser that the read-only flow works and that no command control is present.

## Test requirements

- Switching mission does not keep the previous mission's points on the chart.
- The page source or route table has no command endpoint.

## Testing requirements

- Switching mission does not keep the previous mission's points on the chart.
- The page source or route table has no command endpoint.

## Security and safety requirements

- The UI does not display secrets or unpublished samples in a public build.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- An operator can complete one investigation on the synthetic mission and on local Yamcs when it is running.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
