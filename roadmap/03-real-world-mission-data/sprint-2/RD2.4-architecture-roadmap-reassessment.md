# RD2.4 - Architecture and roadmap reassessment

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Pause briefly after the first real-data OPS-SAT pass (`RD2.3`) to review the architectural debt, governance overhead, and strategic alignment captured in [docs/architecture_roadmap_review_2026_11_26.md](../../../docs/architecture_roadmap_review_2026_11_26.md), consult with the project owner, and explicitly redefine, slim down, defer, or add follow-up tasks before investing in `RD3–RD4` and Phase 04 (`AV1–AV6`).

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. Next-gen specifications remain deferred under `roadmap/deprecated-03-next-gen-autonomy/` and `roadmap/08-next-gen-autonomy/`.

Gaps and observations recorded for this reassessment (see [docs/architecture_roadmap_review_2026_11_26.md](../../../docs/architecture_roadmap_review_2026_11_26.md)):

- `apps/api/main.py` exceeds 1,230 lines and mixes ingest, legacy file-dedupe helpers, DLQ, metrics, runs, replay, uploads, and approvals in a single module ahead of `PR4.9` auth changes and Phase 03/05 growth.
- `apps/agent/graph.py` duplicates graph transitions between `build_graph()` (LangGraph) and `_next_after()` inside `_run_with_durable_checkpoint()`.
- Governance and formal sign-off overhead (`PR4` and multi-phase specs) may outweigh domain delivery speed for a solo/small-team lab unless explicitly right-sized.
- Auxiliary narrative docs (such as local/untracked overviews like `docs/project-overview.md`) can drift from `roadmap/MASTER.md` and `docs/book/`.
- Real-data lessons from `RD2.3` (including KB citation coverage and retrieval behavior on OPS-SAT) are not yet fed back into `RD3–RD4`, `PR4`, or `AV1–AV6`.

## Requirements

- Review each observation in [docs/architecture_roadmap_review_2026_11_26.md](../../../docs/architecture_roadmap_review_2026_11_26.md) against concrete findings from `RD2.3` and the current `PR4` state.
- Consult with the project owner on primary positioning (AI Platform/SRE showcase vs. SpaceOps scientific benchmark/publication vs. external pilot) and record explicit dispositions (`keep`, `redefine`, `defer`, `add`, or `drop`).
- For every accepted refactoring or scope change (e.g., splitting `apps/api/main.py`, unifying `apps/agent/graph.py` checkpoint topology, aligning narrative docs, or adjusting `RD3–RD4` / `AV` / `PR4` tasks), either create properly formatted sprint task specs + `BOARD.md` rows or update existing specs with explicit rationale.
- Do not weaken any safety, OPA, approval, ground-truth isolation, or model-egress guardrail while simplifying process overhead.

## Functional and non-functional requirements

- Review each observation in [docs/architecture_roadmap_review_2026_11_26.md](../../../docs/architecture_roadmap_review_2026_11_26.md) against concrete findings from `RD2.3` and the current `PR4` state.
- Consult with the project owner on primary positioning and record explicit dispositions (`keep`, `redefine`, `defer`, `add`, or `drop`) for each review topic.
- Translate every approved decision into concrete sprint specs, board updates, or backlog items rather than leaving decisions only in chat or loose notes.
- Non-functional: preserve roadmap link integrity, pass `tests/test_master_roadmap_structure.py` and `tests/test_production_readiness_pr4_roadmap.py`, keep CI synthetic fixtures unchanged, and make no claim that a reassessment changes production admission.

## Architecture and affected components

- `docs/architecture_roadmap_review_2026_11_26.md` and `docs/README.md` (and disposition of `docs/project-overview.md`).
- Candidate code areas evaluated (not modified by this review task unless split into approved implementation tasks): `apps/api/main.py` and `apps/agent/graph.py`.
- Downstream roadmap specs and boards in `roadmap/02.5-production-readiness/`, `roadmap/03-real-world-mission-data/`, and `roadmap/04-anomaly-detection-validation/` through `roadmap/07-external-validation/`.

## Dependencies

- RD2.3 (wait for the first real OPS-SAT replay and read-only agent pass so decisions are grounded in real-data evidence, not speculation).

## Implementation checklist

- [ ] Review all six topics in [docs/architecture_roadmap_review_2026_11_26.md](../../../docs/architecture_roadmap_review_2026_11_26.md) alongside `RD2.3` evidence and current `PR4` status.
- [ ] Run an owner consultation to agree on primary project positioning and governance vs. delivery balance.
- [ ] Record explicit keep / redefine / defer / add / drop dispositions for each topic (including `apps/api/main.py` modularization, `apps/agent/graph.py` topology unification, `docs/project-overview.md`, and downstream Phase `03–07` / `PR4` tasks).
- [ ] Apply approved task additions or redefinitions to the relevant sprint specs and `BOARD.md` files, and update `roadmap/CHANGELOG.md` if roadmap sequence or phase scope changes.
- [ ] Verify roadmap structure and link-integrity tests pass after any edits.

## Test requirements

- `pytest tests/test_master_roadmap_structure.py tests/test_production_readiness_pr4_roadmap.py` passes after any roadmap/task updates.
- Every newly added or redefined task spec resolves all local markdown links and conforms to the required headings and status rules.
- Existing synthetic CI fixtures and eval tests remain untouched and green.

## Testing requirements

- `pytest tests/test_master_roadmap_structure.py tests/test_production_readiness_pr4_roadmap.py` passes after any roadmap/task updates.
- Every newly added or redefined task spec resolves all local markdown links and conforms to the required headings and status rules.
- Existing synthetic CI fixtures and eval tests remain untouched and green.

## Security and safety requirements

- Simplifying documentation or process overhead must never weaken OPA fail-closed enforcement, approval identity/atomicity controls, mission/ground-truth isolation (`RD1.3`), or `LLM_DATA_POLICY.md` model-egress controls.
- Any decision affecting `PR4` admission gates must preserve the explicit `2026-11-23` No-go verdict until `PR4.7` formally re-reviews evidence or signed waivers.
- External model processing remains default-deny; synthetic CI fixtures remain isolated from historical datasets.

## Acceptance criteria

- Every observation in [docs/architecture_roadmap_review_2026_11_26.md](../../../docs/architecture_roadmap_review_2026_11_26.md) has a recorded disposition with rationale.
- Any approved refactoring or scope change is reflected as concrete, test-validated task specs and board rows (or explicitly deferred with a trigger condition).
- Roadmap structure and link tests pass with zero broken links.

## Required execution evidence

- A sanitized decision note under this sprint's future `evidence/` directory summarizing the consultation date, `RD2.3` inputs reviewed, dispositions per topic, tasks added/redefined/deferred, and test commands run.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until `RD2.3` evidence has been reviewed, the consultation dispositions and any approved roadmap/task updates are recorded, roadmap tests pass, and a sanitized evidence note exists. Writing this specification does not implement any refactoring and does not change the 2026-11-23 No-go decision.
