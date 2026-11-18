# PR2.4 - Trace/log retention and privacy policy

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Policy date** | 2026-09-26 |
| **Decision** | Cloud Trace + Cloud Logging target; current Jaeger remains stage-only |
| **Evidence** | [Policy](../../../docs/data_retention_privacy_pr24.md), [JSON evidence](evidence/PR2.4-retention-privacy-2026-09-26.json) |

## Description

Define how traces, logs, audit records, metrics, eval artifacts, and reports are retained and what
data may be exported to external providers. This prepares NG3 compliance work and production pilot
review.

## Requirements

- Retention policy for traces, logs, metrics, audit, approvals, eval reports, and generated reports.
- Privacy/data classification for simulated, stage, and production-pilot data.
- Redaction requirements for logs, traces, prompts, audit args, and reports.
- Managed trace/log backend decision plus minimum implementation path for production pilot
  (for example Cloud Trace, Grafana Tempo, persistent Jaeger, or an accepted temporary stage-only
  alternative with explicit retention limits).
- Deletion/export process for operator review artifacts.

## Checklist

- [x] Retention matrix added.
- [x] Data classification matrix added.
- [x] Redaction expectations documented.
- [x] Trace/log backend decision and minimum implementation path documented.
- [x] NG3 compliance dependency noted.

## Test requirements

- Static checks or tests for known sensitive fields where available.
- Documentation link test.

## Closure note

PR2.4 closes the policy and architecture-decision scope. It also adds baseline structured-log
redaction and regression checks for known secret shapes and prohibited trace body attributes.

Done does not claim that the managed production backend is deployed. The current Jaeger
all-in-one deployment is explicitly ephemeral and limited to synthetic local/stage use. Cloud
Trace, Cloud Logging, access controls, configured retention, and a deletion/expiry drill remain
mandatory PR3.4 production-pilot evidence.

NG3.3 must extend this baseline into a cross-artifact masking audit before production data or
external publication is approved.
