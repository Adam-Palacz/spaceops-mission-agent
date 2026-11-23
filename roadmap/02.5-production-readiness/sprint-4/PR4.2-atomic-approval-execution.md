# PR4.2 - Atomic approval execution and idempotency

| Field | Value |
|-------|-------|
| **Status** | Todo |
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

- [ ] Schema and migration are implemented.
- [ ] Transactional claim and idempotency behavior are implemented.
- [ ] Crash/retry/reconciliation behavior is documented.
- [ ] Multi-replica concurrency test proves one winning claim.
- [ ] Downstream side-effect test proves at-most-once externally visible execution.
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
