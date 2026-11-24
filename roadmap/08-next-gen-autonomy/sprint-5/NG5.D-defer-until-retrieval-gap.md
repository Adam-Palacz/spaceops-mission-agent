# NG5.D - Defer GraphRAG until retrieval fails a measured case

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The KB is already vector and document search. A graph is justified by a missed cross-subsystem question, not by the availability of the technique.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- KB MCP and pgvector exist. NG5 specs for a dependency graph, hybrid retrieval, and multi-hop evals are Todo.

## Requirements

- Do not build the graph before AV6 records a retrieval miss that the current KB cannot answer.
- Historical specs stay the design if that miss appears.

## Functional and non-functional requirements

- Do not build the graph before AV6 records a retrieval miss that the current KB cannot answer.
- Historical specs stay the design if that miss appears.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Historical NG5 specs and the current KB.

## Dependencies

- AV6.2

## Implementation checklist

- [ ] Link the historical specs.
- [ ] Leave the KB implementation unchanged.

## Test requirements

- Current KB tests remain the retrieval baseline.

## Testing requirements

- Current KB tests remain the retrieval baseline.

## Security and safety requirements

- A future graph must still cite sources and must not add write tools.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- NG5 is Todo and its entry condition is written down.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
