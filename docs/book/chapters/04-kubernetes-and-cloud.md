# Kubernetes, cloud, and release engineering

## Why

A working local agent is not enough. Deployment must preserve isolation, secrets, migrations,
resource limits, rollback, observability, and cost controls across repeatable environments.

## Decision

Helm is the packaging boundary, with environment overlays for dev, stage, and prod. Terraform owns
GCP infrastructure. Stage is ephemeral by default. External Secrets Operator and Google Secret
Manager provide stage/prod secret delivery without service-account keys. GitOps is optional but
must not compete with imperative Helm for the same release.

## Implementation

- [ADR 0005](../../adr/0005-environment-strategy-dev-stage-prod.md) defines environment semantics.
- [ADR 0006](../../adr/0006-kubernetes-packaging-helm.md) defines Helm packaging.
- [Stage deploy](../../runbooks/gcp_stage_deploy.md) and
  [teardown](../../runbooks/gcp_stage_teardown.md) encode the cloud lifecycle.
- [Stage operating policy](../../runbooks/stage_operating_policy.md) defines ownership, drift,
  budget, recreate RTO, and teardown rules.
- [Secrets bootstrap](../../runbooks/k8s_secrets_bootstrap.md) separates local and managed paths.
- [Environment promotion](../../runbooks/environment_promotion.md) connects release gates to stage
  and prod.

## Verification

Helm templates/lint run in CI and release gates. Temporary GKE stages have proven full image
build/push, migration, health, Scenario A/B, monitoring, secret rotation, soak/failure behavior, and
cleanup. PR3.1 tied static and live results to one release fingerprint.

## Evidence

<!-- private:start -->
Private engineering evidence may retain sanitized project-scoped resource IDs and exact CLI hashes.
Public artifacts replace project identifiers and network addresses and do not retain cloud-console
screenshots.
<!-- private:end -->

The public-safe narrative relies on IaC, redacted CLI evidence, and JSON result records rather than
manual cloud-console screenshots.

## Limitations

The lab does not prove production regional capacity, managed Postgres HA, 24/7 operations, or
disaster recovery. Budget alerts notify but are not hard spending caps. GPU and multi-cloud paths
remain separately gated.

## Lessons learned

Cloud drills exposed assumptions that static validation could not: GSM IDs reject slash-separated
names, disabled `LatestOrFail` versions do not fall back, preemptible single-node clusters can
invalidate recovery evidence, and Docker availability affects paid test windows. Teardown
verification is part of acceptance, not housekeeping.
