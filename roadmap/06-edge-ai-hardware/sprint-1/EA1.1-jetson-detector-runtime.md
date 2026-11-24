# EA1.1 - Jetson runtime for the selected detector

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Put the AV detector on the board that will actually be measured. Do not invent a second model.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No Jetson documentation, device tree, or deploy script exists.

## Requirements

- Target is Jetson Orin Nano when available. If it is not available, the task ends as blocked with the missing hardware named.
- The model is the AV3 selection or, if none was selected, an AV2 model that can run on CPU.
- Streaming input is a replay of a licensed dataset slice or the synthetic fixture. It is not a live spacecraft.

## Functional and non-functional requirements

- Target is Jetson Orin Nano when available. If it is not available, the task ends as blocked with the missing hardware named.
- The model is the AV3 selection or, if none was selected, an AV2 model that can run on CPU.
- Streaming input is a replay of a licensed dataset slice or the synthetic fixture. It is not a live spacecraft.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- AV detector package and a board runbook.

## Dependencies

- AV2.1. AV3 only if a model was selected.

## Implementation checklist

- [ ] Write the runbook, including the absent-hardware exit.
- [ ] Run the detector on the synthetic fixture on the board or on CPU as the fallback evidence.

## Test requirements

- The runtime reports model id and device.
- A missing board does not fail CI.

## Testing requirements

- The runtime reports model id and device.
- A missing board does not fail CI.

## Security and safety requirements

- No spacecraft interface is connected to the board.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The evidence names the device or the blocker.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
