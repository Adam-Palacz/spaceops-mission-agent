# PR2.2 - Secrets rotation and external secret proof

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
- [ ] Rotation procedure executed for at least the critical secret classes.
- [x] Local synthetic ESO sync and probe rollout behavior verified.
- [ ] Live SpaceOps workload restart/rollout behavior verified.
- [x] Local probe/ESO/event leak check performed; live logs/traces/audit/dashboard check pending.
- [x] Rollback path documented; live rollback execution pending.

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

## Remaining live proof

PR2.2 requires a separately approved ESO/GSM stage window. The live drill must rotate applicable
real secret classes one at a time, verify actual SpaceOps workload recovery, inspect logs/traces/
audit/dashboards, and execute rollback for at least one class. MCP service-token rotation is
currently N/A because MCP authentication is not implemented; this remains an explicit boundary.

## Status

In progress: inventory, chart contract, local ESO rotation, probe rollout, local leak scan, Helm
plaintext checks, live procedure, and rollback plan are complete. Live ESO/GSM workload rotation
and rollback evidence remain pending explicit approval.

