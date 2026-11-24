# MC1.1 - Local Yamcs and license gate

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Use Yamcs as the reference mission-control API. Decide the AGPL boundary before the process is required for CI or for a distributed demo.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No Yamcs service, configuration, or license note exists in the repo.

## Requirements

- Document a local, non-production Yamcs and a synthetic or tutorial database.
- Record AGPL-3.0 for the server and LGPL for the API and clients, and whether SpaceOps will shell out, link, or only speak HTTP.
- CI does not download Yamcs and does not fail when it is absent.
- Authentication to Yamcs is configured even for the local instance. Anonymous write routes are not enabled.

## Functional and non-functional requirements

- Document a local, non-production Yamcs and a synthetic or tutorial database.
- Record AGPL-3.0 for the server and LGPL for the API and clients, and whether SpaceOps will shell out, link, or only speak HTTP.
- CI does not download Yamcs and does not fail when it is absent.
- Authentication to Yamcs is configured even for the local instance. Anonymous write routes are not enabled.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- A compose or runbook fragment under `infra/` or `docs/runbooks/`, kept optional.

## Dependencies

- RD1 channel model, so imported parameters land in the registry.

## Implementation checklist

- [ ] Write the license decision.
- [ ] Bring up Yamcs locally and record the version.
- [ ] Leave CI green without it.

## Test requirements

- The runbook's absence path is tested or explicitly manual.
- The license decision names the integration style.

## Testing requirements

- The runbook's absence path is tested or explicitly manual.
- The license decision names the integration style.

## Security and safety requirements

- Do not enable command queues, processors that uplink, or packet links to a real spacecraft.
- Do not commit Yamcs data directories.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reviewer can start the local instance from the runbook or see why it was not started.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
