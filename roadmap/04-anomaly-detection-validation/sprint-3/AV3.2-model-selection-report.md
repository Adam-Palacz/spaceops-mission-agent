# AV3.2 - Selection against the baseline table

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Keep a learned model only when the pre-registered metric improves on the internal validation fold and the test score is reported once.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Nothing stops a later author from quoting the best test score after several tries. AV1.1 is the control, and this task has to use it.

## Requirements

- One pre-registered comparison on the internal fold.
- The official test partition is scored once for the selected configuration.
- A result that loses to EWMA or isolation forest stays in the table.
- No automatic promotion into the agent.

## Functional and non-functional requirements

- One pre-registered comparison on the internal fold.
- The official test partition is scored once for the selected configuration.
- A result that loses to EWMA or isolation forest stays in the table.
- No automatic promotion into the agent.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- AV1 registry and AV2/AV3 detectors.

## Dependencies

- AV3.1

## Implementation checklist

- [ ] Run the comparison.
- [ ] Write the selection decision, including a decision to keep no learned model.

## Test requirements

- The registry shows a single test evaluation for the chosen configuration.
- A second test evaluation is marked contaminated, not official.

## Testing requirements

- The registry shows a single test evaluation for the chosen configuration.
- A second test evaluation is marked contaminated, not official.

## Security and safety requirements

- The report does not include unpublished ESA mission samples.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- AV4 and AV6 know which checkpoint, if any, is the selected one.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
