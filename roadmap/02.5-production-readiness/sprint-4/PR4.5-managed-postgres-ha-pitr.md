# PR4.5 - Managed Postgres HA and PITR drill

| Field | Value |
|-------|-------|
| **Status** | In progress |
| **Closes** | PR2.1 managed HA/PITR gap |
| **Owner** | Data / SRE |
| **Depends on** | PR4.4 platform/IAM baseline |

## Description

Prove the selected managed Postgres service can meet the pilot's availability, backup, point-in-time
recovery, and restore requirements.

## Requirements

- Provision the smallest practical temporary managed Postgres HA profile through Terraform.
- Enable automated backups, PITR, encryption, private connectivity, and least-privilege identity.
- Record configured recovery window, expected RPO/RTO, region/zone topology, and cost guardrails.
- Insert a sanitized canary sequence and capture a recovery timestamp between mutations.
- Exercise failover or provider-supported HA verification and perform PITR to an isolated instance.
- Verify restored data boundaries, application connectivity, audit events, and measured RTO/RPO.
- Remove temporary instances, backups, addresses, and networking after evidence capture unless an
  approved pilot owner explicitly retains them.

## Checklist

- [x] Terraform plan and cost estimate are reviewed.
- [x] HA, backups, PITR, encryption, and IAM are configured.
- [x] Failover/HA verification is executed.
- [x] Isolated PITR restore is executed and validated.
- [x] Measured RTO/RPO and data-loss boundary are recorded.
- [ ] Paid-resource teardown and residual-resource check pass.

## Test requirements

- Pre- and post-recovery canaries prove the selected recovery boundary.
- Application smoke test succeeds against the restored database.
- Unauthorized database and backup access fails.
- Evidence contains timestamps and sanitized resource references, not credentials or project IDs.
- Cloud inventory after teardown shows no unintended billable database resources.

## Done gate

The existing logical dump/restore drill does not satisfy this task. Mark Done only after an actual
managed HA/PITR drill and verified cleanup.

## Execution evidence (2026-11-23)

- Regional HA failover completed in 42 seconds, changed the active zone, and retained both canary
  rows.
- The isolated PITR operation completed in 642 seconds. The restore included the committed
  pre-boundary row and excluded the post-boundary row.
- Alembic connected to the restored database through the keyless Auth Proxy and IAM database user.
- A separate principal without Cloud SQL roles received HTTP `403` for instance and backup APIs,
  and its IAM database login was denied.
- Both billable instances, their automatic backups, temporary proxies, temporary principal, and
  operator IAM grants were removed. Cloud SQL inventory is empty.
- Google retains the service-producer subnet for up to four days after instance deletion. The empty
  VPC, private range, and service connection therefore remain tracked in Terraform pending a retry
  after 2026-11-27 13:04 UTC. They carry no database runtime charge.

Status remains **In progress** until the provider hold expires and the residual network inventory
check passes.

Evidence:

- [Managed HA/PITR drill](../../../docs/managed_postgres_ha_pitr_pr45.md)
- [Sanitized machine-readable result](evidence/PR4.5-cloud-sql-ha-pitr-2026-11-23.json)
