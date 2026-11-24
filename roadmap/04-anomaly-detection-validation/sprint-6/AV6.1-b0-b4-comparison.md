# AV6.1 - B0 through B4 comparison

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The study exists to learn where the agent adds anything. A loss is a valid result.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The five variants are not implemented as a study. The agent and the lab rules exist separately.

## Requirements

- B0 is rules and thresholds. B1 is the selected classical detector. B2 is a telemetry summary sent to an LLM without MCP or KB. B3 is the current agent with MCP, KB, and policy. B4 is B1 followed by B3.
- Detectors are compared on detection metrics. Agents are compared on AV5 metrics. End-to-end rows use the same scenario list.
- All model variants on real samples use the same eligible data policy and matched model access. Use local models if external approval is absent; if no eligible model is available, report unavailable variants, not synthetic scores as real-data comparisons.

## Functional and non-functional requirements

- B0 is rules and thresholds. B1 is the selected classical detector. B2 is a telemetry summary sent to an LLM without MCP or KB. B3 is the current agent with MCP, KB, and policy. B4 is B1 followed by B3.
- Detectors are compared on detection metrics. Agents are compared on AV5 metrics. End-to-end rows use the same scenario list.
- All model variants on real samples use the same eligible data policy and matched model access. Use local models if external approval is absent; if no eligible model is available, report unavailable variants, not synthetic scores as real-data comparisons.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- AV2 detectors, AV5 scorer, current agent. No new specialist graph.

## Dependencies

- AV2.2
- AV5.2

## Implementation checklist

- [ ] Freeze the scenario list in the registry.
- [ ] Run the five variants once.
- [ ] Write the table, including negative results.

## Test requirements

- Each variant has a registry id.
- Agent comparisons retain the AV5 exposure-control cohorts and matched no-evidence controls; synthetic scores are not compared as if they used the real test set.
- A missing variant is a blank cell with a reason, not an imputed win.

## Testing requirements

- Each variant has a registry id.
- Agent comparisons retain the AV5 exposure-control cohorts and matched no-evidence controls; synthetic scores are not compared as if they used the real test set.
- A missing variant is a blank cell with a reason, not an imputed win.

## Security and safety requirements

- B2 must not become a backdoor that sends unlabeled real telemetry to an external model.

- External model processing is default-deny. For isolated historical public-data experiments only, follow the reviewed minimal egress/redaction control in `roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md`. All other data retains the stricter existing restrictions. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The report can be read without assuming B3 or B4 won.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
