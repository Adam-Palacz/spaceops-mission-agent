# Audit integrity and MCP workload trust (PR4.3)

## Audit integrity decision

Audit entries now form a sequence-numbered SHA-256 chain. Every entry contains the previous hash
and its own canonical hash. Stage/prod can additionally sign each entry with an HMAC key delivered
through the existing External Secrets/GSM path. Verification detects mutation, deletion/reordering
inside the chain, an incorrect signing key, and malformed records.

The signing key is not committed or written to evidence. PR4.4 must export the signed stream and
root hashes to access-controlled managed storage; a local chain alone cannot stop an administrator
from deleting the complete file.

## MCP workload identity decision

Production MCP services use Istio workload identity:

- sidecars are injected into API, agent-worker, and MCP pods;
- each MCP workload requires `STRICT` mTLS;
- an `AuthorizationPolicy` allows only the API and agent-worker Kubernetes service-account
  principals in the release namespace;
- other service accounts, namespaces, plaintext clients, and external callers are denied.

The application retains fixed named MCP methods and argument validation. Workload identity protects
the transport caller; it does not expand the tool allowlist.

## Platform operations disposition

Platform operations remain read-only. `--apply --i-approve` still executes no mutation.
PR23-006 is accepted only under that invariant. Introducing any write path reopens the finding and
requires the verified approval identity, Postgres execution claim, OPA scope, downstream
idempotency, and signed audit controls.

## Verification

[PR4.3 evidence](../roadmap/02.5-production-readiness/sprint-4/evidence/PR4.3-security-boundary-drill-2026-11-23.json)
records a valid three-entry signed chain, successful tamper detection, static MCP identity-policy
checks, and disabled platform writes. Helm lint and production rendering produce four strict-mTLS
peer policies and four caller authorization policies.

## Remaining admission work

- Deploy the policies on a stage cluster with Istio and prove API/worker allow plus unauthorized
  service-account and cross-namespace denial.
- Complete durable managed audit export and access/retention proof under PR4.4.
- Record named Security and production-pilot owner dispositions for PR23-004 through PR23-006.

PR4.3 therefore remains **In progress**.
