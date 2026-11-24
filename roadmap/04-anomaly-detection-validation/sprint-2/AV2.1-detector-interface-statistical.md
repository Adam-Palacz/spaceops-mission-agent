# AV2.1 - Detector interface, thresholds, z-score, and EWMA

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The simplest detectors are part of the result, not a warmup to delete later.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The agent has escalation heuristics for lab text. There is no reusable detector object and no rolling statistic.

## Requirements

- A detector accepts ordered numeric samples and returns scored windows. It does not create incidents and does not call the LLM.
- Static thresholds, rolling z-score, and EWMA are the first three implementations.
- Thresholds are fit on the training partition only.
- Missing samples stay missing. They are not filled with zeros unless the method's card says so.

## Functional and non-functional requirements

- A detector accepts ordered numeric samples and returns scored windows. It does not create incidents and does not call the LLM.
- Static thresholds, rolling z-score, and EWMA are the first three implementations.
- Thresholds are fit on the training partition only.
- Missing samples stay missing. They are not filled with zeros unless the method's card says so.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- New detector package. Incident creation waits for AV4.

## Dependencies

- AV1.1
- AV1.2
- RD1.3

## Implementation checklist

- [ ] Define the interface and the three methods.
- [ ] Test each on a synthetic step change.
- [ ] Show a training-only fit.

## Test requirements

- A step change scores higher than a flat series for the method that claims to see it.
- Fitting does not read the test partition.

## Testing requirements

- A step change scores higher than a flat series for the method that claims to see it.
- Fitting does not read the test partition.

## Security and safety requirements

- Detectors have no network and no write tools.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- AV6 can cite these three rows.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
