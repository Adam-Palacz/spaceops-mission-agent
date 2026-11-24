# RD3.2 - Annotations, rare nominal events, and telecommand history

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

ESA-AD distinguishes anomalies, rare nominal events, and telecommands. Collapsing them into one positive class copies a shortcut the upstream benchmark code itself calls temporary.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The upstream README notes that algorithms currently treat rare nominal events as anomalies. That is not the SpaceOps metric definition.
- Telecommands are execution timestamps. The published table lists 821 telecommands and zero for Mission3. They are auxiliary inputs, not labels.

## Requirements

- Store anomaly annotations, rare nominal events, and telecommands as different ground-truth or context types.
- Telecommands keep impact or priority only when the source file has it, encoded as data, not as an instruction to the agent.
- Target and non-target channels, and numerical and categorical channels, stay marked as in the source.
- No task in this sprint computes a detection score.

## Functional and non-functional requirements

- Store anomaly annotations, rare nominal events, and telecommands as different ground-truth or context types.
- Telecommands keep impact or priority only when the source file has it, encoded as data, not as an instruction to the agent.
- Target and non-target channels, and numerical and categorical channels, stay marked as in the source.
- No task in this sprint computes a detection score.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- RD1.3 ground-truth store.
- Channel registry extended with the ESA-AD channel groups and subsystems that the files actually contain.

## Dependencies

- RD3.1

## Implementation checklist

- [ ] Map the three annotation kinds on the test slice.
- [ ] Assert rare nominal events are queryable separately from anomalies.
- [ ] Assert Mission3 telecommand count can be zero without failing import.

## Test requirements

- A rare nominal event does not satisfy an anomaly query.
- A telecommand timestamp does not create an anomaly label.
- Categorical channels are not cast into floats without a recorded encoding.

## Testing requirements

- A rare nominal event does not satisfy an anomaly query.
- A telecommand timestamp does not create an anomaly label.
- Categorical channels are not cast into floats without a recorded encoding.

## Security and safety requirements

- Telecommand names are not turned into proposed commands or GitOps edits.
- The agent tool profile from RD2.3 remains unable to read these annotations.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The import report counts anomalies, rare nominal events, and telecommands separately.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
