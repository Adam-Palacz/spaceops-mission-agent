# Managed Observability Baseline (PR4.4)

## Decision

The production-pilot backend is Google Cloud Logging for sanitized workload and signed-audit
records, and Google Cloud Trace for distributed traces. The regional log bucket is configured by
Terraform with 30-day retention. The OpenTelemetry Collector exports traces with a dedicated
Google service account through GKE Workload Identity; no exporter key is mounted.

The in-cluster Jaeger deployment remains a stage-only debugging option and is not a production
system of record.

## Architecture and access

- Terraform enables the Logging, Trace, Monitoring, and IAM APIs and creates the regional bucket,
  selective log sink, collector service account, and only `roles/logging.logWriter` and
  `roles/cloudtrace.agent`.
- The Helm managed-observability overlay disables Jaeger and configures the Collector
  `googlecloud` exporter.
- The Kubernetes service account is annotated with the Google service account only when the
  Workload Identity binding is enabled.
- Application audit records are emitted as structured, signed records to standard output. The sink
  accepts only records marked `spaceops_managed_canary` or `spaceops_audit`.
- Query/export access is not granted to the collector identity. Human read access remains a
  separately managed project responsibility.

Same-project log-bucket sinks do not receive a separate writer identity. Consequently, no
`roles/logging.bucketWriter` binding is created for this sink.

## Data handling

Only synthetic, bounded metadata is allowed in the production-readiness drill:

- a random trace identifier;
- a synthetic canary correlation identifier;
- outcome, timing, and component names.

Prompts, request/response bodies, credentials, operator email addresses, cloud project identifiers,
and raw incident payloads are prohibited in committed evidence. Evidence stores only sanitized
provider names, region, result counts, HTTP status, and hashed or redacted identifiers.

## Live drill, 2026-11-23

The drill used the Terraform-managed regional backend without creating GKE or Cloud SQL.

1. Terraform converged the bucket, sink, collector service account, and least-privilege writer
   roles with no drift.
2. A synthetic log containing a correlation identifier was written and read from the custom
   `_AllLogs` view.
3. A Cloud Trace root span carrying the same correlation identifier was written through the Trace
   API and read by the authorized operator. Trace ingestion was eventually consistent and became
   queryable after propagation.
4. A temporary service account had no Logging viewer role. After IAM propagation, an impersonated
   `entries:list` request returned HTTP `403`.
5. The temporary denied principal was deleted.
6. Terraform destroyed the sink, collector identity, and IAM bindings and requested deletion of
   the custom bucket. The sink returned `NOT_FOUND`; the bucket entered `DELETE_REQUESTED`; no GKE
   cluster or Cloud SQL instance was present.

The sanitized machine-readable result is in
`roadmap/02.5-production-readiness/sprint-4/evidence/PR4.4-managed-observability-2026-11-23.json`.

## Retention and deletion semantics

- Custom Cloud Logging records use the configured 30-day retention period.
- Deleting a custom Logging bucket starts the provider recovery period. The bucket is unavailable
  for normal use while its lifecycle is `DELETE_REQUESTED`; Google permanently deletes it after
  the provider recovery window. The application has no backup copy of this bucket.
- Cloud Trace retains spans for the provider-defined 30-day period. Individual trace deletion is
  not exposed by the service, so expiry—not immediate record deletion—is the deletion mechanism.
- Deleting the collector identity stops future export but does not bypass provider retention for
  records already accepted.
- A legal or security hold must follow `docs/data_retention_privacy_pr24.md`; no hold was active in
  this drill.

## Reproduction and safety

Use `enable_managed_observability=true` with the normal production-pilot Terraform deployment.
For a backend-only drill, target only the resources in `managed_observability.tf`; a non-targeted
plan also proposes the complete GKE stage platform.

After the query and deny checks:

1. destroy the sink, bucket, collector service account, and its IAM bindings;
2. verify the sink is absent and the bucket is `DELETE_REQUESTED`;
3. verify no `spaceops-otel-*` or temporary denied-principal service account remains;
4. verify the GKE cluster list is empty and that Cloud SQL was not enabled by this drill;
5. scan committed evidence for email addresses, project IDs, tokens, and private payloads.

API enablement may remain because it has no standalone runtime charge. A bucket in provider-managed
pending deletion is not an approved long-lived pilot resource and must not receive new records.
