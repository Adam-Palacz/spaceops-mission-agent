# Managed PostgreSQL HA/PITR Drill (PR4.5)

## Decision and profile

The production-pilot database target remains Cloud SQL for PostgreSQL 15 with regional HA. The
temporary drill used the smallest dedicated-core profile accepted for regional HA:

- one vCPU / 3.75 GiB (`db-custom-1-3840`);
- 10 GiB fixed SSD;
- primary and standby in separate zones in `us-central1`;
- automated backups and PITR enabled with seven retained backups and seven days of transaction
  logs;
- Google-managed encryption at rest and `ENCRYPTED_ONLY` transport;
- a dedicated VPC, Private Service Access range, and private IP;
- Cloud SQL IAM database authentication, `roles/cloudsql.client`, and
  `roles/cloudsql.instanceUser`; no application password was persisted.

Terraform defines the profile in `infra/terraform/gcp/managed_postgres.tf`. Public IPv4 remained
enabled only so the keyless Cloud SQL Auth Proxy could execute the temporary drill from the
operator workstation; the production path is private IP from the pilot VPC.

## Cost guardrails

- The source and restore instances are disposable and deletion protection is disabled.
- The drill limit is three hours; no instance may remain for convenience.
- The source existed for less than one hour. The isolated restore existed for approximately
  33 minutes.
- Query Insights, disk autoresize, read replicas, and final backups were disabled.
- The restore was deleted before the Terraform-managed source.
- Service APIs may remain enabled because they have no standalone runtime charge.

The regional source includes a standby, and the PITR clone briefly duplicates that topology.
Therefore the drill is intentionally time-boxed even though the selected machine is the smallest
practical HA tier.

## Executed drill, 2026-11-23

### HA failover

The source started with primary and standby in different zones. A provider failover completed in
42 seconds and the active zone changed to the former standby zone. A fresh IAM-authenticated query
immediately returned both source canary rows.

### PITR boundary

1. An IAM-authenticated application user created and committed
   `synthetic-before-pitr`.
2. The operator captured a database-server timestamp after that commit.
3. `synthetic-after-pitr` was committed after the captured boundary.
4. Cloud SQL cloned the source to an isolated regional instance at the selected timestamp.
5. The provider clone operation took 642 seconds.
6. The restore contained exactly the pre-boundary row and excluded the post-boundary row.
7. `python -m alembic current` connected successfully through the Auth Proxy using the restored
   database and IAM identity.

The measured restore is within the one-hour pilot RTO. The selected timestamp was approximately
two minutes old when the clone started, within the 15-minute pilot RPO target. The intended
data-loss boundary is every transaction committed after the selected timestamp.

### Negative authorization

A separate temporary service account received no Cloud SQL client, instance-user, viewer, or
backup role. Its token received HTTP `403` for both instance metadata and backup-list requests.
Even after a matching IAM database user was created, database login failed because the principal
lacked the required IAM authorization. The temporary principal was deleted after the checks.

## Teardown and provider recovery hold

Both Cloud SQL instances, their databases, users, automated backups, and temporary proxies were
removed. Inventory returned zero Cloud SQL instances and no final backup was requested. Project IAM
bindings for the drill operator were removed.

Private Service Access cleanup was requested three times. Google rejected deletion because Cloud
SQL keeps service-producer resources recoverable for up to four days after the last instance is
deleted. During that documented provider window:

- the VPC, allocated range, and service connection remain in Terraform state;
- they host no instance and have no database runtime charge;
- they must not be reused;
- SRE must retry the targeted Terraform destroy after 2026-11-27 13:04 UTC and verify the VPC,
  range, and peering are absent.

PR4.5 remains **In progress** until that residual inventory check passes. This recovery hold is not
permission to retain a database or to mark the task Done early.

## Sanitized evidence

The machine-readable record is
`roadmap/02.5-production-readiness/sprint-4/evidence/PR4.5-cloud-sql-ha-pitr-2026-11-23.json`.
It excludes project identifiers, account names, connection strings, passwords, access tokens,
private addresses, and operation IDs.
