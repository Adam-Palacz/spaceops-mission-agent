# Roadmap — SpaceOps Mission Agent Lab

This folder holds the **execution plan**: phases, sprints, and task-level specs. Use it to implement work in order and track status. Canonical high-level sources: [MASTER.md](MASTER.md), [goals.md](goals.md), [01-foundation-mvp.md](01-foundation-mvp.md), [02-production-scale.md](02-production-scale.md), and [02.5-production-readiness.md](02.5-production-readiness.md). The old next-gen vision is the deprecated archive [deprecated-03-next-gen-autonomy.md](deprecated-03-next-gen-autonomy.md).

---

## Structure

| Path | Content |
|------|---------|
| **[01-foundation-mvp/01-core/](01-foundation-mvp/01-core/)** | Phase: core pipeline (Sprint 1 + Sprint 2). Ingest → Report → Act + OPA + approvals. |
| **[01-foundation-mvp/02-hardening/](01-foundation-mvp/02-hardening/)** | Phase 4: docs, runbooks, expanded evals, optional UI. |
| **[0x-publication-roadmap.md](0x-publication-roadmap.md)** | Simplified publication plan (technical + product narrative + OSS visibility), independent from sprint execution. |
| **[02.5-production-readiness.md](02.5-production-readiness.md)** | Strategy for production readiness between Production Scale and deep L3/L4 autonomy. |
| **[02.5-production-readiness/](02.5-production-readiness/)** | Execution: PR1-PR4 sprints; current [phase review](02.5-production-readiness/PHASE_REVIEW.md) is No-go/reference-stage only, with PR4 remediation scheduled. |
| **[deprecated-03-next-gen-autonomy.md](deprecated-03-next-gen-autonomy.md)** | Deprecated historical vision for L3/L4 autonomy. Not phase 03. |
| **[MASTER.md](MASTER.md)** | Current sequence: finish PR4, then mission data and benchmarks. Next-gen is deferred. |
| **[03-real-world-mission-data/](03-real-world-mission-data/)** | Planned historical telemetry and cited incidents. Not started. |
| **[04-anomaly-detection-validation/](04-anomaly-detection-validation/)** | Planned detection and agent-evaluation study. Not started. |
| **[05-mission-control-integration/](05-mission-control-integration/)** | Planned read-only Yamcs and public stream. Not started. |
| **[06-edge-ai-hardware/](06-edge-ai-hardware/)** | Research measurements and offline model. Not flight readiness. |
| **[07-external-validation/](07-external-validation/)** | Paper, review, and a pilot that stays behind admission. |
| **[08-next-gen-autonomy/](08-next-gen-autonomy/)** | Deferred L3/L4 dispositions. Not the next build. |
| **[deprecated-03-next-gen-autonomy/](deprecated-03-next-gen-autonomy/)** | Deprecated historical NG1-NG5 specifications. Formerly numbered 03. |
| **[02-production-scale/](02-production-scale/)** | Post-MVP productionization (PS1–PS7). |
| **[backlog/](backlog/)** | Idea pool + [TRIAGE.md](backlog/TRIAGE.md); schedule into PS/NG sprints. |

Each phase contains **sprint folders** (e.g. `01-foundation-mvp/01-core/sprint-1/`). Inside each sprint:

- **README.md** — Sprint goal, outcomes, and how to work in this folder.
- **BOARD.md** — Status of all tasks (Todo | In progress | Done | Blocked).
- **`Sx.y-short-name.md`** — One file per task: description, requirements, checklist, test requirements.

---

## How to use (implementation)

1. **Pick a task** — Open the sprint’s `BOARD.md`, choose a task in Todo.
2. **Open the task file** — e.g. `sprint-1/S1.1-directory-structure.md`; read Description, Requirements, Checklist.
3. **Implement** — Follow the checklist; run tests from “Test requirements”.
4. **Update BOARD.md** — Set task to In progress, then Done when complete; link PR or commit if useful.
5. **Sprint done** — When all tasks in the sprint BOARD are Done, run “Definition of done” from the sprint README.

---

## Maintenance

| Field | Value |
|-------|--------|
| **Version** | 1.0 |
| **Last updated** | 2026-11-24 |

### Instructions for AI

1. **Task work** — When implementing a task, read the task’s .md file in the sprint folder (e.g. `01-foundation-mvp/01-core/sprint-1/S1.4-fastapi-ingest.md`). Use its Requirements and Checklist; do not invent new scope. After implementation, suggest updating BOARD.md (e.g. task → Done).
2. **Adding tasks** — New tasks go in the right sprint folder. Create a new `Sx.y-name.md` (same format as existing tasks) and add a row to that sprint’s `BOARD.md`. Keep sprint README and BOARD in sync.
3. **Scope** — If the user asks for something that isn’t in a task file, map it to an existing task or propose a new task file and BOARD update. Do not change scope in the canonical roadmap docs without the user’s approval.
4. **Order** — Prefer implementing tasks in sprint order (S1.1 → S1.14, then S2.1 → S2.11); respect dependencies noted in task files.
5. **Backlog** — [backlog/](backlog/) is a list of items (items.md) and spec files (BL-xxx.md). To do something: create a sprint task from the backlog spec; track status in the sprint BOARD, not in the backlog.
