# PR2.2 - Secrets rotation and external secret proof

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Live drill date** | 2026-11-20 |
| **Backend** | Google Secret Manager + ESO + GKE Workload Identity |
| **Evidence** | [Local proof](evidence/PR2.2-local-eso-rotation-2026-09-26.json), [live GSM drill](evidence/PR2.2-live-gsm-rotation-2026-11-20.json) |

## Description

Prove that stage/prod secrets are not just designed but operable. Rotate secrets through the
approved external-secret path and verify workloads recover without leaking values.

## Requirements

- Use ESO/GSM/Vault or the selected stage/prod secret backend.
- Rotate OpenAI/LLM key, database password, approval token, MCP service token, and GitOps token
  where applicable.
- Validate rollout/restart behavior.
- Ensure logs, traces, audit events, and dashboards do not expose secret values.

## Checklist

- [x] Secret inventory documented.
- [x] Rotation procedure executed for at least the critical secret classes.
- [x] Local synthetic ESO sync and probe rollout behavior verified.
- [x] Live SpaceOps workload restart/rollout behavior verified.
- [x] Local and live logs/traces/audit/dashboard/event leak checks performed.
- [x] Rollback path documented and live approval-token rollback executed.

## Test requirements

- Helm template check proves no plaintext stage/prod secrets are rendered.
- Manual or scripted rotation evidence.

## Implementation notes

- Added [secrets_rotation_pr22.md](../../../docs/runbooks/secrets_rotation_pr22.md) with the secret
  inventory, ESO/GSM stage procedure, coordinated database-password cutover, leak checks, and
  rollback.
- Extended the chart `ExternalSecret` contract to include optional Cursor and GPU backend keys,
  matching keys already consumed by the API.
- Executed a safe local ESO proof on kind with the `fake` provider and synthetic database, LLM,
  approval, GitOps, and MCP contract values.
- Verified `SecretSynced`, target Secret resource-version change, probe pod replacement, and changed
  SHA-256 hashes for all five classes without recording raw values.
- Scanned probe logs, ESO logs, and Kubernetes events: zero synthetic raw-value matches.
- Rendered stage/prod Helm overlays with ESO enabled: one `ExternalSecret`, zero plaintext `Secret`
  resources, and zero `stringData` blocks; Helm lint passed.
- Evidence:
  [PR2.2-local-eso-rotation-2026-09-26.json](evidence/PR2.2-local-eso-rotation-2026-09-26.json).

## Completed live proof

The approved, time-boxed GKE stage drill used only generated synthetic credentials:

- enabled Secret Manager and IAM Credentials APIs through Terraform;
- installed ESO with GKE Workload Identity and no service-account key;
- corrected GSM-incompatible slash-based remote IDs to hyphenated secret IDs;
- rotated all seven chart secret classes and changed the Postgres role password in a coordinated
  cutover;
- proved API health and database connectivity before and after rotation;
- proved the new approval token returned 200 while the prior and missing tokens returned 401;
- restarted API, Postgres, KB MCP, GitOps MCP, and telemetry persister paths;
- executed approval-token rollback by publishing the prior value as a new latest GSM version;
- scanned SpaceOps/ESO logs, events, API audit, Jaeger metadata, and Prometheus labels/alerts:
  zero raw-value matches;
- deleted namespaces, seven GSM secrets, GKE, Artifact Registry, compute instances, disks,
  forwarding rules, and addresses; only Terraform budget-alert resources remain.

Evidence:
[PR2.2-live-gsm-rotation-2026-11-20.json](evidence/PR2.2-live-gsm-rotation-2026-11-20.json).

MCP service-token rotation remains N/A because MCP authentication is not implemented; PR23-005
tracks that boundary.

## Status

Done: local and live ESO/GSM proofs, coordinated database rotation, workload recovery, leak checks,
approval rollback, evidence, and cost cleanup are complete.

