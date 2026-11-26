# SpaceOps Mission Agent Lab — Docs & diagrams

This file is the **index and entry point** for documentation in `docs/`. Mermaid diagrams are stored as **.mmd** files in subfolders by domain. Use a Mermaid-compatible viewer (VS Code Mermaid extension, GitHub/GitLab, [Mermaid Live](https://mermaid.live)) to render them.

**Repository:** [README](../README.md) · [portfolio/README.md](portfolio/README.md) (PS6.10) · [roadmap/MASTER.md](../roadmap/MASTER.md) · [roadmap/goals.md](../roadmap/goals.md) · [roadmap/01-foundation-mvp.md](../roadmap/01-foundation-mvp.md) · [roadmap/02-production-scale.md](../roadmap/02-production-scale.md) · [roadmap/README.md](../roadmap/README.md)

---

## Role of `docs/` in the project

The **docs/** directory holds project documentation that supports both humans and AI tooling:

- **README.md** (this file) — Index of Mermaid diagrams; start here when looking for a flow, architecture, or schema.
- **shadow_models.md** — Shadow-testing and model promotion gate (P4.8): when to run, how to read reports, who decides.
- **output_schema.md** — Strict agent output envelopes (`AgentReportV1`, fail-closed `output_schema_violation`, PS4.2).
- **prompt_injection_threat_model.md** — Untrusted input threats, guards, audit codes (PS4.3).
- **behavior_metrics.md** — Escalation rate, evidence coverage, stage latency metrics (PS4.6).
- **[monitoring-production-analysis.md](monitoring-production-analysis.md)** — Production readiness of Postgres, OTel, Jaeger, Prometheus/Grafana (PS7.4 / BL-001).
- **[slo-production-readiness.md](slo-production-readiness.md)** — PR1.2 SLO catalog, alert routing, and synthetic alert drill.
- **[runbooks/stage_operating_policy.md](runbooks/stage_operating_policy.md)** — PR1.3 stage policy: ephemeral-by-default GKE, ownership, cost guardrails, RTO, secrets, and drift checks.
- **[runbooks/stage_soak_load_failure.md](runbooks/stage_soak_load_failure.md)** — PR1.4 soak/load/failure profiles, thresholds, dry-run automation, and live evidence requirements.
- **[runbooks/postgres_backup_restore.md](runbooks/postgres_backup_restore.md)** - PR2.1 Postgres production-pilot HA posture, backup policy, restore drill, integrity checks, and RTO/RPO evidence.
- **[runbooks/secrets_rotation_pr22.md](runbooks/secrets_rotation_pr22.md)** — PR2.2 secret inventory, local ESO rotation proof, controlled ESO/GSM live procedure, leak checks, and rollback.
- **[security_control_review_pr23.md](security_control_review_pr23.md)** — PR2.3 focused review of OPA, approvals, MCP, audit, platform ops, and LLM gateway controls.
- **[data_retention_privacy_pr24.md](data_retention_privacy_pr24.md)** — PR2.4 retention, classification, redaction, managed trace/log backend, export, and deletion policy.
- **[runbooks/release_promotion_gate_pr31.md](runbooks/release_promotion_gate_pr31.md)** — PR3.1 blocking CI/stage promotion gate, release evidence, failure behavior, and rollback snapshots.
- **[runbooks/incident_oncall_game_day_pr32.md](runbooks/incident_oncall_game_day_pr32.md)** — PR3.2 incident classes, on-call roles, escalation, communication templates, and game-day drill.
- **[production_pilot_plan_pr33.md](production_pilot_plan_pr33.md)** — PR3.3 bounded production-pilot charter, owners, integrations, safety limits, success metrics, and exit criteria.
- **[book/README.md](book/README.md)** — PR3.5 English engineering-book source, private/public editions, redaction, screenshots, and HTML/PDF/EPUB build commands.
- **[approval_identity_authorization_pr41.md](approval_identity_authorization_pr41.md)** — PR4.1 OIDC/JWKS approval identity, approver-role enforcement, threat model, and drill evidence.
- **[approval_atomic_execution_pr42.md](approval_atomic_execution_pr42.md)** — PR4.2 Postgres approval state, transactional claims, downstream idempotency, and concurrency drill.
- **[audit_mcp_trust_pr43.md](audit_mcp_trust_pr43.md)** — PR4.3 signed audit chain, Istio MCP workload identity, and platform write-boundary disposition.
- **[managed_observability_pr44.md](managed_observability_pr44.md)** — PR4.4 Cloud Logging/Trace IaC, access-denial proof, retention, deletion semantics, and live drill evidence.
- **[managed_postgres_ha_pitr_pr45.md](managed_postgres_ha_pitr_pr45.md)** — PR4.5 Cloud SQL regional failover, PITR boundary, IAM denial, cost guardrails, and teardown evidence.
- **[live_paging_pr46.md](live_paging_pr46.md)** — PR4.6 PagerDuty delivery, acknowledgement, resolution, and the remaining escalation and key-revocation gaps.
- **[architecture_roadmap_review_2026_11_26.md](architecture_roadmap_review_2026_11_26.md)** — Architecture and roadmap review notes (2026-11-26): governance vs. domain balance, API/graph refactoring candidates, and strategic alignment checkpoint scheduled in `RD2.4`.
- **Folder READMEs** — Each major repo folder (`data/`, `kb/`, `evals/`, `infra/`, `apps/`, `roadmap/`, …) has a short `README.md` for onboarding (PS7.5 / BL-002).
- **[runbooks/ci_gating_policy.md](runbooks/ci_gating_policy.md)** — Hard vs soft CI gates, OPA/HITL criteria, recovery (PS4.7).
- **[runbooks/guardrails_quality_triage.md](runbooks/guardrails_quality_triage.md)** — Failed-gate triage, decision tree, PS4 symptom → action (PS4.8).
- **[evals_llm_judge_hooks.md](evals_llm_judge_hooks.md)** — Optional future LLM-as-judge eval hooks (PS4.4, non-blocking).
- **[llm_gateway.md](llm_gateway.md)** — LLM gateway contract, backend metadata, and `LLM_BACKEND` routing (PS1.6 / PS5).
- **[llm_gpu_backend.md](llm_gpu_backend.md)** — Optional NVIDIA NIM backend, `gpu` compose profile, and manual smoke checklist (PS5.3 / PS5.7).
- **[llm_cost_guardrails.md](llm_cost_guardrails.md)** — Cost telemetry and process/postgres budget modes (PS5.6).
- **[evals_backend_parity.md](evals_backend_parity.md)** — OpenAI vs GPU parity reports, invalid-arm rules, and promotion criteria (PS5.8).
- **[adr/README.md](adr/README.md)** — ADR index 0001-0012 (PS6.10 / PR2.1).
- **[adr/0005-environment-strategy-dev-stage-prod.md](adr/0005-environment-strategy-dev-stage-prod.md)** — `dev` / `stage` / `prod` model, promotion gates (PS6.1).
- **[threat_model.md](threat_model.md)** — Portfolio threat model: injection, tool abuse, poisoning, secrets (PS6.10).
- **[portfolio/README.md](portfolio/README.md)** — External reviewer entry: demos, runbooks, dependency hygiene (PS6.10).
- **[runbooks/environment_promotion.md](runbooks/environment_promotion.md)** — Promote releases and GPU canaries across environments (PS6.1).
- **[adr/0006-kubernetes-packaging-helm.md](adr/0006-kubernetes-packaging-helm.md)** — Helm chart layout and env overlays (PS6.2).
- **[runbooks/local_k8s_dev.md](runbooks/local_k8s_dev.md)** — Local kind cluster + `make k8s-up` (PS6.3).
- **workflow/** — High-level pipeline (Ingest to Post-incident) and escalation path; aligns with `roadmap/01-foundation-mvp.md` and `roadmap/goals.md` F1–F10.
- **architecture/** — System boundaries (API, Agent, MCP, OPA, storage, observability), repo layout, and production-ready criteria from `goals.md` §4.5.
- **agent/** — LangGraph state machine and Act logic (safe vs restricted, OPA, approval); implements behaviour described in `roadmap/01-foundation-mvp.md` and policy in `roadmap/goals.md` §4.3.
- **planning/** — Sprint and phase roadmap (S1, S2, Phase 4) and epic→deliverable mapping; mirrors `roadmap/01-foundation-mvp.md`.
- **requirements/** — How goals decompose into Functional, Non-functional, Policy, and MoE/MoP; references `roadmap/goals.md` §4.
- **data/** — Audit log event schema (append-only, immutable); matches `roadmap/goals.md` §4.6.

**Cross-references for AI:** When answering questions about pipeline, architecture, agent behaviour, roadmap, or requirements, use this index to locate the right .mmd; the canonical text remains in `roadmap/goals.md`, `roadmap/01-foundation-mvp.md`, and `roadmap/02-production-scale.md`.

---

## Folder structure

| Folder | Purpose | Key concepts |
|--------|---------|--------------|
| **[workflow/](workflow/)** | End-to-end pipeline and escalation | Ingest, Triage, Investigate, Decide, Act, Report, Post-incident; when to escalate (confidence, evidence, timeout, OPA error). |
| **[architecture/](architecture/)** | System shape and repo layout | FastAPI, LangGraph, MCP servers (Telemetry, KB, Ticketing, GitOps), OPA, Postgres/pgvector, DuckDB, data/, kb/, ops-config, OTel/Jaeger/Prometheus/Grafana; single-command run, pinned deps, structured logging. |
| **[agent/](agent/)** | Agent state and Act behaviour | LangGraph nodes (Triage → Investigate → Decide → Act → Report); Escalation state; safe vs restricted steps; OPA allow/deny/error; approval request and execution. |
| **[planning/](planning/)** | Delivery plan | Sprint 1 (pipeline to Report + evals + OTel), Sprint 2 (Act + OPA + approvals + injection suite), Phase 4 (docs, runbooks, expanded evals). |
| **[requirements/](requirements/)** | Goals and measures | Functional (F1–F10), Non-functional (NF1–NF9), Policy (P1–P6); MoE (triage accuracy, citation precision, unsafe=0, escalation); MoP (latency, tool-call count). |
| **[data/](data/)** | Audit and schema | Audit log: timestamp, trace_id, incident_id, actor, tool, args_hash, decision, policy_result, outcome; application append-only, not tamper-evident. |
| **[runbooks/](runbooks/)** | Operator & maintainer runbooks | How to add a new MCP, how to add eval cases, how to operate the agent, future playbooks. |

---

## Index of diagrams

### Workflow
| Diagram | File | Use when |
|---------|------|----------|
| End-to-end pipeline | [workflow/end_to_end_pipeline.mmd](workflow/end_to_end_pipeline.mmd) | Explaining the full flow from ingest to post-incident. |
| Pipeline with escalation path | [workflow/pipeline_with_escalation.mmd](workflow/pipeline_with_escalation.mmd) | Showing when the agent escalates (confidence/evidence/timeout/OPA) and hands off to Report. |

### Architecture
| Diagram | File | Use when |
|---------|------|----------|
| System architecture (components) | [architecture/system_architecture.mmd](architecture/system_architecture.mmd) | Describing components, data flow, and observability. |
| Repository structure | [architecture/repo_structure.mmd](architecture/repo_structure.mmd) | Explaining directory layout (apps/, data/, kb/, evals/, infra/). |
| Production-ready criteria | [architecture/production_ready_criteria.mmd](architecture/production_ready_criteria.mmd) | Checking or explaining "production-ready" (single command, fixtures, evals, lockfile, logging). |

### Agent
| Diagram | File | Use when |
|---------|------|----------|
| LangGraph state flow | [agent/langgraph_state_flow.mmd](agent/langgraph_state_flow.mmd) | Describing agent states and transitions, including to Escalation. |
| Act flow: safe vs restricted | [agent/act_flow_safe_restricted.mmd](agent/act_flow_safe_restricted.mmd) | Explaining how safe steps execute vs restricted (OPA, approval, execute or deny + escalation). |

### Planning
| Diagram | File | Use when |
|---------|------|----------|
| Roadmap: sprints and phase | [planning/roadmap_sprints.mmd](planning/roadmap_sprints.mmd) | Showing S1, S2, Phase 4 and what each delivers. |
| Epic and deliverable summary | [planning/epic_deliverable_summary.mmd](planning/epic_deliverable_summary.mmd) | Mapping epics (E0, E1, E2) to deliverables. |

### Requirements
| Diagram | File | Use when |
|---------|------|----------|
| Requirements structure | [requirements/requirements_structure.mmd](requirements/requirements_structure.mmd) | Showing how goals break into F, NF, Policy, MoE. |
| MoE / MoP | [requirements/moe_mop.mmd](requirements/moe_mop.mmd) | Explaining effectiveness and performance measures (evals, dashboard). |

### Data / schema
| Diagram | File | Use when |
|---------|------|----------|
| Audit log event schema | [data/audit_log_schema.mmd](data/audit_log_schema.mmd) | Defining or implementing the audit log format (goals.md §4.6). |

---

## UI

- Next.js operator UI (Phase 4 P4.5): [../apps/ui/README.md](../apps/ui/README.md)
- Post-incident learning loop (Phase 4 P4.7): [runbooks/post_incident_loop.md](runbooks/post_incident_loop.md)
- 15-minute MVP demo script (with optional `.env` skip): [runbooks/demo_15min.md](runbooks/demo_15min.md)
- DB migrations runbook (PS1.3): [runbooks/db_migrations.md](runbooks/db_migrations.md)
- Replay metadata schema and usage (PS1.4): [replay_metadata.md](replay_metadata.md)
- Replay CLI/API workflow (PS1.5): [runbooks/replay_workflow.md](runbooks/replay_workflow.md)
- Fixture upload + simulate (PS2.7): [runbooks/fixture_upload_simulation.md](runbooks/fixture_upload_simulation.md)
- LLM gateway contract (PS1.6): [llm_gateway.md](llm_gateway.md)
- Optional GPU backend (PS5.3 / PS5.7): [llm_gpu_backend.md](llm_gpu_backend.md)
- LLM cost guardrails (PS5.6): [llm_cost_guardrails.md](llm_cost_guardrails.md)
- Backend parity evals (PS5.8): [evals_backend_parity.md](evals_backend_parity.md)
- Guardrails fail-closed minimum hardening (PS1.7): [runbooks/guardrails_minimum_hardening.md](runbooks/guardrails_minimum_hardening.md)
- Distributed tracing + W3C propagation verification (PS1.9): [runbooks/distributed_tracing_ps19.md](runbooks/distributed_tracing_ps19.md)

*.mmd file paths are relative to the `docs/` directory (for example,
`workflow/end_to_end_pipeline.mmd` = `docs/workflow/end_to_end_pipeline.mmd` in the repo).*

---

## Updating diagrams

- When **goals**, **roadmap**, or **architecture** change, update the matching .mmd and, if needed, the descriptions in this file.
- Keep diagram IDs and labels consistent with terminology in `roadmap/goals.md`, `roadmap/01-foundation-mvp.md`, and `roadmap/02-production-scale.md` (e.g. "escalation packet", "fail-closed", "safe vs restricted").

---

## Maintenance

| Field | Value |
|-------|--------|
| **Document version** | 1.1 |
| **Last updated** | 2026-11-26 |

### Instructions for AI when working in `docs/`

1. **Keep index and folder in sync.** Before adding, removing, or renaming any `.mmd` in `docs/` or subfolders, read this README. After the change, update the "Folder structure" table and "Index of diagrams" so they match the actual files. No orphan rows (file removed but still in index); no missing rows (new .mmd not listed).

2. **One diagram = one .mmd.** New diagrams go in the right subfolder (`workflow/`, `architecture/`, `agent/`, `planning/`, `requirements/`, `data/`). Add one Index row under the right heading; keep Folder structure accurate.

3. **Canonical text is in roadmap.** When changing behaviour or requirements, update `roadmap/goals.md`, `roadmap/01-foundation-mvp.md`, or `roadmap/02-production-scale.md` first, then the relevant .mmd and this README if needed. Do not define requirements or process only in `docs/`.

4. **If unsure, list the folder.** When unsure which .mmd exist in a subfolder, list that folder (e.g. `docs/workflow/`) and then update this README so Index and Folder structure match.

5. **Bump version or date on substantive edits.** When you add a section, rework Maintenance, or change the index, set "Last updated" to today (YYYY-MM-DD) or bump "Document version".
