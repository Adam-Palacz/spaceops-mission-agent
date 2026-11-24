# AV3.1 - Representative autoencoder and sequence models

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Train a few published model families on the training partition. Do not build a model zoo.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- There is no training loop, checkpoint format, or ONNX export.

## Requirements

- Candidates are an autoencoder, an LSTM autoencoder, and one temporal CNN or a small transformer. The selection note may drop any of them before implementation.
- Multivariate input is allowed only for datasets that actually have aligned channels. OPSSAT-AD segments are univariate and stay univariate.
- Cross-channel correlation is a separate, named experiment, not an implied feature of every model.
- Training reads the training partition and the internal validation fold only.

## Functional and non-functional requirements

- Candidates are an autoencoder, an LSTM autoencoder, and one temporal CNN or a small transformer. The selection note may drop any of them before implementation.
- Multivariate input is allowed only for datasets that actually have aligned channels. OPSSAT-AD segments are univariate and stay univariate.
- Cross-channel correlation is a separate, named experiment, not an implied feature of every model.
- Training reads the training partition and the internal validation fold only.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Detector interface from AV2. Checkpoints outside git.

## Dependencies

- AV2.2 and a baseline table that shows what the classical methods miss.

## Implementation checklist

- [ ] Write the selection note before adding a framework.
- [ ] Train only the selected candidates.
- [ ] Export one ONNX file if EA1 will need it. Otherwise skip export.

## Test requirements

- A selected model loads and scores a synthetic window.
- An unselected architecture has no code path.

## Testing requirements

- A selected model loads and scores a synthetic window.
- An unselected architecture has no code path.

## Security and safety requirements

- Training stays local. No telemetry upload to a hosted training service.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The report lists the rejected architectures and the reason.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
