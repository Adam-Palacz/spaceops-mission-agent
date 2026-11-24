# EA3.1 - Measurement table for available devices

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Compare CPU, an available GPU, and Jetson on the same detector and the same slice.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No power meter procedure or thermal log exists. An RTX-class GPU may exist on a workstation, but it is not a recorded benchmark.

## Requirements

- Rows are only devices that were measured.
- Columns are latency, throughput, power, energy per inference, memory, the AV1 quality metric, and temperature or throttling when a sensor exists.
- A missing power meter removes the power column for that device. It does not get a guessed wattage.

## Functional and non-functional requirements

- Rows are only devices that were measured.
- Columns are latency, throughput, power, energy per inference, memory, the AV1 quality metric, and temperature or throttling when a sensor exists.
- A missing power meter removes the power column for that device. It does not get a guessed wattage.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- EA1 runtime and AV1 metrics.

## Dependencies

- EA1.2 or EA1.1 if only CPU is available.

## Implementation checklist

- [ ] Write the measurement procedure.
- [ ] Fill the table for the devices at hand.

## Test requirements

- Each filled cell has a command and a device name in the evidence note.

## Testing requirements

- Each filled cell has a command and a device name in the evidence note.

## Security and safety requirements

- Do not publish serial numbers.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The table's empty cells are explicit.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
