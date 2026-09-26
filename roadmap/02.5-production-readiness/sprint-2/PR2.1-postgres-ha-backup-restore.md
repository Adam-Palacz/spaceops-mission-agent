# PR2.1 - Postgres HA posture and backup/restore drill

## Description

Move Postgres from "persistent enough for stage" toward a production-pilot posture. The immediate
requirement is a tested backup and restore drill; managed HA can be selected where available.

## Requirements

- Decide production-pilot Postgres target: managed cloud DB, in-cluster operator, or documented
  staged transition.
- Define backup schedule, retention, encryption, and restore owner.
- Execute restore drill using representative data: incidents, audit, approvals, checkpoints,
  queue ledger, and LLM usage ledger.
- Record RTO/RPO and known data-loss boundaries.

## Checklist

- [x] ADR/runbook updated with Postgres production posture.
- [x] Backup job or managed backup configuration documented.
- [x] Restore drill executed.
- [x] Data integrity checks after restore documented.
- [x] RTO/RPO targets and logical restore measurements recorded.

## Test requirements

- Automated or manual restore verification steps.
- Link tests for runbook/ADR references.

## Implementation notes

- Added [ADR 0012](../../../docs/adr/0012-postgres-production-pilot-ha-backup.md), selecting
  managed Postgres HA as the production-pilot target and documenting the staged transition from the
  current in-cluster StatefulSet.
- Added [postgres_backup_restore.md](../../../docs/runbooks/postgres_backup_restore.md) with backup
  schedule, retention, encryption, restore ownership, logical dump/restore steps, managed PITR drill
  steps, representative data categories, integrity checks, and data-loss boundaries.
- Added evidence record
  [evidence/PR2.1-postgres-restore-drill-2026-09-26.json](evidence/PR2.1-postgres-restore-drill-2026-09-26.json).
- Added link/content tests in
  [tests/test_production_readiness_pr21_postgres_restore.py](../../../tests/test_production_readiness_pr21_postgres_restore.py).

## Initial blocked attempt - 2026-07-03

Local restore execution was attempted against the existing Docker Compose Postgres path, but Docker
is not running in this workspace:

```powershell
docker info --format '{{.ServerVersion}}'
```

Observed error: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`.

The blocked attempt remains recorded in
[evidence/PR2.1-postgres-restore-drill-2026-07-03.json](evidence/PR2.1-postgres-restore-drill-2026-07-03.json).

## Completed logical restore drill - 2026-09-26

The drill ran against an isolated `pgvector/pgvector:pg15` container and a separate restore
database, without using the project Postgres volume.

- Applied Alembic through revision `20260603_0003`.
- Seeded incidents, runs, approval audit, checkpoints, queue, DLQ, and LLM usage ledger markers.
- Created a custom-format `pg_dump`, restored it into `spaceops_pr21_restore`, and ran
  `alembic upgrade head`.
- Source and restored row counts matched for every required table.
- Marker values matched, including checkpoint `next_node`, queue status, and token total.
- The restored append-only audit trigger rejected a tamper attempt.
- Measured RTO: **10.32 seconds** (**0.172 minutes**), below the 60-minute target.
- Measured RPO for the quiesced logical dataset: **0 minutes**. Logical dumps still do not cover
  writes after dump start unless the application is quiesced.

This proves the logical dump/restore fallback. Managed Cloud SQL HA/PITR remains a production-pilot
go/no-go drill and is not claimed by PR2.1.

## Status

Done: production posture, backup policy, logical restore execution, integrity checks, measured
RTO/RPO, evidence, and link/content tests are complete.
