# EV5.1 - Product requirements and commercial feasibility

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A business conclusion needs the benchmark and the admission limits. It is allowed to be negative.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The portfolio is a technical review bundle, not a commercial requirements document.

## Requirements

- Inputs are the AV6 report, the admission decision, the license record for each dataset, and the Yamcs license decision.
- The note may recommend staying a research repository.
- EuroHPC or extra compute is mentioned only if AV3 records a capacity gap. It is not a default step.

## Functional and non-functional requirements

- Inputs are the AV6 report, the admission decision, the license record for each dataset, and the Yamcs license decision.
- The note may recommend staying a research repository.
- EuroHPC or extra compute is mentioned only if AV3 records a capacity gap. It is not a default step.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- A document. No billing integration and no new service.

## Dependencies

- AV6.2 for any performance-based claim. The note can still be written earlier if it avoids those claims.

## Implementation checklist

- [ ] Write the decision and the evidence it used.

## Test requirements

- A commercial claim without an input citation fails review.

## Testing requirements

- A commercial claim without an input citation fails review.

## Security and safety requirements

- No customer data and no pricing that implies an existing contract.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The phase review records the product decision separately from the technical exit gates.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
