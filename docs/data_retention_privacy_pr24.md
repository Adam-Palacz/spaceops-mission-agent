# Data Retention and Privacy Policy (PR2.4)

**Policy owner:** Security / SRE  
**Approved scope:** local development and isolated stage  
**Production-pilot status:** conditional; managed trace/log backend and NG3 masking gates must pass
before pilot data is admitted.

## Purpose

This policy defines retention, classification, redaction, export, and deletion rules for SpaceOps
observability and operator-review data. It is a technical baseline, not legal advice. Contractual,
regulatory, or mission-specific requirements override these defaults through an approved change.

The current repository uses simulated data. Real spacecraft, customer, employee, or special
category personal data is prohibited until the PR3.4 review explicitly expands the allowed data
scope.

## Data classification

| Class | Examples | Handling |
|---|---|---|
| Public | Published documentation, intentionally public synthetic examples | May be published after owner review |
| Internal | Synthetic telemetry, test traces, aggregate metrics, non-sensitive build reports | Authenticated project access; external export only to approved providers |
| Confidential | Production-pilot telemetry, incident payloads, prompts/responses, reports, operator identity, infrastructure identifiers | Least privilege, encryption in transit/at rest, redaction, approved region/provider |
| Restricted | API keys, passwords, bearer tokens, cookies, private keys, raw authentication material | Secret manager only; never in prompts, logs, traces, reports, fixtures, evidence, or source control |

Environment rules:

| Environment | Permitted data | Prohibited data |
|---|---|---|
| Local/dev | Public and synthetic Internal data | Production/customer data; persistent real credentials in fixtures |
| Stage | Synthetic Internal data; sanitized Confidential-like test cases | Real personal data, real mission telemetry, Restricted values |
| Production pilot | Approved Confidential operational data after PR3.4 go/conditional-go | Restricted values in observability; data outside the approved pilot purpose |

Data that cannot be classified is treated as Confidential. Authentication material is always
Restricted regardless of environment.

## Retention schedule

Retention is measured from event creation. Shorter provider limits are acceptable for local/stage;
longer retention requires a documented purpose, owner, access review, and cost/privacy approval.

| Data set | Local/dev | Isolated stage | Production-pilot target | System of record / deletion owner |
|---|---:|---:|---:|---|
| Application/container logs | Session or 7 days | 14 days | 30 days | Cloud Logging / SRE |
| Distributed traces | Session only | 7 days | 30 days | Cloud Trace / SRE |
| Prometheus metrics | Session or 15 days | 15 days | 90 days | Managed metrics / SRE |
| Audit records | 30 days | 90 days | 365 days | Durable audit store / Security |
| Approval records | 30 days | 90 days | 365 days | Postgres target / Security |
| Agent checkpoints, terminal status | 30 days | 30 days | 30 days | Postgres / API owner |
| Replay inputs and incident payloads | 30 days | 30 days | 90 days | Postgres/object store / Operations |
| Eval inputs and reports | Until next baseline or 90 days | 180 days | 365 days when used for a release decision | CI artifact store / Model owner |
| Generated incident reports | 30 days | 90 days | 365 days | Approved report store / Operations |
| PR evidence and sanitized release records | Project lifetime | Project lifetime | Project lifetime | Git / Release owner |

`Project lifetime` applies only to sanitized evidence that contains no Restricted data and no
unapproved Confidential content. Git history is not a deletion-capable data store; sensitive
artifacts must never be committed.

Backups inherit the classification of their source. Deleted live records may remain in encrypted
backups until the backup expiry defined by the backup policy. Restore drills must not silently
reintroduce records whose retention period has expired; a post-restore expiry sweep is required.

## Redaction and minimization

### Logs

- Never log request bodies, prompts, model responses, secret values, authorization headers,
  cookies, connection strings with credentials, or complete external-provider responses.
- Log stable IDs, category/reason codes, counts, durations, outcomes, and hashes where correlation
  is necessary.
- `apps.telemetry.JsonTraceFormatter` applies a best-effort baseline redaction to messages and
  exceptions for bearer tokens, known secret assignments, provider token prefixes, and Postgres
  URL passwords.
- Baseline regex redaction is defense in depth, not permission to log sensitive input.

### Traces and metrics

- Span attributes use bounded metadata such as `run_id`, `incident_id`, action type, outcome,
  count, model ID, and reason code.
- Prompts, payloads, report text, MCP arguments/results, approval keys, and raw exception bodies
  are prohibited span attributes.
- Metric labels must be low-cardinality and must not contain operator identity, incident text,
  prompts, payloads, tokens, email addresses, or customer identifiers.

### Audit and approvals

- Audit stores an argument hash rather than raw arguments.
- Approval identity must come from verified authentication before production pilot; the current
  shared-key and caller-supplied attribution limitation is PR23-002.
- Audit is application append-only but not yet tamper-evident (PR23-004).
- Hashing does not anonymize low-entropy identifiers. Access controls and retention still apply.

### Prompts, evals, and reports

- Minimize inputs before prompt assembly. Remove credentials and unnecessary operator/customer
  identifiers at ingestion, not after the LLM call.
- Production-pilot prompt/response capture is off by default. An approved debugging window must be
  time-boxed, access-logged, and deleted when the window closes.
- Eval fixtures and reports use synthetic or irreversibly sanitized data.
- Generated reports must pass the NG3 masking audit before external publication or production
  pilot use.

## Managed backend decision

### Current state

- Local and stage use the OpenTelemetry Collector and in-cluster Jaeger all-in-one.
- Jaeger has no persistent volume or retention control in the current Helm chart. Pod deletion
  removes its data. It is a temporary stage visualization tool, not a production system of record.
- Kubernetes container logs use the cluster runtime path; the chart does not currently configure a
  durable log backend.
- Prometheus defaults to `15d` retention when the monitoring overlay is enabled.

### Production-pilot target

Use **Google Cloud Trace** for traces and **Google Cloud Logging** for GKE workload logs. Keep the
OpenTelemetry API/Collector boundary so another OTLP-compatible backend can replace GCP without
application instrumentation changes. Metrics remain Prometheus-compatible and may move to Google
Managed Service for Prometheus separately.

Minimum implementation path before a production-pilot go decision:

1. Enable Cloud Trace and Logging APIs in the pilot project.
2. Bind a dedicated collector/workload identity with trace-write only; do not mount static service
   account keys.
3. Add a production-only OTel `googlecloud` exporter and disable in-cluster Jaeger as the
   production system of record.
4. Configure Cloud Logging buckets with 30-day retention, region, CMEK decision, and least-
   privilege viewer roles.
5. Configure Cloud Trace retention/access according to provider capabilities and record any
   provider-enforced duration that differs from this policy.
6. Run a sanitized canary trace/log, query it with an authorized operator, prove unauthorized
   access is denied, then perform a deletion/expiry drill.
7. Attach configuration and screenshots/CLI evidence to PR3.4 without including raw Confidential
   or Restricted data.

Until these steps are complete, stage remains synthetic-only and PR3.4 cannot declare an
unconditional production-pilot `Go`.

## External export rules

Export is deny-by-default for Confidential data. The data owner must record:

- purpose, fields, classification, destination, region, retention, encryption, and receiving role;
- provider agreement/security approval where applicable;
- a sample proving Restricted values are absent;
- deletion date and owner.

Only the minimum necessary fields may be exported. Public AI services, issue trackers, chat, and
screenshots are not approved destinations for raw incident payloads, prompts, traces, or logs.
Screenshots must be cropped, reviewed, and redacted before they enter evidence or publication.

## Operator export and deletion procedure

1. Identify the artifact by stable IDs and data range; do not copy broad datasets for convenience.
2. Classify it and confirm the requester is authorized.
3. Export to an encrypted, access-controlled location with an expiry date and checksum manifest.
4. Run secret and personal-data review before sharing or committing evidence.
5. Record requester, purpose, approver, exported fields, destination, and expiry in the review
   ticket.
6. On expiry or approved deletion request, delete the primary artifact and derived copies, revoke
   share links, and record backup-expiry behavior.
7. Verify deletion by querying the primary store and artifact index. Preserve only a sanitized
   deletion receipt.

Legal/security hold suspends normal deletion only with written owner, scope, reason, and review
date. A hold is not permission for broader access or export.

## Compliance and roadmap dependency

NG3 compliance work depends on this policy but must add enforcement:

- NG3.3 must test masking across logs, traces, audit decisions, reports, screenshots, and exports.
- NG3 must define subject/record discovery where personal data is admitted.
- PR3.4 must verify the managed backend, retention configuration, deletion drill, PR2.3 findings,
  and any policy exceptions before production-pilot approval.

## Verification

`tests/test_production_readiness_pr24_retention_privacy.py` verifies policy coverage, known
sensitive-field redaction, trace attribute constraints, current Jaeger limitations, and roadmap
handoff.
