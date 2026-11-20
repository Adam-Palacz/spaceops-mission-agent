# PR2 Sprint Review

## Verdict

PR2 is complete as the data durability, secrets, security-review, and privacy-policy track.
Postgres restore and ESO/GSM rotation have executed evidence, and all four board tasks are Done.

Sprint completion does **not** grant production-pilot approval. PR2.3 High findings PR23-002 and
PR23-003 remain phase-closure blockers, while managed Postgres PITR and managed trace/log backend
proof remain PR3.4 gates.

## Completed tasks

| Task | Result | Evidence |
|------|--------|----------|
| PR2.1 | Done | Logical backup/restore drill restored seven required data categories with measured 10.32 s RTO and 0 min quiesced-data RPO. |
| PR2.2 | Done | [Local ESO proof](evidence/PR2.2-local-eso-rotation-2026-09-26.json) and [live GSM/GKE rotation](evidence/PR2.2-live-gsm-rotation-2026-11-20.json). |
| PR2.3 | Done | [Security review](../../../docs/security_control_review_pr23.md) with one remediated High and two explicit High phase blockers. |
| PR2.4 | Done | [Retention/privacy policy](../../../docs/data_retention_privacy_pr24.md), baseline log redaction, and managed-backend implementation gates. |

## PR2.2 live summary

- Backend: Google Secret Manager through External Secrets Operator and GKE Workload Identity; no
  service-account key.
- Credentials: generated stage-only synthetic values; no production credential was used.
- Contract correction: slash-based remote names were replaced by GSM-compatible hyphenated IDs.
- Rotation: all seven chart secret classes changed hashes; Postgres role and clients were changed
  in a coordinated cutover.
- Workload recovery: API health returned 200 and database connection succeeded before and after;
  API, Postgres, KB MCP, and GitOps MCP pod UIDs changed.
- Approval boundary: new token returned 200; previous and missing tokens returned 401.
- Rollback: prior approval value was published as a new latest version, synchronized, and restored;
  the failed version was disabled after sync.
- Leak scan: zero raw-value matches across SpaceOps and ESO logs, Kubernetes events, API audit,
  Jaeger service metadata, and Prometheus labels/alerts.
- Cost cleanup: zero GKE clusters, Artifact Registry repositories, compute instances, persistent
  disks, forwarding rules, reserved addresses, or GSM drill secrets remain. Terraform retains only
  budget-alert and notification resources.

## Operational findings

1. Google Secret Manager secret IDs cannot contain `/`; backend-neutral path notation must not be
   copied directly into GSM `remoteRef.key`.
2. ESO `LatestOrFail` does not select an older enabled version when the latest numbered version is
   disabled. Safe rollback publishes the prior value as a new latest version, waits for sync, and
   then disables the failed version.
3. A single `e2-standard-2` preemptible node was sufficient for this short drill and minimized cost,
   but it is not an HA or soak profile.

## Residual risks and PR3.4 gates

- PR23-002: approval principal/role is not cryptographically established.
- PR23-003: approval execution claim is not atomic across API replicas.
- Managed Cloud SQL HA/PITR evidence remains required before production-pilot go/no-go.
- Cloud Trace/Cloud Logging retention, access-denial, and deletion/expiry evidence remains pending.
- MCP service-token rotation is N/A until MCP caller authentication exists (PR23-005).
- Audit storage remains application append-only, not tamper-evident (PR23-004).

## Sprint decision

The PR2 engineering scope is accepted as complete. The phase remains **No-go for production pilot**
until PR3.4 resolves or formally waives the named High findings and verifies the remaining managed
service gates.
