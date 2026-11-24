# AV1.2 - Official metrics and baseline hook

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Pick the published metrics first so model authors cannot invent a flattering score after seeing results.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Lab behavior metrics cover escalation and evidence coverage. They are not the OPSSAT-AD seven-metric set or the ESA-ADB operational metrics.

## Requirements

- Implement the metric functions against the papers, with citations in the module docstring.
- OPSSAT-AD metrics are computed on the 529-segment test partition only.
- ESA-ADB metrics are reported twice when relevant: the upstream rare-nominal-as-anomaly convention, and SpaceOps' separated convention.
- MLflow is optional local tracking. If it is not installed, the registry file from AV1.1 is the record. Do not require a tracking server.

## Functional and non-functional requirements

- Implement the metric functions against the papers, with citations in the module docstring.
- OPSSAT-AD metrics are computed on the 529-segment test partition only.
- ESA-ADB metrics are reported twice when relevant: the upstream rare-nominal-as-anomaly convention, and SpaceOps' separated convention.
- MLflow is optional local tracking. If it is not installed, the registry file from AV1.1 is the record. Do not require a tracking server.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- A small `evals` or `benchmarks` package imported by tests. Not the agent graph.

## Dependencies

- AV1.1

## Implementation checklist

- [ ] Name the metrics and their citations.
- [ ] Test them on a hand-computed toy confusion pattern.
- [ ] Document the baseline hook the later detectors must call.

## Test requirements

- Toy expected values match the test.
- A detector result without a metric name is rejected.

## Testing requirements

- Toy expected values match the test.
- A detector result without a metric name is rejected.

## Security and safety requirements

- Metric code does not log sample values.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- AV2, AV3, and AV6 call this hook rather than private score formulas.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
