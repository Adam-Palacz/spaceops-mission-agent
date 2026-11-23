# PR4.5 - Managed Postgres HA and PITR drill

| Field | Value |
|-------|-------|
| **Status** | Todo |
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

- [ ] Terraform plan and cost estimate are reviewed.
- [ ] HA, backups, PITR, encryption, and IAM are configured.
- [ ] Failover/HA verification is executed.
- [ ] Isolated PITR restore is executed and validated.
- [ ] Measured RTO/RPO and data-loss boundary are recorded.
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
