# SpaceOps production pilot plan (PR3.3)

## Decision boundary

This document defines a bounded production pilot, not unrestricted production and not autonomous
spacecraft operations. The pilot may start only after PR3.4 records `Conditional go` or `Go`.

The current default is **No-go** because approval identity/authorization (PR23-002), atomic approval
execution (PR23-003), and managed trace/log backend gates are not yet closed or explicitly waived.
Writing the plan does not waive those controls.

## Pilot charter

- **Purpose:** evaluate whether SpaceOps can safely assist human operators with telemetry anomaly
  triage, evidence collection, report generation, and controlled escalation.
- **Duration:** ten staffed business days, with exact start/end dates recorded by the pilot owner.
- **Operating window:** Monday-Friday, 09:00-17:00 in the declared local timezone. There is no
  unattended operation and no 24/7 support claim.
- **Environment:** dedicated GCP project and dedicated `spaceops-prod` namespace or cluster,
  provisioned through reviewed Terraform/Helm/GitOps. Stage remains separate.
- **Traffic:** low-volume, operator-initiated sessions only. No open public endpoint.
- **Users:** named pilot operators, platform/on-call engineers, security reviewer, and read-only
  pilot stakeholders. Anonymous and self-service users are prohibited.
- **Data:** synthetic or explicitly approved, minimized operational data. Real spacecraft,
  customer, personal, export-controlled, or special-category data is prohibited unless a later
  legal/security decision expands the scope in writing.

## Ownership and support model

Before PR3.4 can approve the pilot, every role below must have a named primary and backup in the
private change record. The public repository stores roles, not personal contact details.

| Responsibility | Accountable role | Operational responsibility |
|---|---|---|
| Pilot scope and go/no-go | Production-pilot owner | Approves dates, users, data, spend, and stop decisions |
| GCP, Kubernetes, releases | Platform owner | Provisioning, promotion, rollback, teardown, cost checks |
| Agent behavior and evals | Mission-agent owner | Scenario validation, quality/safety regression response |
| Identity, OPA, audit, secrets | Security owner | Access review, waivers, incident participation |
| Postgres, backup, retention | Data owner | Backup/restore, retention and deletion evidence |
| LLM provider and budget | Model/cost owner | Provider approval, quotas, token/cost review |
| Daily operation | Primary on-call | Acknowledgement, triage, safe runbook execution |
| Incident coordination | Incident commander | Severity, decisions, communications, closure |

Support exists only during the staffed pilot window. Outside it, the system is scaled to zero or
torn down and alerts route to the next scheduled review rather than implying a 24/7 pager.

## Environment and cost controls

- Production pilot uses immutable image references and the
  [PR3.1 release gate](runbooks/release_promotion_gate_pr31.md).
- Secrets use GSM plus External Secrets Operator and Workload Identity; no service-account keys or
  laptop `.env` deployment path.
- Postgres must follow the managed HA/backup posture and completed restore procedure in
  [ADR 0012](adr/0012-postgres-production-pilot-ha-backup.md).
- Monitoring uses the PR1 SLO baseline. Traces/logs must use the managed backends required by
  [PR2.4](data_retention_privacy_pr24.md), not ephemeral Jaeger as the system of record.
- The Terraform billing budget and notification route must exist before provisioning. A budget
  alert is not a hard cap: the platform owner checks actual/forecast spend at the beginning and end
  of every operating window.
- LLM calls use Postgres budget mode with an approved daily token cap. Exceeding either the
  infrastructure forecast or LLM cap stops new runs pending cost-owner approval.
- Default environment posture is ephemeral/time-boxed. Teardown follows
  [stage operating policy](runbooks/stage_operating_policy.md); the pilot owner records any
  exception and expiry.

## Data and privacy contract

The [PR2.4 policy](data_retention_privacy_pr24.md) is binding.

| Data category | Pilot handling |
|---|---|
| Telemetry/incident inputs | Synthetic or explicitly approved minimum fields; encrypted and purpose-limited |
| Prompts/model responses | Capture off by default; time-boxed debugging requires Security approval and deletion |
| Logs/traces/metrics | IDs, counts, outcomes, and bounded metadata only; no raw payloads or secrets |
| Audit/approvals | Verified principal, durable state, access-controlled retention |
| Evidence/publication | Sanitized hashes, IDs, timings, and decisions; public edition passes PR3.5 redaction |

Default retention targets are 30 days for logs/traces, 90 days for metrics, and 365 days for audit,
approval, release-decision, and approved eval records. Provider limitations and deletion/expiry
proof must be attached to PR3.4.

## Allowed actions and safety limits

| Capability | Pilot status | Control |
|---|---|---|
| Ingest approved telemetry fixture/feed | Allowed | Authenticated source, schema validation, rate limit |
| Read telemetry/KB and generate report | Allowed | MCP allowlist, evidence policy, output schema |
| Escalate to human | Allowed and preferred on uncertainty | Escalation packet and audit event |
| Create ticket or GitOps pull request | Disabled by default | May be enabled only after PR23-002/003 closure, OPA allow, verified approver, and idempotent claim |
| Direct cluster/config mutation by agent | Prohibited | Human operator follows audited runbook |
| Platform remediation/replay | Read-only recommendations | Separate authenticated approval is required for future writes |
| Spacecraft/ground-segment command | Prohibited | Outside project and pilot scope |

OPA deny/error remains fail-closed. Budget denial, missing evidence, prompt-injection detection,
provider failure, and unavailable approvals must escalate without executing a restricted action.

## External integration contracts

| Integration | Pilot contract | Admission gate |
|---|---|---|
| Telemetry source | Authenticated HTTPS/NATS adapter; approved schema, rate and data owner | Synthetic/sanitized sample, source auth, replay/dedupe proof |
| Ticketing | Dedicated pilot project; minimum metadata; no raw confidential payload | Service identity, least privilege, rollback/delete test |
| GitOps repository | Dedicated repo/path; agent creates PR only; protected branch applies changes | GitOps MCP confinement, branch protection, human review |
| Identity provider | OIDC/IAP-equivalent verified principal and approver role | Closes PR23-002; negative authorization test |
| Approval store | Transactional Postgres state and unique idempotency claim | Closes PR23-003; concurrent one-side-effect drill |
| LLM provider | Approved account/model/region, DPA/security review, no training where required | Key in GSM, egress allowlist, budget and outage tests |
| Observability | Managed Logging/Trace and Prometheus-compatible metrics | Retention, authorized query, denied query, deletion/expiry drill |
| Postgres | Managed HA service with PITR/backups | RPO/RTO and restore evidence for the pilot service |

Any integration absent from this table is denied until added through a reviewed change.

## Release, rollback, stop, and teardown

Promotion requires matching passing PR3.1 static and stage evidence for the immutable release,
manual pilot-owner approval, security sign-off/waivers, backup status, and no expired exception.

Immediate rollback criteria:

- health or availability gate fails after promotion;
- error rate exceeds 5% or p95 run latency exceeds 60 seconds for two evaluation windows;
- safety/evidence/OPA gate regresses;
- queue/DLQ cannot be bounded;
- unapproved backend, model, data source, or configuration is observed.

Immediate pilot stop criteria:

- any unsafe or unauthorized action;
- suspected secret, personal-data, or confidential-payload exposure;
- audit/approval integrity cannot be trusted;
- PR23-002/003 compensating control fails;
- cost forecast exceeds the approved limit without owner approval;
- a SEV-1 cannot be contained within the incident plan.

Rollback follows [Kubernetes rollback](runbooks/k8s_rollout_rollback.md). Incident response follows
[PR3.2](runbooks/incident_oncall_game_day_pr32.md). Teardown removes workloads, load balancers,
disks, registry artifacts, temporary secrets, and stage/prod compute; only explicitly approved
budget/notification resources may remain. The owner verifies zero orphan resources.

## Success metrics

Measured only during staffed pilot windows:

- API availability at least 99%;
- p95 run duration at most 60 seconds;
- run error rate at most 5%;
- zero unsafe or unauthorized actions;
- zero sustained OPA/evidence-policy violations;
- 100% of restricted attempts denied or linked to a verified approval decision;
- 100% of completed reports contain required evidence;
- no unowned DLQ backlog at window close;
- rollback and incident acknowledgement meet the PR3.2 targets;
- spend remains within approved infrastructure and LLM limits;
- operator feedback records usefulness and false-escalation observations for every session.

## Pilot exit criteria

Successful completion requires:

1. all hard metrics above pass for the full pilot;
2. no unresolved SEV-1 and every SEV-2 has an owner and accepted remediation date;
3. backup/restore, secret rotation, release gate, rollback, managed observability, retention, and
   deletion evidence remain valid;
4. Security confirms approval identity/atomicity and disposition of PR23-004 and PR23-005;
5. operators complete the runbook and feedback review;
6. cost owner confirms actual spend and removes orphan resources;
7. PR3.4 records the next decision: stop, extend under the same scope, or approve a separately
   reviewed production expansion.

Failure to meet these criteria returns the system to isolated stage/reference status. It does not
silently extend the pilot.

## Legal/compliance assumptions and non-goals

This plan is technical guidance, not legal advice. The pilot owner must obtain applicable provider,
data-processing, regional, licensing, export-control, employment/privacy, and customer approvals
before admitting non-synthetic data.

Non-goals:

- real spacecraft or ground-segment command/control;
- unattended L3/L4 autonomy or 24/7 mission operations;
- medical, safety-of-life, classified, or export-controlled workloads;
- public multi-tenant access;
- direct autonomous infrastructure remediation;
- claiming regulatory certification, disaster recovery, or production scale beyond measured pilot
  evidence;
- enabling GPU/multi-cloud paths without their separate promotion and cost gates.

## PR3.4 sign-off checklist

- [ ] Exact pilot dates, timezone, named role roster, contacts, and support hand-off are in the
  private change record.
- [ ] PR23-002/003 are closed or have explicit time-boxed waivers and compensating controls.
- [ ] PR23-004/005 have accepted dispositions.
- [ ] Managed trace/log retention, authorized/denied query, and deletion/expiry evidence pass.
- [ ] Integration credentials, identities, regions, retention, and least privilege are approved.
- [ ] Matching PR3.1 release evidence and PR3.2 incident/rollback evidence are attached.
- [ ] Budget values, forecast, teardown owner, and stop authority are recorded.
- [ ] Production readiness decision explicitly states `No-go`, `Conditional go`, or `Go`.
