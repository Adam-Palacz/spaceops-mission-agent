# Incident, on-call, and game-day operations (PR3.2)

This runbook defines the production-pilot incident model, escalation roles, communication templates,
and repeatable game-day procedure. It complements the service-specific recovery runbooks; it does
not authorize unsafe mission actions.

## Severity and response targets

| Severity | Example | Acknowledge | Incident commander | Update cadence |
|----------|---------|-------------|--------------------|----------------|
| SEV-1 | Unsafe action executed or audit integrity lost | 5 min | Immediately | 15 min |
| SEV-2 | API unavailable, Postgres degraded, unbounded DLQ | 10 min | Within 15 min | 30 min |
| SEV-3 | Partial degradation with a safe workaround | 30 min | Optional | 60 min |

These are production-pilot targets, not claims of a staffed 24/7 service.

## Incident classes

| Class | Detection | Fail-safe expectation | First mitigation | Owner |
|-------|-----------|-----------------------|------------------|-------|
| API outage | `SpaceOpsApiUnavailable`, readiness/health failure | No new actions | Roll back release or restore replicas | Platform |
| Worker stuck | queue age, lease timeout, worker unavailable | Variant A jobs remain resumable; Variant B is N/A | Restart worker, reclaim lease | Mission agent |
| OPA unavailable | OPA scrape/decision errors | Restricted actions fail closed | Restore OPA; never bypass policy | Security |
| Postgres degraded | DB probe, latency/error alerts | Writes fail visibly; no fabricated success | Stop promotion, restore service/backup | Data |
| Queue/DLQ growth | NATS lag and `/dlq/telemetry` count | Preserve payload and evidence | Stabilize dependencies, controlled replay | Platform |
| LLM backend outage | provider errors and backend status | Escalate without unsafe fallback | Restore provider or approved backend | Mission agent |
| Budget cap hit | budget exception/metric | Stop model calls and escalate | Confirm cap; approve budget change separately | Cost owner |
| Unsafe-action regression | safety eval or audit finding | Block release and disable action path | Security escalation and rollback | Security |

Service procedures:

- [Queue/DLQ recovery](queue_dlq_recovery.md)
- [Kubernetes rollout/rollback](k8s_rollout_rollback.md)
- [Postgres backup/restore](postgres_backup_restore.md)
- [LLM backend rollout](llm_backend_rollout.md)
- [Guardrail triage](guardrails_quality_triage.md)

## On-call roles

- **Primary on-call:** acknowledges, gathers bounded evidence, starts the incident record, and performs
  safe runbook steps.
- **Incident commander (IC):** owns severity, decisions, timeline, hand-offs, and closure. The IC does
  not execute commands while coordinating a SEV-1/SEV-2.
- **Technical lead:** selects and validates mitigation/rollback for the affected component.
- **Security lead:** mandatory for unsafe-action, OPA, approval, secret, MCP-boundary, or audit events.
- **Communications lead:** publishes internal updates and prepares any external statement.
- **Scribe:** records timestamps, commands, decisions, evidence links, and follow-up owners.

One person may cover multiple roles in a lab drill, but the evidence must state that the roles were
simulated. Production-pilot contacts and paging destinations remain deployment configuration, not
public repository data.

## Escalation path

1. Primary on-call acknowledges and classifies the signal.
2. Declare SEV-1 immediately for unsafe action or audit integrity loss; otherwise use impact.
3. Assign IC and scribe for every SEV-1/SEV-2.
4. Page the component owner; add security for every safety/control-plane incident.
5. Prefer rollback or fail-closed isolation over live debugging.
6. Escalate to pilot owner when the response target is missed or customer/mission scope is unclear.
7. Close only after health, safety gates, queues, and observability return to the expected state.

## Communication templates

Initial:

```text
[SEV-N] SpaceOps <component> incident
Detected: <UTC> | IC: <name/role> | Impact: <known/unknown>
Safety posture: <fail-closed / actions disabled / investigating>
Current action: <rollback/restore/triage>
Next update: <UTC>
```

Update:

```text
[SEV-N update] <UTC>
State: <investigating/mitigating/monitoring>
Evidence: <alerts, release ID, trace/run IDs>
Decision: <what and why>
Next action/update: <owner, UTC>
```

Resolved:

```text
[SEV-N resolved] <UTC>
Impact window: <start-end> | Mitigation: <summary>
Safety validation: <gate/evidence>
Follow-ups: <IDs, owners, dates>
Post-incident review: <date/link>
```

Never include secret values, customer data, raw prompts, or sensitive telemetry in status messages.

## Game-day procedure

The minimum PR3.2 drill uses local kind and an API outage. It creates a safe Helm revision, scales the
API deployment to zero, records a synthetic `APIUnavailable` signal, captures triage metadata, and
executes `helm rollback` to the known-good revision.

Prerequisites:

1. A disposable `kind-spaceops-dev` context is active.
2. The minimal SpaceOps Helm release is healthy in `spaceops-dev`.
3. No production traffic or cloud resources are involved.

Execute:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/pr32_game_day.ps1
```

Acceptance:

- baseline and restored `/health` return `ok`;
- zero available API replicas produce the synthetic incident signal;
- triage and simulated escalation appear in the timeline;
- Helm rollback restores the baseline revision and removes the game-day marker;
- every improvement has an ID, owner, status, and target/evidence.

The local synthetic signal proves the response path but not external paging delivery. A real
Alertmanager/PagerDuty or managed paging integration remains a production-pilot prerequisite.

## Evidence and follow-up policy

Store evidence under `roadmap/02.5-production-readiness/sprint-3/evidence/`. Evidence may include
timestamps, IDs, counts, hashes, statuses, and bounded non-sensitive diagnostics. It must not contain
secrets or raw sensitive payloads.

Every failed assertion or deferred operational control becomes either:

- a roadmap/backlog item with owner and target, or
- an explicit readiness-review risk acceptance with owner and expiry.

Use the [post-incident learning loop](post_incident_loop.md) for root cause and durable prevention.
