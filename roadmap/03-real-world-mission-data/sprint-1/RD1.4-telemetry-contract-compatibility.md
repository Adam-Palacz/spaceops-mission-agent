# RD1.4 - TelemetryEventV1 compatibility review

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Extend the contract only where the adapter cannot express a required fact in `metadata`. Existing producers must keep working.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- `ContractBase` forbids extra fields, so a new required field would break `tests/test_contracts_v1.py` and the NDJSON fixture.
- Schema export is `scripts/export_contract_schemas.py`.

## Requirements

- Prefer reserved `metadata` keys: `mission_id`, `dataset_id`, `license`, `sample_kind`, `segment_id`.
- If a field is promoted to the model, it is optional and defaults so old events validate.
- Published JSON schema and Alembic comments stay in sync with the decision.
- Do not add anomaly labels to `TelemetryEventV1`.

## Functional and non-functional requirements

- Prefer reserved `metadata` keys: `mission_id`, `dataset_id`, `license`, `sample_kind`, `segment_id`.
- If a field is promoted to the model, it is optional and defaults so old events validate.
- Published JSON schema and Alembic comments stay in sync with the decision.
- Do not add anomaly labels to `TelemetryEventV1`.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- `apps/contracts/v1.py`, contract tests, schema export, and the telemetry table comment if a column is actually required.

## Dependencies

- RD1.1 and RD1.3 decide the keys.

## Implementation checklist

- [ ] Record the compatibility decision.
- [ ] Update tests for both old and new events.
- [ ] Regenerate the schema only if the model changes.

## Test requirements

- The current synthetic NDJSON still validates.
- A provenance-bearing event validates.
- An event with an unexpected top-level field still fails.

## Testing requirements

- The current synthetic NDJSON still validates.
- A provenance-bearing event validates.
- An event with an unexpected top-level field still fails.

## Security and safety requirements

- Do not put license text, URLs with tokens, or file paths into required columns that are logged by default.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- RD2 adapters have one accepted envelope.
- No existing ingest caller needs a migration to keep using synthetic data.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
