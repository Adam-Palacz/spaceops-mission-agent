# RD4.3 - Historical cases with hidden reference answers

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Agent reasoning has to be scored against a held-out explanation. If the answer is in the KB, the test measures retrieval of the answer, not diagnosis.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Current semantic evals ship the expected behavior in fixtures the scorer uses. That is appropriate for CI and wrong for a claimed historical diagnosis score.

## Requirements

- A case file has a visible packet (symptoms, time range, dataset id) and a hidden reference (cause, appropriate action, unacceptable action) stored for the scorer only.
- The hidden file is not indexed by KB MCP and is not mounted into the agent run.
- Cases must say whether a root cause is actually known. Unknown cause is an allowed label.
- OPSSAT-AD segment labels are not valid hidden root causes.
- Record public-report exposure risk and evidence availability at the incident cutoff. Freeze separate cohorts: named public reconstructions, blinded/aliased versions (remove nonessential mission names, dates, distinctive wording and source URLs from model-visible inputs), and separately labeled synthetic or physically plausible perturbed cases. Preserve real evidence and provenance in the evaluator. Do not claim blinded public cases are guaranteed unseen by the model.
- Keep post-incident root-cause reports out of the diagnosis retrieval index; keep only material available at the case cutoff. Evaluate answer retrieval separately, if needed.

## Functional and non-functional requirements

- A case file has a visible packet (symptoms, time range, dataset id) and a hidden reference (cause, appropriate action, unacceptable action) stored for the scorer only.
- The hidden file is not indexed by KB MCP and is not mounted into the agent run.
- Cases must say whether a root cause is actually known. Unknown cause is an allowed label.
- OPSSAT-AD segment labels are not valid hidden root causes.
- Record public-report exposure risk and evidence availability at the incident cutoff. Freeze separate cohorts: named public reconstructions, blinded/aliased versions (remove nonessential mission names, dates, distinctive wording and source URLs from model-visible inputs), and separately labeled synthetic or physically plausible perturbed cases. Preserve real evidence and provenance in the evaluator. Do not claim blinded public cases are guaranteed unseen by the model.
- Keep post-incident root-cause reports out of the diagnosis retrieval index; keep only material available at the case cutoff. Evaluate answer retrieval separately, if needed.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Evaluation runner, not the agent graph.
- Separate directory from `evals/fixtures` so CI semantic tests do not load them.

## Dependencies

- RD4.1
- RD1.3

## Implementation checklist

- [ ] Define the split file layout.
- [ ] Test that KB search and the telemetry tool cannot read the hidden file.
- [ ] Include one synthetic case in CI and keep real cases out of git if their text is restricted.
- [ ] Freeze case families/cohort assignments together and audit model-visible packets, KB, tool output and metadata for identifying cues and future evidence.

## Test requirements

- Agent-visible search misses the hidden answer.
- The scorer can read it after the prediction is saved.
- A case with unknown cause does not require a guessed subsystem.
- Blinded packets and retrieval results omit prohibited identifiers and future reports while retaining evidence necessary for the task; transformed cases are identified as such in the scorer.

## Testing requirements

- Agent-visible search misses the hidden answer.
- The scorer can read it after the prediction is saved.
- A case with unknown cause does not require a guessed subsystem.
- Blinded packets and retrieval results omit prohibited identifiers and future reports while retaining evidence necessary for the task; transformed cases are identified as such in the scorer.

## Security and safety requirements

- Hidden files follow the same redaction rule as evidence notes.

- External model processing is default-deny. For isolated historical public-data experiments only, follow the reviewed minimal egress/redaction control in `roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md`. All other data retains the stricter existing restrictions. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- AV5 can score diagnosis only on cases this task marks as having a known cause.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
