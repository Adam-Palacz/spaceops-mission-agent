# Phase: Production Readiness

This phase hardens SpaceOps from a production-like reference into a credible production pilot
baseline. It is a dedicated operations, reliability, security, and release-readiness track between
Production Scale and deep Next-Gen Autonomy.

Source strategy: [`../02.5-production-readiness.md`](../02.5-production-readiness.md).

**Current review:** [No-go - reference/stage only](PHASE_REVIEW.md) (2026-11-23). Planned PR1-PR3
delivery is complete. [PR4](sprint-4/) is the remediation and re-review sprint for the remaining
security, managed-service, and paging admission gates.

---

## Sprint map

| Sprint | Folder | Goal |
|--------|--------|------|
| **PR1** | [sprint-1/](sprint-1/) | Observability, SLOs, stage operating policy, soak/failure tests. |
| **PR2** | [sprint-2/](sprint-2/) | Data durability, secrets rotation, security review, trace/log retention. |
| **PR3** | [sprint-3/](sprint-3/) | Release/incident gates, pilot plan, engineering book, final go/no-go review. |
| **PR4** | [sprint-4/](sprint-4/) | Admission remediation, managed-service drills, live paging, and re-review. |

---

## Autonomy dependency rule

Next-gen execution is deferred by the [master roadmap](../MASTER.md). The 2026-11-23 review
rule is preserved in [deprecated-03-next-gen-autonomy/README.md](../deprecated-03-next-gen-autonomy/README.md):
NG1-NG2 local proof is no longer the next build, and NG3+ production-like promotion stays blocked.
Any later autonomy task that touches a production-like path still inherits this phase's SLO,
audit, release, and security gates. PR4.8 through PR4.12 are additional admission inputs inside
[sprint 4](sprint-4/README.md), not a new phase.

---

## Definition of done for the phase

- All PR1-PR4 boards are Done.
- Production readiness review exists and records go/no-go status.
- Stage/prod promotion runbook references the new gates.
- Residual risks are either accepted with owners or converted to follow-up tasks.
- Next-Gen Autonomy README is updated with the production-readiness dependency.

---

## How to work in this phase

- Prefer PR1 -> PR2 -> PR3 order.
- Treat observability, backup/restore, secrets, and release gates as blocking requirements.
- Keep implementation evidence in docs/runbooks, tests, Helm/GitOps overlays, and sprint reviews.
- Treat generated HTML/PDF/EPUB as derived artifacts; canonical technical truth remains in versioned
  Markdown, ADRs, runbooks, tests, and evidence records.
- Do not mark a task Done with analysis only when the spec requires an executed drill.
