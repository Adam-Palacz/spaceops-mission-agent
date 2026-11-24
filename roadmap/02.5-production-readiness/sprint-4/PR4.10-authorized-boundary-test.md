# PR4.10 - Authorized test of the principal trust boundaries

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A focused test of the boundaries the threat model already names. This is not a request to build an exploit, and it is not done until the tester and the rules are named.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- PR2.3 reviewed OPA, approvals, MCP, audit, and the gateway. PR4.1 through PR4.3 add evidence for some of those boundaries and leave acceptance open.
- No authorized boundary-test report exists.

## Requirements

- Scope is the documented boundaries: ingest, approval identity, OPA fail-closed behavior, MCP tool allowlist, and audit integrity.
- The tester, the environment, and the stop conditions are written down before any test.
- Findings get the same owner and expiry shape as PR2.3. A finding is not a public exploit procedure.
- Production and any real mission dataset are out of scope.

## Functional and non-functional requirements

- Scope is the documented boundaries: ingest, approval identity, OPA fail-closed behavior, MCP tool allowlist, and audit integrity.
- The tester, the environment, and the stop conditions are written down before any test.
- Findings get the same owner and expiry shape as PR2.3. A finding is not a public exploit procedure.
- Production and any real mission dataset are out of scope.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing threat model and the PR4.1-PR4.3 controls.

## Dependencies

- A named tester. PR4.1's negative auth tests are a starting point, not a substitute.

## Implementation checklist

- [ ] Write the scope and the stop conditions.
- [ ] Execute only inside that scope, in the lab.
- [ ] File sanitized findings.

## Test requirements

- Each finding maps to a boundary in the scope.
- The report contains no exploit steps, credentials, or payloads.

## Testing requirements

- Each finding maps to a boundary in the scope.
- The report contains no exploit steps, credentials, or payloads.

## Security and safety requirements

- Stop if the test would touch a system outside the lab or a real spacecraft path.
- Do not store stolen credentials, because the test must not take any.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- PR4.7 can cite the report or a waiver with an owner and an expiry.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
