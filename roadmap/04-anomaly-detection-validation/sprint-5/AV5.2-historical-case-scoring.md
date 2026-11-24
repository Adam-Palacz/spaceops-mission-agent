# AV5.2 - Score historical cases without using anomaly labels as causes

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A binary anomaly flag does not identify a subsystem fault. Diagnosis claims need the RD4 case files.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- OPSSAT-AD labels mean the segment should notify an operator. They do not name a root cause.

## Requirements

- Run the agent metric suite on RD4 cases that have a known cause, and separately list cases with unknown cause.
- Do not compute root-cause accuracy on OPSSAT-AD or ESA-AD anomaly flags.
- The prediction is stored before the hidden reference is opened.
- Freeze named public, blinded public, and synthetic/perturbed cohorts and case families before model/prompt tuning. Run an identity-only/no-telemetry baseline on named cases to estimate recall of public reports, and a matched no-evidence control on blinded cases. Compare full-evidence and no-evidence runs using the same model, prompt version and scoring rubric. Record model/version, exposure risk, case counts, paired metric deltas and uncertainty; report separate cohort metrics. Public-case recall may reflect memorization; do not claim unseen-event generalization.

## Functional and non-functional requirements

- Run the agent metric suite on RD4 cases that have a known cause, and separately list cases with unknown cause.
- Do not compute root-cause accuracy on OPSSAT-AD or ESA-AD anomaly flags.
- The prediction is stored before the hidden reference is opened.
- Freeze named public, blinded public, and synthetic/perturbed cohorts and case families before model/prompt tuning. Run an identity-only/no-telemetry baseline on named cases to estimate recall of public reports, and a matched no-evidence control on blinded cases. Compare full-evidence and no-evidence runs using the same model, prompt version and scoring rubric. Record model/version, exposure risk, case counts, paired metric deltas and uncertainty; report separate cohort metrics. Public-case recall may reflect memorization; do not claim unseen-event generalization.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- AV5.1 scorer and RD4.3 files.

## Dependencies

- AV5.1
- RD4.3

## Implementation checklist

- [ ] Execute the order: predict, store, then score.
- [ ] Publish counts of known-cause and unknown-cause cases.
- [ ] Execute and report the memorization controls and paired comparisons, including negative results and limitations.

## Test requirements

- Opening the hidden file before the prediction is stored fails the test.
- An OPSSAT-AD label cannot satisfy the root-cause metric.
- An identity-only run receives no telemetry, tools, or ground truth; a blinded no-evidence run has no mission identity or evidence. A transformed case cannot be counted as a real historical case.

## Testing requirements

- Opening the hidden file before the prediction is stored fails the test.
- An OPSSAT-AD label cannot satisfy the root-cause metric.
- An identity-only run receives no telemetry, tools, or ground truth; a blinded no-evidence run has no mission identity or evidence. A transformed case cannot be counted as a real historical case.

## Security and safety requirements

- External LLM calls on real cases remain disabled unless the specific historical public-data exception in the planned egress policy has been implemented, tested and approved. Local-only model runs are otherwise required.

- External model processing is default-deny. For isolated historical public-data experiments only, follow the reviewed minimal egress/redaction control in `roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md`. All other data retains the stricter existing restrictions. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The phase report has an agent table that a reader cannot confuse with the detector table.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
