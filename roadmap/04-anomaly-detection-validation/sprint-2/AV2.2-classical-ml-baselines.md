# AV2.2 - Isolation Forest and Local Outlier Factor

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Classical unsupervised models are the ML baseline. They are not a claim that deep models are required.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No scikit-learn detector is wired into the repo. Adding the dependency is part of this task and must go through the existing dependency policy.

## Requirements

- Isolation Forest and Local Outlier Factor use the same interface as AV2.1.
- Hyperparameters are chosen on a training-internal validation fold, never on the official test partition.
- The OPSSAT-AD reported row uses the handcrafted features in `dataset.csv` or the raw segments, and the report says which.
- If the real file is absent, CI runs a synthetic stand-in and the official row is marked not-run.

## Functional and non-functional requirements

- Isolation Forest and Local Outlier Factor use the same interface as AV2.1.
- Hyperparameters are chosen on a training-internal validation fold, never on the official test partition.
- The OPSSAT-AD reported row uses the handcrafted features in `dataset.csv` or the raw segments, and the report says which.
- If the real file is absent, CI runs a synthetic stand-in and the official row is marked not-run.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Detector package plus a pinned dependency.

## Dependencies

- AV2.1

## Implementation checklist

- [ ] Implement both models.
- [ ] Record the feature choice.
- [ ] Produce a metric row through the AV1.2 hook.

## Test requirements

- Synthetic outliers score above the training median.
- The official test partition is not opened during parameter selection.

## Testing requirements

- Synthetic outliers score above the training median.
- The official test partition is not opened during parameter selection.

## Security and safety requirements

- Model files contain no embedded samples from the test partition.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The baseline table has five named methods or an explicit not-run reason.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
