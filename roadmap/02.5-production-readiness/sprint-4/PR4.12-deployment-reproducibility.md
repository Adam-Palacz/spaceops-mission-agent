# PR4.12 - Deployment reproducibility from a clean checkout

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Helm, Terraform, and compose exist. A new machine cannot yet follow one documented path that names every required input and the expected health check.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Deploy docs are split across compose, kind, Helm, and GCP stage runbooks.
- Stage GCP is ephemeral by policy. A reproducibility drill must not leave a billable resource behind.

## Requirements

- One runbook path from a clean checkout to a local healthy `/health`, using compose or kind. Pick one and name the inputs.
- A second, optional stage path lists required credentials without containing them, and it ends in teardown.
- The drill records the tool versions and the commit.
- A step that depends on an uncommitted secret fails with a named missing input.

## Functional and non-functional requirements

- One runbook path from a clean checkout to a local healthy `/health`, using compose or kind. Pick one and name the inputs.
- A second, optional stage path lists required credentials without containing them, and it ends in teardown.
- The drill records the tool versions and the commit.
- A step that depends on an uncommitted secret fails with a named missing input.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing compose, Helm chart, and stage runbooks.

## Dependencies

- None for the local path. The stage path stays optional and cost-capped.

## Implementation checklist

- [ ] Write or consolidate the local path.
- [ ] Run it from the documented start state.
- [ ] Tear down anything the run started.

## Test requirements

- A second run on the same commit reaches `/health`.
- A missing documented input fails closed.

## Testing requirements

- A second run on the same commit reaches `/health`.
- A missing documented input fails closed.

## Security and safety requirements

- No cloud project id, token, or password in the evidence.
- Do not create a long-lived cluster or database for this drill.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- PR4.7 can cite the local drill and either a stage drill or a waiver.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
