# NG3.3 — Masking audit logs

| **Task ID** | NG3.3 | **Status** | Todo |

Log policy decisions without leaking redacted values.

## Dependency

Use the classification, retention, export, and redaction baseline from
[PR2.4](../../02.5-production-readiness/sprint-2/PR2.4-retention-privacy.md).
The audit must cover logs, traces, audit decisions, generated reports, screenshots, and operator
exports. Regex log redaction alone is not sufficient evidence for production-pilot data.
