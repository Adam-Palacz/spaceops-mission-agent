# Evidence, safety, and evaluation

## Why

Plausible prose is not an operational result. The system needs measurable evidence coverage,
deterministic safety gates, regression fixtures, and an audit trail that explains why a run acted,
stopped, or escalated.

## Decision

SpaceOps treats evidence and safety as hard gates. Reports use structured envelopes, citations when
available, and explicit escalation reasons. Prompt-injection checks, OPA, approval, budget controls,
and MCP allowlists form independent layers. Quality signals that cannot safely block a merge remain
clearly marked as soft.

## Implementation

- The [CI gating policy](../../runbooks/ci_gating_policy.md) separates hard and soft gates.
- [Prompt-injection controls](../../prompt_injection_threat_model.md) sanitize untrusted content.
- [Behavior metrics](../../behavior_metrics.md) track escalation, evidence, latency, and outcomes.
- Golden replay detects structured-output drift.
- Semantic evals test evidence and citation behavior without requiring a live LLM.
- Backend parity prevents invalid GPU/fallback arms from being promoted.

## Verification

The release gate runs lint, typing, the complete pytest suite, dedicated approval/OPA checks, Helm
stage/prod validation, and migration SQL generation. Live stage adds health, ingestion, both demo
scenarios, queue readiness, a zero-DLQ threshold, and rollback snapshots.

## Evidence

Machine-readable results are indexed in the appendix and hashed into each generated book manifest.
The canonical security assessment is
[PR2.3](../../security_control_review_pr23.md).

## Limitations

Application audit is append-only but not tamper-evident. CI safety results do not replace a live
penetration test. Stage Scenario A may contain evidence without citation references when the KB
index is not available.

## Lessons learned

Tests should verify the failure mode, not merely the successful response. The strongest controls in
this project assert that no approval is created on OPA failure, no fallback bypasses a budget deny,
and no restricted side effect occurs after a failed gate.
