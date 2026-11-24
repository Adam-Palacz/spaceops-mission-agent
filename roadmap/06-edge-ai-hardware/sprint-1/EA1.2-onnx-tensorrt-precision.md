# EA1.2 - ONNX and TensorRT precision comparison

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

FP16 or INT8 only counts if the metric change against the FP32 reference is reported.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- There is no ONNX export in the repo.

## Requirements

- Export the selected model to ONNX when a learned model exists. CPU baselines may skip TensorRT and say so.
- Compare FP32, FP16, and INT8 only for precisions the device supports.
- Quality uses the AV1 metric on the same split, not a visual check.

## Functional and non-functional requirements

- Export the selected model to ONNX when a learned model exists. CPU baselines may skip TensorRT and say so.
- Compare FP32, FP16, and INT8 only for precisions the device supports.
- Quality uses the AV1 metric on the same split, not a visual check.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- EA1 runtime and AV1 metrics.

## Dependencies

- EA1.1
- AV1.2

## Implementation checklist

- [ ] Record supported precisions.
- [ ] Score each built artifact or mark it unavailable.

## Test requirements

- A precision without a metric is not called a result.

## Testing requirements

- A precision without a metric is not called a result.

## Security and safety requirements

- Exported files that embed samples stay out of git.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The table has one row per precision that was actually built.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
