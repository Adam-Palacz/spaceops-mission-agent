# Secrets rotation and external-secret proof (PR2.2)

This runbook defines how SpaceOps rotates stage/prod secrets through External Secrets Operator
(ESO) and a managed backend. It also records the safe local proof used before touching GCP Secret
Manager (GSM) or real credentials.

**Related:** [ADR 0007](../adr/0007-secrets-management-k8s.md),
[Kubernetes secrets bootstrap](k8s_secrets_bootstrap.md), and
[stage operating policy](stage_operating_policy.md).

## Safety rules

- Never print, log, commit, screenshot, or store a real secret value in evidence.
- Record only secret identifiers, backend version numbers, Kubernetes resource versions, rollout
  UIDs, and one-way hashes produced inside disposable probe workloads.
- Use synthetic values for local proof.
- A live GSM rotation requires an approved stage window, named operator, rollback owner, and
  explicit confirmation immediately before creating/enabling a new secret version.
- Do not rotate production credentials as part of a documentation-only or dry-run task.

## Secret inventory

| Secret class | Store path | K8s key | Main consumers | Rotation note |
|--------------|------------|---------|----------------|---------------|
| Database password | `spaceops-{env}/postgres-password` | `postgres-password` | Postgres, API, persister, KB MCP, worker | Coordinated maintenance; database role and clients must change together |
| OpenAI/LLM key | `spaceops-{env}/openai-api-key` | `OPENAI_API_KEY` | API, agent worker | Restart consumers; smoke one guarded LLM path |
| Approval token | `spaceops-{env}/approval-api-key` | `APPROVAL_API_KEY` | API/UI clients | Restart API; old token must stop authorizing after cutover |
| GitOps token | `spaceops-{env}/github-token` | `GITHUB_TOKEN` | API and GitOps MCP | Restart consumers; verify read-only repository operation before writes |
| NGC key | `spaceops-{env}/ngc-api-key` | `NGC_API_KEY` | Optional NIM path | Rotate only when NIM is enabled |
| Cursor/GPU backend keys | `spaceops-{env}/cursor-sh-api-key`, `gpu-llm-api-key` | `CURSOR_SH_API_KEY`, `GPU_LLM_API_KEY` | Optional LLM backends | Restart API/worker and run backend health check |
| MCP service token | `spaceops-{env}/mcp-<name>-token` | Not implemented | Future authenticated MCP services | **N/A today:** MCP service-token auth is not implemented; track before claiming this class live |

Environment variables are injected with `secretKeyRef`; changing a Secret does not update an
already-running process. A controlled rollout is therefore part of every rotation.

## Completed local ESO proof

The local proof uses a dedicated namespace, ESO's `fake` provider, and five synthetic secret
classes: database, LLM, approval, GitOps, and an MCP-token contract probe.

Flow:

1. Install ESO into local kind.
2. Create a namespaced fake `SecretStore` with version-one synthetic values.
3. Create an `ExternalSecret` and wait for `Ready=True / SecretSynced`.
4. Start a probe Deployment that logs only SHA-256 hashes of injected values.
5. Replace all backend values with version two and force ESO synchronization.
6. Confirm the target Secret resource version changes.
7. Restart the probe and confirm its pod UID and all five hashes change.
8. Scan probe logs, ESO logs, and namespace events for the synthetic raw-value pattern.
9. Render stage/prod Helm overlays and confirm no `Secret` or `stringData` is emitted.

Evidence:
[PR2.2-local-eso-rotation-2026-09-26.json](../../roadmap/02.5-production-readiness/sprint-2/evidence/PR2.2-local-eso-rotation-2026-09-26.json).

This proves ESO synchronization and rollout mechanics without real credentials. It does not prove
GSM Workload Identity, live SpaceOps workload recovery, coordinated Postgres password rotation, or
cloud log/trace/dashboard leak checks.

## Controlled live stage procedure (ESO + GSM)

### Preconditions

- Stage window is approved and time-boxed.
- ESO, `SecretStore`, and Workload Identity are healthy.
- Current GSM versions and rollback versions are recorded by identifier only.
- `ExternalSecret` reports `Ready=True`.
- Affected workload replicas, owners, and smoke checks are listed.
- Evidence output location exists; terminal transcript redaction is enabled.

### Non-database secret rotation

For one class at a time:

1. Add a new GSM version using an approved secure-input mechanism. Do not put the value on the
   command line or in shell history.
2. Record only the GSM secret ID and new version number.
3. Force ESO refresh:

   ```bash
   kubectl annotate externalsecret spaceops-secrets \
     -n spaceops-stage force-sync="$(date +%s)" --overwrite
   kubectl wait --for=condition=Ready externalsecret/spaceops-secrets \
     -n spaceops-stage --timeout=2m
   ```

4. Confirm the target Kubernetes Secret resource version changed; do not decode its data.
5. Restart affected Deployments and wait for rollout completion.
6. Run `/health`, the relevant guarded operation, and PR1 monitoring checks.
7. Confirm the previous credential no longer authorizes where revocation can be tested safely.
8. Disable, but do not immediately destroy, the old GSM version until the rollback window closes.

### Database password rotation

Use a maintenance window:

1. Pause/scale down database-writing consumers.
2. Keep the prior GSM version enabled for rollback.
3. Change the Postgres role password through an authenticated administrative session.
4. Add/enable the matching GSM version and force ESO sync.
5. Restart Postgres clients, then restore replicas.
6. Verify migrations, API health, persister/queue progress, checkpoints, and LLM usage ledger access.
7. If verification fails, restore the prior database role password, re-enable the prior GSM
   version, force sync, and roll workloads again.

## Leak check

Search by known test sentinel or a locally computed hash; never paste a real secret into a shared
query or evidence file.

Check:

- API, worker, MCP, ESO, and Postgres logs;
- Jaeger trace attributes/events;
- audit payloads and action arguments;
- Prometheus labels and Grafana panels;
- Kubernetes events and Deployment descriptions;
- CI/release artifacts and terminal transcripts.

The live evidence must contain match counts and query scope, not matching raw content.

## Rollback

1. Re-enable the previously recorded backend version.
2. Force ESO synchronization and confirm a new Kubernetes Secret resource version.
3. Restart affected workloads.
4. Run the same smoke and leak checks.
5. For Postgres, restore the database role password before restarting clients.
6. Record cause, owner, timeline, and whether the failed version was disabled or destroyed.

## Closure criteria

PR2.2 can be marked Done only after a controlled stage rotation proves:

- ESO/GSM synchronization for the applicable critical classes;
- SpaceOps workload rollout and recovery;
- coordinated database-password handling or an explicit, owned waiver;
- logs, traces, audit, dashboards, events, and artifacts contain no secret values;
- rollback is executed for at least one class or demonstrated during a failed cutover.

