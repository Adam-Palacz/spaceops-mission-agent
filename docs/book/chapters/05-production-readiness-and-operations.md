# Production readiness and operations

## Why

Production readiness is a decision about bounded risk, ownership, and recovery—not a synonym for
feature completion. The system must be operable by people under failure and must state what it is
not ready to do.

## Decision

The production-readiness track sits between Production Scale and deeper L3/L4 autonomy. It requires
observability, durability, secret rotation, security review, release gates, incident practice, and
a bounded pilot charter. The current decision is **No-go: reference/stage only**.

## Implementation

- PR1 established monitoring, SLOs, stage policy, and soak/failure proof.
- PR2 established restore, live secret rotation, security findings, and privacy/retention policy.
- PR3 established blocking release gates, an API-outage rollback game day, and the
  [production pilot plan](../../production_pilot_plan_pr33.md).
- The [incident/on-call runbook](../../runbooks/incident_oncall_game_day_pr32.md) defines severity,
  roles, escalation, communications, and follow-up ownership.

## Verification

The PR3.2 game day created a new Helm revision, scaled API replicas to zero, recorded a synthetic
availability signal, captured triage/escalation, rolled back to the known-good revision, and
restored health. The release gate passed on a temporary GKE stage and teardown checks found no paid
workload resources afterward.

## Evidence

The authoritative decision is the
[Production Readiness Phase Review](../../../roadmap/02.5-production-readiness/PHASE_REVIEW.md).
It imports every PR23 security finding, managed observability gates, owners, re-review criteria, and
Next-Gen dependency rules.

## Limitations

PR23-002 and PR23-003 remain open High blockers. Managed Logging/Trace access, retention, and
deletion proof is absent. Managed Postgres HA/PITR and real paging delivery remain unproven. No
named private pilot roster, dates, contacts, or legal approvals exist.

## Lessons learned

An explicit No-go is a useful engineering output. It prevents completed implementation tasks from
being misrepresented as permission to admit production data or increase autonomy.
