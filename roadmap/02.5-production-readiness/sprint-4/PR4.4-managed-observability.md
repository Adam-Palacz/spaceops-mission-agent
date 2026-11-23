# PR4.4 - Managed logging and tracing evidence

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Closes** | PR2.4 production-pilot gates |
| **Owner** | SRE / Security |
| **Depends on** | PR4.3 |

## Description

Turn the PR2.4 retention/privacy policy into executed managed-backend evidence for the selected
production-pilot platform.

## Requirements

- Configure managed logging and tracing in the approved region through IaC.
- Use workload identity and least-privilege access; do not introduce static exporter credentials.
- Configure the approved retention period and document provider deletion/expiry semantics.
- Prove an authorized operator can query a sanitized canary log and correlated trace.
- Prove an unauthorized principal cannot query or export the same records.
- Execute a deletion/expiry drill, including documented behavior of backups and provider copies.
- Apply masking/redaction policy to logs, traces, audit, reports, screenshots, and exports.

## Checklist

- [x] Managed backend and retention are configured through IaC.
- [x] Sanitized log/trace correlation query succeeds.
- [x] Unauthorized query/export is denied.
- [x] Deletion/expiry behavior is exercised and recorded.
- [x] Masking and secret scans pass across evidence outputs.
- [x] Temporary resources are removed unless retained by the approved pilot plan.

## Test requirements

- Exporter and backend health checks pass.
- Authorized and denied access tests use separate principals.
- Evidence records retention configuration, timestamps, query outcome, and sanitized IDs.
- Leak scan finds no credentials, project identifiers, personal data, or raw sensitive payloads.
- Teardown verification lists any retained billable resource and accountable owner.

## Done gate

Local Jaeger or an ephemeral in-cluster backend is insufficient. Evidence must come from the
managed backend selected for the pilot or from an explicitly approved equivalent.

## Completion evidence (2026-11-23)

- Terraform converged a regional Cloud Logging bucket with 30-day retention, a selective sink, and
  a keyless collector identity with only log-write and trace-agent roles.
- An authorized operator read one sanitized canary log and one Cloud Trace span carrying the same
  synthetic correlation identifier.
- A separate temporary service account without read access received HTTP `403`; the account and
  its impersonation binding were then removed.
- Terraform teardown removed the sink, collector identity, and IAM bindings. The log bucket entered
  the provider `DELETE_REQUESTED` recovery state. No GKE or Cloud SQL runtime was retained.
- Cloud Trace per-record deletion is not available; the provider-enforced 30-day expiry is recorded
  as the trace deletion mechanism.
- Committed evidence contains no project ID, operator contact, credential, or raw payload.

Evidence:

- [Managed observability design and drill](../../../docs/managed_observability_pr44.md)
- [Sanitized machine-readable result](evidence/PR4.4-managed-observability-2026-11-23.json)
