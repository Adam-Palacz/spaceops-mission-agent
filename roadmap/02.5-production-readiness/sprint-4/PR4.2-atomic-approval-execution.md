# PR4.2 - Atomic approval execution and idempotency

| Field | Value |
|-------|-------|
| **Status** | In progress |
| **Closes** | PR23-003 |
| **Owner** | API / Data |
| **Depends on** | PR4.1 |

## Description

Make execution claiming durable and atomic so concurrent API replicas cannot execute the same
approved operation more than once.

## Requirements

- Store approval and execution state in Postgres rather than process-local memory.
- Claim eligible work in one transaction with a unique idempotency key and explicit state
  transition.
- Define retry, lease/timeout recovery, terminal failure, and operator reconciliation behavior.
- Couple the durable claim to downstream idempotency or an outbox pattern where a database
  transaction cannot include the side effect.
- Preserve immutable attribution to the verified principal introduced by PR4.1.
- Expose metrics and audit events for claims, duplicates, retries, stuck work, and reconciliation.

## Checklist

- [x] Schema and migration are implemented.
- [x] Transactional claim and idempotency behavior are implemented.
- [x] Crash/retry/reconciliation behavior is documented.
- [x] Multi-replica concurrency test proves one winning claim.
- [x] Downstream side-effect test proves at-most-once externally visible execution.
- [ ] PR23-003 closure or waiver is approved by Security and the pilot owner.

## Test requirements

- Concurrent replicas race for one approved action; exactly one claim succeeds.
- Duplicate requests with the same key do not create another side effect.
- Crash after claim and before completion follows the documented recovery policy.
- Transaction rollback leaves no false successful execution.
- Metrics and audit records identify duplicate suppression without leaking sensitive payloads.

## Done gate

Do not mark Done from a mocked repository test alone. The acceptance evidence must use Postgres and
at least two concurrent execution contenders.

## Implementation evidence

- [Atomic execution design](../../../docs/approval_atomic_execution_pr42.md)
- [Postgres concurrency drill](evidence/PR4.2-postgres-claim-drill-2026-11-23.json): eight
  contenders, one winning claim, one externally visible side effect, no repeat claim.
- Alembic migration `20261123_0004` and runtime store use a unique idempotency key, row lock, claim
  token, worker fence, lease, attempts, and durable completion state.
- The GitHub GitOps path returns an existing PR for a replayed deterministic approval branch.

The implementation and executed Postgres evidence are complete. Named Security/pilot-owner
acceptance remains outstanding, so PR23-003 and this task remain open.
