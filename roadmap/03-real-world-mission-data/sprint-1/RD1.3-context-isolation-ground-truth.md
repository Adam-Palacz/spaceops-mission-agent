# RD1.3 - Mission isolation and ground-truth separation

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Owner** | Mission Data / Security |
| **Implements code** | Yes. `apps/mission_data/isolation.py`, `apps/mission_data/egress.py`, `data/mission_registry/egress_approvals.json`, `docs/mission_isolation_egress_rd13.md`, and guards in Telemetry MCP, LLM gateway, backends, reranker, and KB embeddings. |

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
- Specify and enforce the minimum historical-public-data model egress control in [LLM_DATA_POLICY.md](../LLM_DATA_POLICY.md), including default deny, per-version/provider approval, field allowlist, no external embeddings or fallback in local-only mode, and sanitized audit.

## Functional and non-functional requirements

- Telemetry and ground truth are separate records with a shared dataset id and segment or time key.
- Agent tools used at investigation time cannot read ground truth.
- Evaluation tools can read ground truth only after the prediction is stored.
- Isolation key is dataset id plus mission id, not mission name alone. Two products from OPS-SAT stay distinct.
- Specify and enforce the minimum historical-public-data model egress control in [LLM_DATA_POLICY.md](../LLM_DATA_POLICY.md), including default deny, per-version/provider approval, field allowlist, no external embeddings or fallback in local-only mode, and sanitized audit.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Telemetry MCP and the future benchmark runner. Not the LangGraph decide prompt.
- Storage may be files or Postgres, but the access rule is the same.

## Dependencies

- RD1.1

## Implementation checklist

- [x] Specify the ground-truth record and the tool allowlist.
- [x] Add a negative test that an investigation tool cannot see labels.
- [x] Document the two OPS-SAT dataset ids that must never share labels.
- [x] Implement the minimal egress decision and negative tests from the policy before an external historical model call.

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

- External model processing is default-deny. For isolated historical public-data experiments only, follow the reviewed minimal egress/redaction control in `roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md`. All other data retains the stricter existing restrictions. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reviewer can show that the agent path and the scorer path use different stores or views.
- Approved synthetic test requests pass and unapproved requests fail closed; local-only runs cannot reach external model services.

## Required execution evidence

- Sanitized note: [evidence/RD1.3-isolation-egress-2026-11-26.json](evidence/RD1.3-isolation-egress-2026-11-26.json).
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

The checklist, positive/negative isolation and egress tests, documentation (`docs/mission_isolation_egress_rd13.md`), and sanitized evidence note are in place. `RD1.4` reserved metadata keys required no change. This does not change the 2026-11-23 No-go decision.
