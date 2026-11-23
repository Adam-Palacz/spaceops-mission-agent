# PR4.1 - Verified approval identity and role authorization

| Field | Value |
|-------|-------|
| **Status** | In progress |
| **Closes** | PR23-002 |
| **Owner** | Security / API |
| **Depends on** | None |

## Description

Replace caller-supplied approval identity with an authenticated principal and an enforced approver
role derived from a cryptographically verified credential.

## Requirements

- Select and document the pilot identity provider and OIDC/JWT trust configuration.
- Verify issuer, audience, signature, expiry, and required claims; fail closed on any mismatch.
- Derive the audit principal from the verified credential, never from request body or trusted
  identity headers supplied by the caller.
- Enforce a dedicated approver role/scope and separation-of-duty rules for restricted actions.
- Define service-to-service and emergency-access behavior without adding a shared static bypass.
- Preserve only non-sensitive identity references in public evidence.

## Checklist

- [x] Threat model and identity trust decision are documented.
- [x] Authentication and approver-role authorization are implemented.
- [x] Audit attribution uses the verified principal.
- [x] Positive and negative authorization tests pass.
- [x] A live or production-equivalent token verification drill is recorded.
- [ ] PR23-002 closure or waiver is approved by Security and the pilot owner.

## Test requirements

- Valid approver succeeds within policy scope.
- Missing, expired, wrong-issuer, wrong-audience, malformed, and invalid-signature tokens fail.
- Authenticated non-approver and forged identity fields fail.
- Cross-role and self-approval attempts follow the documented separation-of-duty policy.
- Logs, traces, reports, and evidence contain no bearer token or sensitive claims.

## Done gate

Do not mark Done from unit tests alone. Production-equivalent credential verification, negative
authorization evidence, and an explicit PR23-002 disposition are required.

## Implementation evidence

- [Identity and authorization decision](../../../docs/approval_identity_authorization_pr41.md)
- [OIDC/JWKS drill](evidence/PR4.1-oidc-drill-2026-11-23.json): one valid approver allowed; wrong
  issuer, wrong audience, expired token, missing role, invalid signature, and malformed token
  denied.
- `tests/test_production_readiness_pr41_approval_identity.py` covers cryptographic claims,
  fail-closed behavior, API-key rejection in OIDC mode, and forged identity headers.

The selected provider is Google Cloud Identity Platform. External-provider stage configuration and
named Security/pilot-owner acceptance remain outstanding, so PR23-002 and this task remain open.
