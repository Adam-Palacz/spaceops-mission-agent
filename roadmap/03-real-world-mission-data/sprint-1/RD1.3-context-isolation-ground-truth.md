# RD1.3 - Mission isolation and ground-truth separation

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Detection labels, rare-event tags, and engineering values solve different problems. Mixing them makes every later benchmark unbelievable.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Nothing in the agent state distinguishes a measurement from an annotation.
- KB documents and telemetry live in different stores, but a future import could still put labels into the same NDJSON stream.

## Requirements

- Telemetry and ground truth are separate records with a shared dataset id and segment or time key.
- Agent tools used at investigation time cannot read ground truth.
- Evaluation tools can read ground truth only after the prediction is stored.
- Isolation key is dataset id plus mission id, not mission name alone. Two products from OPS-SAT stay distinct.

## Functional and non-functional requirements

- Telemetry and ground truth are separate records with a shared dataset id and segment or time key.
- Agent tools used at investigation time cannot read ground truth.
- Evaluation tools can read ground truth only after the prediction is stored.
- Isolation key is dataset id plus mission id, not mission name alone. Two products from OPS-SAT stay distinct.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Telemetry MCP and the future benchmark runner. Not the LangGraph decide prompt.
- Storage may be files or Postgres, but the access rule is the same.

## Dependencies

- RD1.1

## Implementation checklist

- [ ] Specify the ground-truth record and the tool allowlist.
- [ ] Add a negative test that an investigation tool cannot see labels.
- [ ] Document the two OPS-SAT dataset ids that must never share labels.

## Test requirements

- Investigation query returns values and units only.
- A scoring query can join predictions to labels after the run id is closed.
- Cross-dataset queries return empty unless the caller names both ids.

## Testing requirements

- Investigation query returns values and units only.
- A scoring query can join predictions to labels after the run id is closed.
- Cross-dataset queries return empty unless the caller names both ids.

## Security and safety requirements

- Ground truth is untrusted as an operator instruction. It is an evaluation artifact.
- No prompt template may interpolate label fields.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reviewer can show that the agent path and the scorer path use different stores or views.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
