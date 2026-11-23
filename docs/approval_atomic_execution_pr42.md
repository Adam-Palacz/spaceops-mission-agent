# Atomic approval execution and idempotency (PR4.2)

## Decision

Production approvals and execution state are stored in Postgres. Approval and execution claiming
share one row lock and transaction. A unique idempotency key, claim token, worker identity, and
lease fence prevent concurrent API replicas from executing the same approval.

The local file store remains a compatibility mode for development only. The production Helm
overlay sets `APPROVAL_STORE_BACKEND=postgres`.

## State model

```text
pending approval
  -> approved + execution claimed
       -> succeeded
       -> failed -> explicit operator reconciliation -> pending execution
       -> expired lease -> reclaimed by one contender
  -> rejected
```

`SELECT ... FOR UPDATE` serializes the approval decision. The subsequent conditional update claims
only pending execution or an expired lease. Completion requires the same claim token and worker,
so a stale worker cannot overwrite the result of a newer claim.

## Downstream idempotency

The idempotency key is `approval:<approval-id>`. GitOps execution already derives a deterministic
branch from the approval ID. The GitHub API path now treats an existing branch with an existing PR
as a successful replay and returns that PR without writing another commit or creating another PR.

This protects the crash window where the external side effect succeeds but the API process exits
before recording completion. Future downstream action types must accept the same idempotency key or
use an outbox/receiver-side unique constraint before production enablement.

## Crash, retry, and reconciliation

- Crash before the side effect: the claim lease expires and one contender can reclaim it.
- Crash after the side effect: the deterministic downstream key returns the existing result.
- Executor returns failure: execution becomes `failed`, with a bounded error and result record.
- Operator retry: verify downstream state, then call the internal
  `requeue_failed_execution()` procedure; the next request creates a new fenced claim.
- Stale claim count, claim outcomes, and execution outcomes are exposed as Prometheus metrics.

## Verification

The live local-Postgres drill used eight simultaneous contenders. It recorded exactly one winning
claim, one externally visible synthetic side effect, one successful completion, and no claim on a
repeat request:

[PR4.2 Postgres claim evidence](../roadmap/02.5-production-readiness/sprint-4/evidence/PR4.2-postgres-claim-drill-2026-11-23.json).

The temporary container was removed after the drill. No GCP resource was created.

## Remaining admission work

The implementation and concurrency evidence are complete. A named Security and production-pilot
owner must accept the PR23-003 closure before PR4.2 can be marked Done.
