# Architecture and Roadmap Review Notes (2026-11-26)

**Date:** 2026-11-26  
**Status:** Consultation input only — does not alter canonical scope, sprint status, or the `2026-11-23` No-go admission decision.  
**Follow-up task:** [RD2.4 - Architecture and roadmap reassessment](../roadmap/03-real-world-mission-data/sprint-2/RD2.4-architecture-roadmap-reassessment.md)

This note captures an independent review of the repository and roadmap at the transition between `PR4` (paused pending the `2026-11-27` Cloud SQL network hold) and `RD1` (initial `apps/mission_data/` implementation). Revisit these points after `RD2.3` completes the first real OPS-SAT replay and read-only agent pass, to consult on which tasks to keep, slim down, redefine, or add before scaling into `RD3–RD4` and Phase 04 (`AV1–AV6`).

---

## 1. Strengths to preserve

- **Evidence-first discipline:** Explicit No-go verdict in [PHASE_REVIEW.md](../roadmap/02.5-production-readiness/PHASE_REVIEW.md), clear separation of the four meanings of "readiness" in [MASTER.md](../roadmap/MASTER.md), and sanitized JSON drill evidence rather than unverified claims.
- **Safety-by-construction agent boundary:** No shell access, strict MCP tool boundary, fail-closed OPA policy + HITL approvals + atomic Postgres execution claims, citation/escalation guardrails, prompt-injection CI gates, and strict Pydantic v1 contracts (`extra="forbid"` in `apps/contracts/v1.py`).
- **Right strategic pivot (2026-11-24):** Deferring multi-agent L3/L4 autonomy (Phase 08) until the existing single-agent pipeline is validated on cited real mission datasets (Phases 03–04) with strict ground-truth isolation.
- **Clean mission-data boundary (`RD1`):** Pure, network-free adapters and defensive provenance validation in `apps/mission_data/`.

---

## 2. Observations and risks to revisit

### 2.1 Governance overhead vs. domain progress (over-governance risk)

- **Observation:** The repository maintains an extensive governance apparatus (8 roadmap phases, per-task specs, sprint boards, JSON evidence records, structure tests, engineering book, and `PR4` expanding from 7 to 12 tasks including role-based Security/pilot-owner sign-offs).
- **Risk:** In a solo or very small-team lab, formal admission/waiver ceremony can absorb disproportionate effort without improving domain capability or research signal.
- **Consultation question:** Which `PR4` / future phase gates should stay strict hard gates, and which should be closed pragmatically via scoped reference-lab dispositions so focus stays on Phases 03–04?

### 2.2 Platform maturity vs. domain evidence gap

- **Observation:** Infrastructure and security controls (Helm, Argo CD, GKE stage, Cloud SQL HA/PITR drill, ESO/GSM rotation, OTel/Prometheus/Grafana, 12 ADRs) are far ahead of the domain dataset layer, which still exercises only `data/telemetry/telemetry.ndjson`. Stage Scenario A also noted missing KB citation references (`PHASE_REVIEW.md` residual risks).
- **Risk:** Continuing to invest in platform hardening before completing a real-data end-to-end pass delays discovering real telemetry, retrieval, and reasoning gaps.
- **Consultation question:** After `RD2.3`, what real failures or blind spots appeared on OPS-SAT telemetry, and should they reshape `RD3`, `RD4`, or `AV1–AV5`?

### 2.3 API monolith growth (`apps/api/main.py`)

- **Observation:** `apps/api/main.py` has grown past 1,230 lines and mixes health/metrics, NDJSON ingest, legacy file-based event-ID deduplication, NATS/Postgres paths, DLQ inspection, run triggers, replay, fixture upload, and approval routes in a single module.
- **Risk:** Adding mission-scoped isolation (`RD1.3`), API route authorization (`PR4.9`), and Phase 05 mission-control endpoints onto one monolithic module increases regression and auth-bypass risk.
- **Consultation question:** Should we schedule a dedicated refactoring task to split `apps/api/main.py` into FastAPI routers (`ingest`, `runs`, `approvals`, `ops/dlq`) and retire or isolate legacy file-dedupe helpers before or alongside `PR4.9`?

### 2.4 Duplicated agent graph topology (`apps/agent/graph.py`)

- **Observation:** Pipeline topology is currently defined in two places inside `apps/agent/graph.py`:
  1. `build_graph()` using LangGraph `StateGraph` edges.
  2. `_run_with_durable_checkpoint()` using a hand-maintained `_next_after()` state machine loop.
- **Risk:** Any future graph change (e.g., mission-scoped investigation branches, read-only profiles, or post-`AV6` autonomy changes) can silently diverge between non-checkpointed and durable-checkpointed execution paths.
- **Consultation question:** Should we unify both execution paths onto a single topology definition (or native LangGraph Postgres checkpointer) and add a parity test?

### 2.5 Secondary documentation drift

- **Observation:** Auxiliary narrative documents (such as local/untracked drafts like `docs/project-overview.md`, dated `2026-10-09`, still describing the deprecated `03-next-gen-autonomy` sequence and mid-`PR2` status) drift behind canonical roadmap updates (`MASTER.md`, `PHASE_REVIEW.md`, `docs/book/`).
- **Risk:** Conflicting narratives confuse external reviewers and future contributors/agents.
- **Consultation question:** Should any local/auxiliary narrative overviews be refreshed against `MASTER.md`, folded into `docs/book/`, or retired in favor of `docs/portfolio/README.md` and `roadmap/MASTER.md`?

### 2.6 Primary project positioning (showcase vs. SpaceOps benchmark/publication)

- **Observation:** Phases `02.5` (enterprise SRE/production admission), `03–04` (scientific anomaly detection & agent benchmark), `05` (Yamcs/SatNOGS mission control), `06` (Jetson edge AI), and `07` (paper & external pilot) pull in different directions.
- **Consultation question:** After seeing concrete `RD2.3` results, explicitly confirm the primary goal (AI Platform/SRE portfolio showcase vs. SpaceOps scientific benchmark/publication vs. external pilot) and trim, reorder, or redefine downstream tasks in Phases `04–07` accordingly.

---

## 3. Candidate follow-up tasks (proposed, not scheduled)

These items are **not** active tasks yet. Evaluate them during [RD2.4](../roadmap/03-real-world-mission-data/sprint-2/RD2.4-architecture-roadmap-reassessment.md):

1. **Modularize `apps/api/main.py` into domain routers** — split ingest, runs/replay, approvals, and DLQ/metrics into dedicated FastAPI routers with clear auth dependency boundaries (pairs well with `PR4.9`).
2. **Unify `apps/agent/graph.py` topology across checkpointed and non-checkpointed runs** — eliminate the duplicated `_next_after()` transition table or cover topology equivalence with an automated test.
3. **Audit and align narrative docs** — resolve `docs/project-overview.md` and check citation coverage gap noted in Stage Scenario A.
4. **Right-size `PR4` and Phases `04–07` scope** — decide explicit keep / slim / defer / add dispositions based on primary project goal and `RD2.3` findings.
