# RD2.3 - Replay, parameter mapping, and one read-only agent pass

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Prove the current agent can investigate a real recording through the existing tools. Do not score it as a detector and do not let it act.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Replay exists for lab incidents. It has never been pointed at OPS-SAT.
- The agent can call telemetry and KB tools and can propose restricted actions when OPA allows them.

## Requirements

- Replay uses the existing run path and a dataset-scoped time range.
- The run is read-only: GitOps, ticketing, and other write tools are disabled for this pass.
- The report may cite only channels returned by the telemetry tool.
- Visualization is a chart or table of the queried channels, not a new product UI. Phase 05 owns the operator console.

## Functional and non-functional requirements

- Replay uses the existing run path and a dataset-scoped time range.
- The run is read-only: GitOps, ticketing, and other write tools are disabled for this pass.
- The report may cite only channels returned by the telemetry tool.
- Visualization is a chart or table of the queried channels, not a new product UI. Phase 05 owns the operator console.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- `docs/runbooks/replay_workflow.md`, telemetry MCP, and the current graph.
- No new specialist agents.

## Dependencies

- RD2.1. RD2.2 is included only when its license gate is open; otherwise the pass uses OPSSAT-AD alone and says so.

## Implementation checklist

- [ ] Configure a read-only tool profile.
- [ ] Run one recorded pass on the lookalike in CI and, if the file is available locally, one pass on the real dataset.
- [ ] Save a sanitized report excerpt.

## Test requirements

- The read-only profile cannot create a PR, a ticket, or an approval.
- A report that mentions a channel not returned by the tool fails the check.
- Synthetic CI evals are not retargeted at OPS-SAT.

## Testing requirements

- The read-only profile cannot create a PR, a ticket, or an approval.
- A report that mentions a channel not returned by the tool fails the check.
- Synthetic CI evals are not retargeted at OPS-SAT.

## Security and safety requirements

- Real samples stay on the machine that holds the dataset. This pass does not call an external LLM with those samples unless redaction from the deferred NG3 design has been accepted for this use.
- Default the real pass to the existing non-LLM evidence path if redaction is not accepted.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- One stored report shows the dataset id, the channels queried, and zero write-tool calls.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
