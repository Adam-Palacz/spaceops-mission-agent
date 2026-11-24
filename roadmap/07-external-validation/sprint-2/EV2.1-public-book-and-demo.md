# EV2.1 - Public book and demo update

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The book pipeline exists. This task refreshes its claims after the roadmap change and after any real benchmark.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- PR3.5 and `scripts/book_build.py` already build private and public editions. The public build redacts.
- The portfolio still describes a lab on synthetic data, which remains accurate until a benchmark is in the book.

## Requirements

- Update the book only with claims the master roadmap marks as done or with an explicit planned label.
- A public demo uses synthetic data unless the dataset license allows the clip.
- Rebuild private and public artifacts and keep the redaction scan.

## Functional and non-functional requirements

- Update the book only with claims the master roadmap marks as done or with an explicit planned label.
- A public demo uses synthetic data unless the dataset license allows the clip.
- Rebuild private and public artifacts and keep the redaction scan.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing book pipeline and portfolio.

## Dependencies

- PR4.11 verifies the current workflow. AV6 is required only for result chapters.

## Implementation checklist

- [ ] List the claims to add.
- [ ] Rebuild both editions.

## Test requirements

- The public edition's redaction scan still passes.
- A planned phase is not described as shipped.

## Testing requirements

- The public edition's redaction scan still passes.
- A planned phase is not described as shipped.

## Security and safety requirements

- The public edition follows the existing redaction rules.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The release notes distinguish lab capability from benchmark results.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
