# Historical public-data model egress policy (planned)

**Status:** specification only; not an approval, implementation, waiver, or production admission. Owner: Security / Mission Data (to be assigned). PR4.7 remains the only pilot admission decision; stage remains synthetic-only. Scope: isolated local/dev historical public-data experiments, not live telemetry or pilot data.

## Decision matrix

| Input | Default | Possible exception |
|---|---|---|
| Synthetic CI fixtures | Existing approved lab path | Existing provider controls apply. |
| Versioned historical public dataset | Local only; external denied | Explicit dataset/version/provider/purpose approval under this policy. |
| Unknown license or classification; mixed, private, sensitive, customer, live or operational data | External denied | No exception under this policy; applicable privacy/security and admission rules remain binding. |
| Ground truth, hidden references, credentials, personal data or restricted technical data | Never send for these experiments | None. |

Public availability or a CC license alone is not approval for external processing. A reviewed minimal egress/redaction control may conclude that no field masking is necessary for specific allowlisted public fields; it must still validate the actual outbound payload. No full NG3 gateway is required for this narrowly scoped path. References to a reviewed redaction control in active roadmap tasks mean this minimum for eligible public historical data only; they do not relax any stricter pilot, live-stream, offline-only or historical security requirement.

## Planned implementation and acceptance (RD1.3; exercised by RD2.3 and AV5)

- Maintain a default-deny, versioned approval registry keyed by dataset ID, version/checksum, approved field list, purpose, provider/account/model/region, allowed processing (including embeddings), owner, review date and expiry. Record license/attribution, confidentiality/export and provider retention/training/contract assessment, and whether redaction is required. Unknown, expired, mismatched or missing records deny external processing.
- Classify and minimize data before any provider request. Apply a schema allowlist plus sensitive-field detection and applicable redaction. Enforce at the model egress boundary for prompts, retrieved snippets, embedding/reranking calls, tool-result context, retries, fallback and evaluation/judge calls. Derived summaries inherit the source restriction until reviewed. Do not include ground truth or hidden reference answers.
- Use an explicitly approved endpoint and account, with provider policy and retention settings checked; forbid unapproved fallback, telemetry export and raw prompt/response logging. Record sanitized decision metadata, dataset and policy revision, no raw payloads or tokens.
- Default real-data runs to an isolated local/no-external backend if approval or enforcement is absent. Disable external embeddings, rerankers, judges and cloud fallback in local-only mode; prove with denied network egress. If no usable local model exists, a non-LLM replay can verify plumbing, but it cannot satisfy an agent reasoning or model benchmark claim.
- Before any approved external benchmark, record an explicit named approval and execute negative tests: unapproved dataset/version, expired policy, wrong provider, forbidden fields, hidden answer, mixed source, direct-call bypass and fallback. Verify approved public-only payloads and deny paths using synthetic fixtures first; record sanitized evidence of the real-data path separately.
- Preserve existing CI on synthetic data only, read-only tool restrictions and mission isolation. Do not mark RD1.3 or RD2.3 Done merely because this policy exists.

This policy does not authorize external processing of re-entry data with an unresolved license, public live streams, customer or export-controlled information. The full NG3 scrubber and existing production privacy review remain independent.
