# PR4.11 - Verify the engineering-book workflow

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The book pipeline is already implemented and PR3.5 is Done. This task checks that the current workflow still builds. It does not assume the workflow is broken.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- `.github/workflows/engineering-book.yml` and `scripts/book_build.py` exist.
- PR3.5 evidence records a build on 2026-11-23. That is not a fresh result on today's main.

## Requirements

- Re-run the workflow or the same commands it runs, on the current revision.
- If it passes, file that evidence and stop.
- If it fails, fix the pipeline and attach the failure and the rerun. Do not mark PR3.5 undone. The historical Done status stays, and this task carries the repair.
- Public redaction remains part of the run.

## Functional and non-functional requirements

- Re-run the workflow or the same commands it runs, on the current revision.
- If it passes, file that evidence and stop.
- If it fails, fix the pipeline and attach the failure and the rerun. Do not mark PR3.5 undone. The historical Done status stays, and this task carries the repair.
- Public redaction remains part of the run.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- The existing book workflow and tests in `tests/test_production_readiness_pr35_engineering_book.py`.

## Dependencies

- None. This can run in parallel with the rest of PR4.

## Implementation checklist

- [ ] Run the current book checks.
- [ ] Store a sanitized result.
- [ ] Repair only if that run fails.

## Test requirements

- The command and the result are in the evidence note.
- The public edition still has a redaction step.

## Testing requirements

- The command and the result are in the evidence note.
- The public edition still has a redaction step.

## Security and safety requirements

- Build logs must be checked for secrets before they are saved.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- PR4.7 knows whether the book workflow is currently green.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
