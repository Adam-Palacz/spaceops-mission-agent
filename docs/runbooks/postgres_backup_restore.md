# Postgres HA, backup, and restore drill (PR2.1)

This runbook defines the production-pilot Postgres posture and the repeatable backup/restore drill.

**Related:** [ADR 0012](../adr/0012-postgres-production-pilot-ha-backup.md),
[graph_worker_checkpoint_ops.md](graph_worker_checkpoint_ops.md),
[queue_dlq_recovery.md](queue_dlq_recovery.md),
[llm_cost_guardrails.md](llm_cost_guardrails.md),
[db_migrations.md](db_migrations.md).

## Posture Decision

Production pilot targets managed Postgres HA. On GCP, use Cloud SQL for PostgreSQL with regional HA,
automated backups, PITR, encrypted storage, and a private connection where possible.

Current state:

| Environment | Current Postgres | Production-readiness stance |
|-------------|------------------|-----------------------------|
| local | Docker Compose `pgvector/pgvector:pg15` | Dev only; logical dump/restore drill supported |
| stage | Helm single-replica StatefulSet, persistent volume | Acceptable for ephemeral stage; not HA |
| production pilot | Managed Postgres | Required before pilot go/no-go |

## Backup Configuration

| Control | Pilot requirement |
|---------|-------------------|
| Automated backups | Enabled, daily minimum |
| PITR/WAL | Enabled when provider supports it |
| Retention | 7 days minimum; 30 days target |
| Encryption | Provider encryption required; CMEK preferred |
| Backup owner | Data/on-call owner |
| Restore owner | Data/on-call executes restore; platform grants cloud/IAM and networking |
| RPO | <= 15 minutes with PITR; <= 24 hours for logical-dump fallback |
| RTO | <= 60 minutes for restore, migrations, smoke, and app repoint |

## Representative Dataset

The drill dataset must cover these state categories:

| Category | Tables / source | Integrity check |
|----------|-----------------|-----------------|
| Incidents | `incidents`, `runs` | Expected `incident_id`, `run_id`, status, and metadata counts |
| Audit | `audit_log` | Append-only trigger exists and approval-related audit rows are present |
| Approvals | `audit_log` plus `data/approvals` note | Approval decisions are visible in audit; JSON request files are backed up separately until PR2.2 |
| Checkpoints | `agent_graph_checkpoints` | Latest checkpoint row has expected `run_id`, `status`, and `next_node` |
| Queue ledger | `agent_run_queue`, `dlq_events` | Pending/done queue counts and DLQ event count match source |
| LLM usage ledger | `llm_usage_ledger` | UTC-day token total matches source |

## Logical Dump Drill

Use this for local/stage and as the fallback path for managed Postgres.

1. Capture source counts and marker rows:

   ```sql
   SELECT 'incidents' AS table_name, count(*) FROM incidents
   UNION ALL SELECT 'runs', count(*) FROM runs
   UNION ALL SELECT 'audit_log', count(*) FROM audit_log
   UNION ALL SELECT 'dlq_events', count(*) FROM dlq_events
   UNION ALL SELECT 'agent_graph_checkpoints', count(*) FROM agent_graph_checkpoints
   UNION ALL SELECT 'agent_run_queue', count(*) FROM agent_run_queue
   UNION ALL SELECT 'llm_usage_ledger', count(*) FROM llm_usage_ledger;
   ```

2. Create the backup:

   ```bash
   pg_dump --format=custom --no-owner --no-acl \
     --file=/tmp/spaceops-pr21.dump "$DATABASE_URL"
   ```

3. Restore into an isolated database:

   ```bash
   createdb "$RESTORE_DATABASE_URL"
   pg_restore --clean --if-exists --no-owner --dbname="$RESTORE_DATABASE_URL" \
     /tmp/spaceops-pr21.dump
   ```

4. Run migrations against the restored database:

   ```bash
   DATABASE_URL="$RESTORE_DATABASE_URL" python -m alembic upgrade head
   ```

5. Run integrity checks:

   ```sql
   SELECT run_id, incident_id, status FROM runs ORDER BY started_at DESC LIMIT 5;
   SELECT incident_id, actor, tool, decision, outcome FROM audit_log ORDER BY timestamp DESC LIMIT 10;
   SELECT run_id, status, next_node FROM agent_graph_checkpoints ORDER BY updated_at DESC LIMIT 5;
   SELECT status, count(*) FROM agent_run_queue GROUP BY status ORDER BY status;
   SELECT reason, count(*) FROM dlq_events GROUP BY reason ORDER BY reason;
   SELECT usage_date, tokens_used FROM llm_usage_ledger ORDER BY usage_date DESC LIMIT 5;
   ```

6. Smoke the application against the restored database with write paths disabled unless this is a
   disposable environment:

   ```bash
   DATABASE_URL="$RESTORE_DATABASE_URL" python -m alembic current
   DATABASE_URL="$RESTORE_DATABASE_URL" python -m pytest tests/test_llm_cost_postgres_ps76.py -q
   ```

## Managed PITR Drill

Use this before production-pilot go/no-go.

1. Confirm automated backup, PITR, retention, encryption, and restore owner in the cloud console or
   IaC plan.
2. Insert or select a known marker run and LLM usage ledger row.
3. Record source timestamp `T0`.
4. Restore to a new managed instance or database at `T0`.
5. Apply connection secret changes only in an isolated namespace or restore test environment.
6. Run the integrity checks above.
7. Record:
   - backup source and restore target,
   - restore start/end time,
   - RTO,
   - RPO or last recoverable timestamp,
   - mismatches,
   - known data-loss boundaries.

## Data-Loss Boundaries

- Logical dumps lose writes after the dump start unless the application is quiesced.
- PITR loses writes after the selected recovery timestamp.
- `data/approvals` JSON files and file-based incident artifacts are not protected by Postgres
  backup; PR2.2 must cover secret-backed storage and artifact backup for those paths.
- External side effects such as tickets, GitOps PRs, and provider audit logs are recovered by their
  own systems, not by Postgres restore.
- In-flight graph execution resumes only from the most recent `agent_graph_checkpoints` row.

## PR2.1 Evidence

Record drill evidence under `roadmap/02.5-production-readiness/sprint-2/evidence/` with:

- restore environment and source,
- backup method,
- representative row counts,
- integrity check results,
- RTO/RPO,
- skipped or blocked items with owner.

Completed logical fallback drill:
[PR2.1-postgres-restore-drill-2026-09-26.json](../../roadmap/02.5-production-readiness/sprint-2/evidence/PR2.1-postgres-restore-drill-2026-09-26.json).
It verifies custom-format dump/restore, representative table counts, marker values, Alembic head,
and the restored append-only audit trigger. Managed Cloud SQL PITR remains required before the
production-pilot go/no-go.

