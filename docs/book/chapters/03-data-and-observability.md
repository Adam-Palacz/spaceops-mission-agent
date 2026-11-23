# Data durability and observability

## Why

Agent correctness is inseparable from data durability and operational visibility. A report is not
trustworthy when telemetry persistence, approval state, audit records, or recovery behavior is
unknown.

## Decision

Postgres/pgvector is the durable application data plane. Logical backup/restore is proven in the
lab, while a managed HA/PITR service is required for a pilot. OpenTelemetry provides the
instrumentation boundary; Prometheus/Grafana supplies the production-readiness baseline. Managed
logging and tracing remain admission gates for non-synthetic pilot data.

## Implementation

- [ADR 0012](../../adr/0012-postgres-production-pilot-ha-backup.md) defines managed Postgres
  posture, RPO/RTO, and restore expectations.
- [Backup/restore runbook](../../runbooks/postgres_backup_restore.md) verifies schema and required
  data categories.
- [Monitoring analysis](../../monitoring-production-analysis.md) documents component coverage and
  gaps.
- [SLO policy](../../slo-production-readiness.md) defines availability, latency, errors, evidence,
  OPA, queue, Postgres, and budget signals.
- [Retention/privacy policy](../../data_retention_privacy_pr24.md) classifies data and constrains
  logs, traces, metrics, audit, approvals, prompts, exports, and deletion.

## Verification

PR2.1 restored seven required data categories with measured recovery. PR1.4 exercised API,
Postgres, OPA, queue, provider, and budget failures. Monitoring targets and rules recovered healthy,
and the final alert list was empty.

## Evidence

The [PR1 review](../../../roadmap/02.5-production-readiness/sprint-1/SPRINT_REVIEW.md) summarizes live
observability/failure proof. The [PR2 review](../../../roadmap/02.5-production-readiness/sprint-2/SPRINT_REVIEW.md)
summarizes durability, secret, security, and privacy work.

## Limitations

The current Postgres proof is a logical drill, not managed multi-zone HA/PITR evidence. In-cluster
Jaeger is ephemeral and not a production system of record. Authorized/denied query and
deletion/expiry evidence for managed logging/tracing is still missing.

## Lessons learned

Recovery must validate semantics, not just process exit codes. Restore evidence checks actual data
categories and schema revision; secret rotation checks client rollout and authentication behavior;
monitoring recovery checks targets, rules, and residual alerts.
