# MC2.2 - Command history and public orbital context

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Commands and orbit events explain telemetry. They are context, not a capability to command.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- ESA-AD telecommands and the re-entry derived orbit fields are dataset-specific. There is no shared context object.

## Requirements

- Command history from Yamcs or a dataset is stored as timestamped context with the same read-only rule as RD3.2.
- Contact windows, eclipse events, and TLE-derived positions are attached only when the source is public and licensed.
- TLE propagation, if implemented, cites the propagator and the element set. It is not a flight dynamics product.

## Functional and non-functional requirements

- Command history from Yamcs or a dataset is stored as timestamped context with the same read-only rule as RD3.2.
- Contact windows, eclipse events, and TLE-derived positions are attached only when the source is public and licensed.
- TLE propagation, if implemented, cites the propagator and the element set. It is not a flight dynamics product.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Context store beside ground truth, visible to investigation as context, not as a command tool.

## Dependencies

- MC2.1

## Implementation checklist

- [ ] Define the context record.
- [ ] Test that a command-history row has no execute method.
- [ ] Attach one public TLE example or skip with a license note.

## Test requirements

- The agent can read the context record.
- No function in the module opens a socket to a spacecraft.

## Testing requirements

- The agent can read the context record.
- No function in the module opens a socket to a spacecraft.

## Security and safety requirements

- Public TLEs are not authorization to task a satellite.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A report can distinguish a measurement, a command-history row, and a derived orbit point.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
