# NG3.D - Split the minimum redaction rule from the full gateway

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The dangerous gap is sending a real sample to an external model. That rule does not require a new multi-stage gateway.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- NG3.1 through NG3.3 specify policy, scrubber, and masking audit. They are Todo.
- PR2.4 already covers retention and privacy for the lab. It is not a mission-data scrubber.

## Requirements

- RD2.3, AV5 and AV6 use the default-deny historical public-data egress policy; MC3 live data remains local-only absent separate security approval. Fail closed unless the applicable control is implemented and approved.
- Building the full scrubber remains NG3 and stays Todo.
- ITAR or EAR data is not imported under this roadmap.

## Functional and non-functional requirements

- RD2.3, AV5 and AV6 use the default-deny historical public-data egress policy; MC3 live data remains local-only absent separate security approval. Fail closed unless the applicable control is implemented and approved.
- Building the full scrubber remains NG3 and stays Todo.
- ITAR or EAR data is not imported under this roadmap.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Historical NG3 specs, PR2.4 privacy document, and the benchmark tasks that call a model.

## Dependencies

- None for the rule. The full gateway depends on a later decision after real data exists.

## Implementation checklist

- [ ] State the fail-closed rule on the phase 08 board.
- [ ] Do not implement the scrubber in this change.

## Test requirements

- The historical NG3 files remain Todo.
- The data-phase specs name the fail-closed rule.

## Testing requirements

- The historical NG3 files remain Todo.
- The data-phase specs name the fail-closed rule.

## Security and safety requirements

- No task in this restructuring authorizes export-controlled technical data.

- External model processing is default-deny. For isolated historical public-data experiments only, follow the reviewed minimal egress/redaction control in `roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md`. All other data retains the stricter existing restrictions. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reader can see the difference between a default-off external call and a future gateway project.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
