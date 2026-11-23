# PR4 Sprint Review / Pause Note

**Review date:** 2026-11-23
**Verdict:** Paused. PR4 is not closed, and the production-admission decision remains
**No-go - reference/stage only**.

This note records the evidence captured so far and the point at which close-out stops. It does not
waive any open gate and it does not mark the sprint Done.

## Task status

| Task | Status | Evidence |
|---|---|---|
| PR4.1 approval identity | In progress | [OIDC drill](evidence/PR4.1-oidc-drill-2026-11-23.json). Technical verification is recorded; Security and pilot-owner acceptance is not. |
| PR4.2 atomic approval | In progress | [Postgres claim drill](evidence/PR4.2-postgres-claim-drill-2026-11-23.json). One winning claim is proven; PR23-003 acceptance is not. |
| PR4.3 audit and MCP trust | In progress | [Security-boundary drill](evidence/PR4.3-security-boundary-drill-2026-11-23.json). Signed audit and static mesh policy exist; live mesh allow/deny and sign-off do not. |
| PR4.4 managed logging/tracing | Done | [Managed observability drill](evidence/PR4.4-managed-observability-2026-11-23.json) |
| PR4.5 managed Postgres HA/PITR | In progress | [HA/PITR drill](evidence/PR4.5-cloud-sql-ha-pitr-2026-11-23.json). Failover, PITR, and IAM denial passed. The empty network remains until the provider hold. |
| PR4.6 live paging | In progress | [Paging drill](evidence/PR4.6-live-paging-2026-11-23.json). One page was delivered, acknowledged, and resolved. Escalation, the Alertmanager sender, and key revocation remain open. |
| PR4.7 admission re-review | Todo | Not started. A repeated No-go would not close the open gates. |

## Why close-out stops here

The remaining work is no longer product implementation. Three facts make a honest Done impossible
today:

1. **The Cloud SQL network cannot be deleted yet.** Google keeps the Private Service Access
   producer subnet for up to four days after the instance is removed. The empty VPC, reserved
   range, and service connection stay until a retry after **2026-11-27 13:04 UTC** (14:04 Europe/Warsaw).
   The database itself is already gone and is not billing. PR4.5 stays In progress until that
   inventory check passes.
2. **PR4.1, PR4.2, and PR4.3 still need a named acceptance.** The drills exist. Closing them
   requires a Security and pilot-owner signature, or a time-boxed waiver with an owner, compensating
   control, expiry, monitoring, and rollback. That signature was not given in this session.
3. **PR4.6 cannot show escalation to a second person on this account.** The trial has one on-call
   user and one policy level. The live page was sent directly to the provider API, not by
   Alertmanager, and a key checked after the temporary service was deleted still returned HTTP 202.
   Closing BL-006 needs a second responder and a repeated drill, or the same kind of expiring
   exception.

PR4.7 runs only after those dispositions. Writing it now would repeat the current No-go without
removing the blockers.

Further paid cloud setup is not justified while the next required action is a calendar retry plus
a human acceptance. Local and synthetic NG1-NG2 work may continue. A production pilot may not.

## Return point

Resume PR4 close-out on or after **2026-11-27 14:04 Europe/Warsaw**:

1. Destroy the residual VPC, address, and service connection. Recheck the inventory. Close PR4.5
   only if that check is clear.
2. Record the named acceptance for PR4.1-PR4.3 and PR4.6, or execute the missing live mesh and
   second-responder paging drills.
3. Write PR4.7. The decision may remain No-go. The phase closes only when every open item is
   evidenced or explicitly accepted with an owner and an expiry.

Until that return, this sprint stays open and the 2026-11-23 No-go stays in force.
