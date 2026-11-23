# Phase: Next-Gen Autonomy (L3–L4)

Extend SpaceOps from **L1/L2** (MVP + production scale) toward **L3 assisted** and **L4 supervised**
autonomy — per [03-next-gen-autonomy.md](../03-next-gen-autonomy.md).

**Entry:** PS6 (minimum) + recommended PS7.1 (stage cloud) for demos in a prod-like environment.
For production-pilot or NG3+ promotion, complete [Production Readiness](../02.5-production-readiness/)
PR4 remediation and receive an explicit Go or Conditional go decision first.
NG1-NG2 may run in parallel when scoped to local or stage-lab proof.

**Current readiness decision (2026-11-23):**
[No-go - reference/stage only](../02.5-production-readiness/PHASE_REVIEW.md). NG1-NG2 may continue
locally or in isolated synthetic stage. NG3 masking research may proceed locally, but NG3+
production-like promotion, real pilot data, NG4, and NG5 remain blocked until a new readiness review
closes or explicitly accepts the listed gates.

**Phase analysis:** [PHASE_ANALYSIS.md](PHASE_ANALYSIS.md).

---

## Autonomy levels (summary)

| Level | What we add |
|-------|-------------|
| **L1/L2 (now)** | Single graph, evidence, OPA, HITL approve/reject, eval gates |
| **L3 (NG1–NG2)** | Flight Director + specialists; collaborative planning |
| **L4 (NG3–NG5)** | Compliance scrubber, edge SLM, GraphRAG multi-hop |

---

## Sprint map

| Sprint | Folder | Theme (vision doc) | Goal |
|--------|--------|-------------------|------|
| **NG1** | [sprint-1/](sprint-1/) | Theme 1 — Multi-agent | Supervisor + 2 specialist agents, merge + audit |
| **NG2** | [sprint-2/](sprint-2/) | Theme 2 — Collaborative HITL | Plan edit, feedback, replan |
| **NG3** | [sprint-3/](sprint-3/) | Theme 3 — Compliance gateway | Redaction before LLM, policy per env |
| **NG4** | [sprint-4/](sprint-4/) | Theme 4 — Edge / air-gap SLM | Offline mode, degraded guarantees |
| **NG5** | [sprint-5/](sprint-5/) | Theme 5 — GraphRAG | Dependency graph + hybrid retrieval + evals |

Estimate: **~2 weeks per sprint**, 3–4 tasks each.

---

## Scope rules

- **OPA and approval** apply to every agent and every write action.
- **Evals** before every merge — new paths need new fixtures (including multi-hop in NG5).
- **Fail-closed** unchanged (goals NF8).
- Do not pull Theme 3–5 into NG1 — ordering reduces “half-L4” risk.

---

## Backlog outside NG

| Item | Where |
|------|--------|
| BL-003 | Closed (compose) — [TRIAGE](../backlog/TRIAGE.md) |
| BL-004 | Closed in PS7.7; live burst remains future resilience work outside NG hard gates |
| BL-005 | PS7.8 (platform ops) — different domain than mission agent |

---

## How to work

- Tasks: `NGx.y-*.md`, status in sprint `BOARD.md`.
- Vision detail: [03-next-gen-autonomy.md](../03-next-gen-autonomy.md) (themes 1–5).
- Project goals: [goals.md](../goals.md).
