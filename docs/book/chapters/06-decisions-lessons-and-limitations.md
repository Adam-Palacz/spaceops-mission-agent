# Decisions, trade-offs, lessons, and current limitations

## Why

Maintainers returning to a project need more than the final architecture. They need to understand
which alternatives were rejected, which failures changed the design, and which claims remain
unsupported.

## Decision

The project consistently prefers bounded, inspectable mechanisms:

- named MCP tools instead of agent shell access;
- fail-closed OPA and evidence checks instead of optimistic execution;
- human approval for restricted actions;
- Postgres durability instead of process-local state for shared controls;
- ephemeral stage plus reproducible teardown instead of an idle demo cluster;
- canonical Markdown/evidence plus generated books instead of manually edited PDFs.

## Implementation

ADRs record environment, queue, checkpoint, LLM backend, Helm, secrets, GitOps, telemetry, and
multi-cloud decisions. Sprint reviews record what actually passed and what changed during live
work. Machine-readable evidence records timings, statuses, hashes, and outcomes.

## Verification

Rejected assumptions were tested directly:

- dependency outages produce escalation;
- OPA errors deny;
- budget exhaustion cannot fall back;
- backup data is restored and counted;
- rotated credentials invalidate prior access;
- release failure blocks promotion;
- rollback restores health;
- teardown leaves no workload resources.

## Evidence

Use the [ADR index](../../adr/README.md), sprint reviews under
[roadmap](../../../roadmap/README.md), and the generated evidence manifest. Generated prose is never
the sole evidence for a technical claim.

## Limitations

Current limitations include shared-key approval identity, non-atomic multi-replica approval
execution, non-tamper-evident audit storage, cluster-trusted MCP callers, ephemeral trace storage,
no real paging delivery, incomplete managed HA/PITR proof, and no production-pilot approval.

The project also does not prove real spacecraft integration, safety-of-life operation, public
multi-tenancy, regulatory certification, 24/7 staffing, or unattended L3/L4 autonomy.

## Lessons learned

1. A live drill should start with cleanup ownership and a cost limit.
2. A successful HTTP response is weaker than semantic evidence assertions.
3. Rollback procedures must match provider semantics, not assumptions.
4. Security findings remain blockers even when their review task is Done.
5. Synthetic/local game days are valuable but cannot prove external paging.
6. Publication needs automated redaction plus human review; neither alone is sufficient.
7. Honest boundaries make future autonomy safer and easier to evaluate.
