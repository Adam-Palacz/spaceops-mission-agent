# PR2.3 Security Control Review

**Review date:** 2026-09-26  
**Scope:** OPA, approvals, MCP, audit, platform operations, and LLM gateway  
**Decision:** review complete; production-pilot phase closure remains blocked by PR23-002 and
PR23-003.

## Executive summary

The reviewed controls provide a credible stage/lab safety baseline. OPA fails closed, the agent
uses named MCP calls rather than arbitrary shell execution, LLM budget denial cannot be bypassed
through fallback, and platform operations remains read-only even when its acknowledgement flag is
present.

The review found one High issue in GitOps MCP argument validation and fixed it in this change.
Two other High findings remain open: approval identity is based on a shared key plus a
caller-supplied attribution header, and the file-backed approval transition is not an atomic,
multi-replica execution claim. These findings do not invalidate local demonstrations, but they
block a production-pilot `go` decision until fixed or formally waived by the Security and SRE
owners in PR3.4.

## Method and evidence

This was a source-assisted review with focused negative tests. It did not include penetration
testing of a live GKE deployment.

- OPA: simulated deny, timeout, connection failure, HTTP 500, malformed response, and missing
  result.
- Approvals: unauthenticated approve/reject, idempotent sequential replay, execution failure, and
  audit attribution.
- MCP: reviewed the fixed client-side tool names and server schemas; attempted GitOps writes
  outside `ops-config`, unsafe branch names, traversal, empty paths, excessive file count, and
  oversized content.
- Audit: verified application code only appends and documented host-level tamper limitations.
- Platform operations: attempted `--apply` without acknowledgement and confirmed that the current
  MVP executes no writes even with acknowledgement.
- LLM gateway: forced budget exhaustion, GPU circuit open, provider timeout/error, and fallback;
  budget denial never falls back to another backend.

Machine-readable evidence is stored in
`roadmap/02.5-production-readiness/sprint-2/evidence/PR2.3-security-review-2026-09-26.json`.

## Boundary results

### OPA fail-closed

**Result: Pass for the reviewed boundary.**

`apps.agent.opa_client.opa_allow` returns `False` for network errors, timeouts, non-success HTTP
responses, non-JSON/malformed bodies, missing results, explicit deny, and an open circuit. The Act
node escalates with `policy_deny` and does not create an approval request when OPA does not allow
the step.

The Rego policy defaults to deny and only admits `change_config` and `restart_service`. It remains
a deliberately small policy, not semantic proof that arbitrary free text is safe.

### Approval authentication, authorization, idempotency, and attribution

**Result: Conditional; two High findings block production-pilot closure.**

The endpoints reject absent or incorrect credentials and sequential retries do not re-execute an
already-decided request. Approve/reject decisions and restricted execution outcomes are audited.

The current shared `APPROVAL_API_KEY` authenticates a client but does not establish an individual
principal or role. `X-Approval-By` is supplied by that client and therefore is attribution
metadata, not verified identity. In addition, the file-backed pending-to-approved transition is
not an atomic execution claim across concurrent processes or API replicas. See PR23-002 and
PR23-003.

### MCP tool and argument boundary

**Result: Pass with residual deployment risk.**

The agent client exposes only named helpers for telemetry, runbook/postmortem search, ticket
creation, and GitOps PR creation. There is no generic model-controlled tool-name dispatch and no
agent shell helper. FastMCP derives input schemas from typed function signatures.

This review fixed GitOps `repo_path` confinement and added branch, file-count, path, and content
size validation. GitOps output remains a pull request path; it does not directly apply a cluster
change.

MCP services do not currently authenticate callers at the application layer. Stage relies on
namespace isolation and NetworkPolicy. This is accepted for the current stage/lab scope and must
be revisited before exposing MCP services outside the trusted cluster network.

### Append-only audit and tamper evidence

**Result: Pass for application append-only semantics; not tamper-evident.**

The audit module opens its NDJSON file in append mode and exposes no update or delete API.
Arguments are represented by a canonical SHA-256 hash and short error messages avoid stack trace
leakage.

The file has no hash chain, signature, immutable object lock, external replication, or trusted
timestamp. A host administrator or compromised workload with filesystem access can alter or
delete historical records without detection. The current implementation must be described as
application append-only, not immutable or tamper-proof.

### Platform operations gating

**Result: Pass for the read-only MVP.**

`--apply` without `--i-approve` exits with code 2. Supplying both flags still reports
`write_actions_executed: false` and `apply_allowed: false`; no mutation implementation exists.
The acknowledgement flag is not authentication and must not become the sole gate when write
actions are added.

### LLM budget, circuit breaker, and fallback

**Result: Pass for the reviewed boundary.**

Process and Postgres budget modes deny calls after the configured cap. A budget denial is terminal
and cannot trigger GPU/OpenAI cross-backend fallback. GPU health and runtime failures open the
circuit and may fall back to OpenAI only when configured credentials are available. Recovery is
tested through the half-open path.

## Findings

### PR23-001 — GitOps MCP accepted arbitrary filesystem roots

- **Severity:** High
- **Status:** Remediated in PR2.3
- **Owner:** Agent Platform
- **Evidence:** `apps/mcp/gitops_server/main.py` and
  `tests/test_production_readiness_pr23_security_review.py`
- **Resolution:** `repo_path` is confined to this repository's `ops-config`; requests also enforce
  a safe `agent/` branch format, 1-20 files, relative non-traversing paths, and a 256 KiB per-file
  content limit.

### PR23-002 — Approval principal and role are not cryptographically established

- **Severity:** High
- **Status:** Open; blocks production-pilot phase closure
- **Owner:** Security / API
- **Required resolution:** replace the shared-key identity model with an authenticated principal
  from the ingress/IdP or a key-to-principal mapping, enforce an approver role, and derive audit
  identity from the verified credential. Do not trust `X-Approval-By` from an untrusted client.
- **Acceptance authority:** Security owner and production-pilot owner in PR3.4.

### PR23-003 — Approval execution claim is not atomic across replicas

- **Severity:** High
- **Status:** Open; blocks production-pilot phase closure
- **Owner:** API / Data
- **Required resolution:** move approval state to Postgres and claim execution with a transaction,
  unique idempotency key, and durable execution state. Add a concurrent approval drill proving one
  downstream side effect.
- **Acceptance authority:** Security owner and production-pilot owner in PR3.4.

### PR23-004 — Audit storage is not tamper-evident

- **Severity:** Medium
- **Status:** Accepted for stage/lab; open for production pilot
- **Owner:** SRE / Security
- **Required resolution:** export audit events to access-controlled durable storage and add hash
  chaining/signing or provider immutability controls with retention monitoring.

### PR23-005 — MCP caller trust depends on cluster isolation

- **Severity:** Medium
- **Status:** Accepted for isolated stage
- **Owner:** Platform / Security
- **Required resolution:** before external or cross-namespace access, add workload identity or mTLS
  authorization per MCP service and test unauthorized calls.

### PR23-006 — Platform acknowledgement is not authorization

- **Severity:** Low
- **Status:** Accepted while platform ops is read-only
- **Owner:** Platform
- **Required resolution:** any future write implementation must use authenticated approvals,
  policy checks, scoped actions, idempotency, and audit; `--i-approve` alone is insufficient.

## Production-readiness handoff

PR3.4 must import all open findings above. A production-pilot decision is `No-go` while PR23-002
or PR23-003 remains open, unless both receive explicit, time-boxed waivers with compensating
controls, named owners, and deadlines. PR23-004 and PR23-005 require an explicit acceptance or
remediation decision in the same review.

## Verification map

- OPA: `tests/test_opa_client.py`, `tests/test_act_opa_policy.py`
- Approvals: `tests/test_api.py`
- MCP: `tests/test_production_readiness_pr23_security_review.py`
- Audit: `tests/test_audit_log.py`
- Platform ops: `tests/test_platform_ops_ps78.py`
- LLM controls: `tests/test_llm_cost_guardrails_ps56.py`,
  `tests/test_llm_backend_resilience_ps54.py`
