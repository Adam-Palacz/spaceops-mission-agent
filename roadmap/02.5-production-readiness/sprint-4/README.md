# PR4 - Production Admission Remediation

**Goal:** resolve or explicitly disposition every blocker from the 2026-11-23 No-go decision and
produce the evidence required for a new production-pilot admission review.

## Outcomes

- Approval identity and role come from a verified credential, with negative authorization proof.
- Approved work is transactionally claimed and produces at most one downstream side effect.
- Audit and MCP trust boundaries are accepted for the proposed pilot topology.
- Managed logs/traces have proven retention, access denial, query, and deletion/expiry behavior.
- Managed Postgres HA/PITR and live paging are exercised with measured evidence.
- A new review records Go, Conditional go, or No-go without inheriting approval from task status.

## Definition of done

- [ ] PR4 board is complete.
- [ ] PR23-002 and PR23-003 are closed or have approved, time-boxed waivers.
- [ ] PR23-004 and PR23-005 have explicit remediation or scoped acceptance decisions.
- [ ] Managed observability, Cloud SQL HA/PITR, and live paging evidence exists.
- [ ] The private pilot record has named accountable owners and operating constraints.
- [ ] A new production-admission review records the decision and supersedes the 2026-11-23 review.

## Operating constraints

- Use synthetic data and the smallest practical temporary cloud resources until a new review grants
  pilot admission.
- Tear down temporary paid resources immediately after evidence capture.
- Never commit credentials, contact details, cloud project identifiers, or unredacted console
  screenshots.
- A completed remediation task does not itself change the current No-go decision.

See [BOARD.md](BOARD.md). The 2026-11-23 [sprint review](SPRINT_REVIEW.md) pauses close-out
until the network hold and the remaining acceptances can be recorded.
