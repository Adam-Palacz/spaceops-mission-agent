# ADR 0012 - Postgres production-pilot HA and backup posture

- **Status:** Accepted
- **Date:** 2026-07-03
- **Deciders:** SpaceOps Mission Agent Lab maintainers
- **Related:** PR2.1, [ADR 0003](0003-langgraph-durable-checkpoint-postgres.md), [ADR 0005](0005-environment-strategy-dev-stage-prod.md), [ADR 0009](0009-gcp-baseline-portable-first.md), [Postgres backup/restore runbook](../runbooks/postgres_backup_restore.md)

## Context

The current Helm chart runs Postgres as a single-replica StatefulSet with a persistent volume. That
is enough for local development, stage proofs, and failure drills that restart the Postgres pod, but
it is not a production-pilot HA posture. Operational Postgres stores mission-relevant state:

- telemetry and incident rows,
- append-only audit rows,
- dead-letter queue rows,
- durable graph checkpoints,
- optional Variant A agent run queue rows,
- shared LLM usage ledger rows for `LLM_BUDGET_MODE=postgres`.

Approval request objects are still file-backed under `data/approvals`; the database backup protects
approval audit history but not those JSON request files until PR2.2 moves or backs up that path.

## Decision

Production pilot uses a managed cloud Postgres service with provider-managed HA, encrypted automated
backups, and point-in-time recovery. On GCP the target is Cloud SQL for PostgreSQL with regional HA
and PITR enabled. The in-cluster StatefulSet remains the default for local development and ephemeral
stage until the managed database transition is implemented.

The staged transition is:

1. Keep the Helm StatefulSet for local and short-lived stage.
2. Add an external Postgres mode by setting `postgres.enabled=false` and pointing all services at a
   managed `DATABASE_URL` from the environment secret.
3. Run Alembic migrations against the managed database.
4. Execute the PR2.1 restore drill from [postgres_backup_restore.md](../runbooks/postgres_backup_restore.md)
   before any production-pilot go/no-go.
5. Promote only after backup success, restore success, data integrity checks, and RTO/RPO evidence
   are attached to the sprint record.

## Backup Policy

| Item | Production-pilot target |
|------|-------------------------|
| Schedule | Managed automated backup at least daily; PITR/WAL retention enabled |
| Retention | 7 days minimum for pilot; 30 days target before broader production |
| Encryption | Provider-managed encryption by default; customer-managed key preferred before broader production |
| Restore owner | Data/on-call owner for restore execution; platform owner for cloud/IAM access |
| RPO target | <= 15 minutes with PITR; <= 24 hours if only daily logical dumps are available |
| RTO target | <= 60 minutes for pilot database restore and application repointing |

## Consequences

- Positive:
  - Database HA and backups are delegated to a managed service instead of hand-rolling HA in the app
    chart.
  - The existing Helm chart remains portable for local and stage.
  - Restore drills can be repeated with either managed PITR or logical dump/restore.
- Trade-offs:
  - Stage is still single-instance Postgres until external database mode is wired and exercised.
  - Approval request JSON files remain a separate backup concern until PR2.2.
  - PITR RPO depends on managed database configuration; logical-only backups have a wider data-loss
    boundary.

