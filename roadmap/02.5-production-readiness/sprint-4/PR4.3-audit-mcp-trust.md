# PR4.3 - Audit integrity and MCP workload trust

| Field | Value |
|-------|-------|
| **Status** | In progress |
| **Addresses** | PR23-004, PR23-005, PR23-006 |
| **Owner** | Platform / Security |
| **Depends on** | PR4.1, PR4.2 |

## Description

Close the remaining security-review decisions for durable audit integrity, authenticated MCP
callers, and the platform-operation write boundary.

## Requirements

- Export audit records to durable, access-controlled storage with provider immutability controls or
  independently verifiable hash/signature chaining.
- Monitor export failures, retention, integrity verification, and unauthorized access.
- Authenticate and authorize MCP workload identity with workload identity or mTLS when the pilot
  topology crosses the currently accepted single-namespace boundary.
- Prove unauthorized and cross-workload MCP calls are denied.
- Keep platform operations read-only; if any write path is proposed, require authenticated
  approval, policy scope, idempotency, and audit before enabling it.
- Record explicit accepted/remediated dispositions for PR23-004, PR23-005, and PR23-006.

## Checklist

- [x] Audit integrity architecture and retention are documented.
- [ ] Audit export/integrity controls and failure alerting are exercised.
- [x] MCP pilot topology and caller-authentication boundary are documented.
- [ ] Unauthorized MCP and audit-access tests pass on a live mesh.
- [x] Platform operations remain read-only or pass the full write-control gate.
- [ ] Security and pilot owner sign off the finding dispositions.

## Test requirements

- Audit mutation/deletion attempt is denied or detected.
- Missing/corrupt audit segment produces an integrity failure and operator signal.
- Unauthorized workload, wrong identity, and cross-namespace MCP calls fail.
- Authorized workload can call only allowlisted tools and validated arguments.
- Platform write attempt remains unavailable unless all required controls are active.

## Done gate

Do not treat namespace isolation alone as sufficient if the selected pilot exposes MCP across a
namespace or trust boundary. The accepted topology and compensating controls must be explicit.

## Implementation evidence

- [Audit and MCP trust design](../../../docs/audit_mcp_trust_pr43.md)
- [Boundary drill](evidence/PR4.3-security-boundary-drill-2026-11-23.json): signed-chain
  verification and tamper detection passed; production Istio policy rendered successfully.
- Production Helm config enables strict mTLS and service-account-principal authorization for every
  MCP service. API and agent-worker are the only allowed callers.
- Platform operations remain read-only.

Live Istio allow/deny evidence, managed audit export under PR4.4, and named finding dispositions
remain outstanding. PR23-004/005 therefore remain open and this task stays In progress.
