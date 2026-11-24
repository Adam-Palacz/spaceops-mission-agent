# AV4.2 - Model registry, rollback, and drift monitoring

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A detector that cannot be named and removed is not operable, even as a lab service.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The LLM gateway has backend selection. There is no equivalent for a numeric detector.

## Requirements

- Registry entries have model id, dataset id, metric snapshot, and a previous id for rollback.
- Rollback is a configuration change to the previous id, not a retraining.
- Drift is a comparison of recent score or input statistics with the training manifest. It opens an incident or a log, and it does not retrain online.
- No paid model-hosting service.

## Functional and non-functional requirements

- Registry entries have model id, dataset id, metric snapshot, and a previous id for rollback.
- Rollback is a configuration change to the previous id, not a retraining.
- Drift is a comparison of recent score or input statistics with the training manifest. It opens an incident or a log, and it does not retrain online.
- No paid model-hosting service.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Local registry files. Helm value only if a later deployment task needs it.

## Dependencies

- AV4.1

## Implementation checklist

- [ ] Register two synthetic versions and roll back.
- [ ] Fire a drift check on a shifted synthetic input.

## Test requirements

- Rollback changes the id the pipeline loads.
- Drift does not update weights.

## Testing requirements

- Rollback changes the id the pipeline loads.
- Drift does not update weights.

## Security and safety requirements

- Model artifacts are not committed if they contain training rows.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- An operator can see which model id produced an incident and how to select the previous one.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
