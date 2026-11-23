# PR4.4 - Managed logging and tracing evidence

| Field | Value |
|-------|-------|
| **Status** | Todo |
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

- [ ] Managed backend and retention are configured through IaC.
- [ ] Sanitized log/trace correlation query succeeds.
- [ ] Unauthorized query/export is denied.
- [ ] Deletion/expiry behavior is exercised and recorded.
- [ ] Masking and secret scans pass across evidence outputs.
- [ ] Temporary resources are removed unless retained by the approved pilot plan.

## Test requirements

- Exporter and backend health checks pass.
- Authorized and denied access tests use separate principals.
- Evidence records retention configuration, timestamps, query outcome, and sanitized IDs.
- Leak scan finds no credentials, project identifiers, personal data, or raw sensitive payloads.
- Teardown verification lists any retained billable resource and accountable owner.

## Done gate

Local Jaeger or an ephemeral in-cluster backend is insufficient. Evidence must come from the
managed backend selected for the pilot or from an explicitly approved equivalent.
