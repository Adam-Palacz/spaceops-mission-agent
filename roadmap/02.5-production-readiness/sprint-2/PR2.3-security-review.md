# PR2.3 - Security review: OPA, approvals, MCP, audit

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Review date** | 2026-09-26 |
| **Decision** | Review complete; production-pilot no-go while PR23-002/003 remain open |
| **Evidence** | [Security review](../../../docs/security_control_review_pr23.md), [JSON evidence](evidence/PR2.3-security-review-2026-09-26.json) |

## Description

Perform a focused security review of the control boundaries that make SpaceOps safe: no shell
access, MCP-only tools, OPA fail-closed policy, authenticated approvals, append-only audit, LLM
budget enforcement, and platform ops gating.

## Requirements

- Review OPA fail-closed behavior under down, timeout, malformed policy response, and deny.
- Review approval authn/authz, idempotency, and audit attribution.
- Review MCP tool allowlist and argument validation.
- Review append-only audit behavior and tamper-evidence limitations.
- Review platform ops triage `--apply` gating.
- Review LLM gateway budget/circuit breaker/fallback controls.

## Checklist

- [x] Security review checklist added.
- [x] Findings recorded with severity and owner.
- [x] At least one negative test/drill per boundary.
- [x] Critical/high issues fixed or explicitly block phase closure.
- [x] Accepted risks queued as mandatory PR3.4 phase-review inputs.

## Test requirements

- Focused tests for security boundary regressions.
- Documentation evidence for accepted risks.

## Closure note

PR2.3 is Done because the review, remediation, negative tests, findings, owners, and disposition
are complete. This status does not mean production-pilot approval.

The review fixed PR23-001, which allowed GitOps MCP callers to select an arbitrary filesystem
root. PR23-002 (verified approval principal/role) and PR23-003 (atomic approval execution claim)
remain High findings and explicitly block phase closure. PR23-004 and PR23-005 are accepted only
for isolated stage/lab operation and require a decision in PR3.4.

Focused verification:

```text
pytest tests/test_production_readiness_pr23_security_review.py \
       tests/test_opa_client.py tests/test_act_opa_policy.py \
       tests/test_api.py tests/test_audit_log.py \
       tests/test_platform_ops_ps78.py \
       tests/test_llm_cost_guardrails_ps56.py \
       tests/test_llm_backend_resilience_ps54.py -q
```

