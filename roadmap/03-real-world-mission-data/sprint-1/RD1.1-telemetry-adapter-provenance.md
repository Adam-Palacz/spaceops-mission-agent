# RD1.1 - Source-agnostic telemetry adapter and provenance

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Owner** | Unassigned |
| **Implements code** | Yes. `apps/mission_data/` maps a fixture row. Ingest is unchanged. |

## Objective and rationale

Define the only supported way to turn an external file into `TelemetryEventV1`, so later datasets cannot invent their own schema.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Ingest accepts any NDJSON that validates. It does not record dataset version, license, or split membership.
- Legacy normalization in `apps/api/main.py` fills missing `event_id` values. That is a fixture convenience, not a provenance model.

## Requirements

- One adapter protocol: raw record in, zero or more `TelemetryEventV1` out, plus a provenance record.
- Provenance includes dataset id, version or checksum, license SPDX id, source URL, and `real` or `synthetic`.
- Adapters are pure and side-effect free. Download and license acceptance stay outside the adapter.
- Reject records that do not map to a registered channel.

## Functional and non-functional requirements

- One adapter protocol: raw record in, zero or more `TelemetryEventV1` out, plus a provenance record.
- Provenance includes dataset id, version or checksum, license SPDX id, source URL, and `real` or `synthetic`.
- Adapters are pure and side-effect free. Download and license acceptance stay outside the adapter.
- Reject records that do not map to a registered channel.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- `apps/contracts/v1.py` only if a compatible optional field is required. Prefer `metadata` keys first.
- New adapter package. Do not special-case OPS-SAT inside `apps/api/main.py`.
- Existing NATS subject and Postgres `telemetry_events` table stay the transport and store.

## Dependencies

- None. This sprint blocks RD2 and RD3.

## Implementation checklist

- [x] Write the provenance schema and the adapter protocol.
- [x] Map one synthetic fixture row through the adapter without changing `telemetry.ndjson`.
- [x] Document which `metadata` keys are reserved.

## Test requirements

- A synthetic row round-trips to the same channel, value, unit, and timestamp.
- A row without a license or dataset id is rejected.
- Existing contract tests still pass.

## Testing requirements

- A synthetic row round-trips to the same channel, value, unit, and timestamp.
- A row without a license or dataset id is rejected.
- Existing contract tests still pass.

## Security and safety requirements

- Provenance must not include credentials or local absolute paths.
- An adapter must not fetch the network.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A second dataset can be added by a new adapter without editing the ingest handler.
- CI still uses only the synthetic fixture.

## Required execution evidence

- Sanitized note: [evidence/RD1-adapter-registry-2026-11-24.json](evidence/RD1-adapter-registry-2026-11-24.json).
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

The checklist, tests, and sanitized evidence note are in place. This does not change the 2026-11-23 No-go decision.
