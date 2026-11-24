# AV6.2 - Ablations and limitations

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

If the agent wins, the report still has to say whether KB, MCP, or the model did the work.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- There is no ablation harness that disables KB or MCP and reruns the same case.

## Requirements

- Ablations: no KB, no telemetry MCP, no extra case context, and at least two LLM backends already supported by the gateway when credentials exist.
- A backend that is not configured is skipped, not failed closed into a fake score.
- Limitations must include the non-chronological OPSSAT-AD split, anonymized ESA missions, and the lack of a command-authority evaluation.
- The recommendation for phase 08 is a paragraph in this report, not a code change.

## Functional and non-functional requirements

- Ablations: no KB, no telemetry MCP, no extra case context, and at least two LLM backends already supported by the gateway when credentials exist.
- A backend that is not configured is skipped, not failed closed into a fake score.
- Limitations must include the non-chronological OPSSAT-AD split, anonymized ESA missions, and the lack of a command-authority evaluation.
- The recommendation for phase 08 is a paragraph in this report, not a code change.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Eval runner flags. Gateway backend selection already exists.

## Dependencies

- AV6.1

## Implementation checklist

- [ ] Add the ablation flags.
- [ ] Write the limitations section.
- [ ] State whether NG1 is justified by a measured cross-subsystem miss.

## Test requirements

- Disabling KB changes the recorded tool list.
- The limitations section exists even when every ablation is inconclusive.

## Testing requirements

- Disabling KB changes the recorded tool list.
- The limitations section exists even when every ablation is inconclusive.

## Security and safety requirements

- Do not add a backend credential to the report.

- External model processing is default-deny. For isolated historical public-data experiments only, follow the reviewed minimal egress/redaction control in `roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md`. All other data retains the stricter existing restrictions. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Exposure and generalization limitations

Report AV5 identity-only and blinded no-evidence controls and full-evidence deltas by cohort. State that pretrained-model exposure cannot be ruled out on public historical reports. Distinguish answer retrieval, historical reconstruction and evidence-grounded reasoning. Do not infer generalization from public-report scores alone.

## Acceptance criteria

- Phase 08's entry gate can point at this paragraph.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
