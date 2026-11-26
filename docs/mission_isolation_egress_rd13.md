# Mission Isolation, Ground-Truth Separation, and Historical Model Egress (RD1.3)

**Task:** [RD1.3](../roadmap/03-real-world-mission-data/sprint-1/RD1.3-context-isolation-ground-truth.md)  
**Policy:** [LLM_DATA_POLICY.md](../roadmap/03-real-world-mission-data/LLM_DATA_POLICY.md)  
**Status:** Implemented for isolated local/dev historical public-data experiments. Does not change the `2026-11-23` No-go production-admission verdict; stage and CI remain synthetic-only.

---

## 1. Isolation Key and OPS-SAT Product Separation

The canonical isolation key is **`(mission_id, dataset_id)`**, never mission name alone (`DatasetScope` in `apps/mission_data/isolation.py`).

Two OPS-SAT historical products share `mission_id = "ops-sat"` and **must never share labels or cross-join**:

| Constant | `mission_id` | `dataset_id` | Description | Labels |
|---|---|---|---|---|
| `OPSSAT_AD_DATASET_ID` | `ops-sat` | `opssat-ad` | Labeled univariate segments (Zenodo `10.5281/zenodo.12588359`, CC BY 4.0) | Evaluator-only ground-truth store (including `train`/`test` split flag) |
| `OPSSAT_REENTRY_UHF_DATASET_ID` | `ops-sat` | `opssat-reentry-uhf` | May 2024 OPS-SAT UHF re-entry campaign (physical telemetry; import blocked until license is recorded) | Never inherits `opssat-ad` labels |

### Query Isolation Rules (`InvestigationTelemetryView` & Telemetry MCP)

- **Unscoped query** (`mission_id=None, dataset_ids=None`): returns only legacy unscoped synthetic records (e.g. `data/telemetry/telemetry.ndjson`). Real/isolated datasets are never returned by an unscoped query.
- **Mission-only query** (`mission_id` set, `dataset_ids` omitted): returns empty. Mission name alone is never sufficient to select isolated datasets.
- **Cross-dataset query**: returns empty for any dataset not explicitly named in `dataset_ids` (or `scopes`). Joining across two datasets requires explicitly naming both dataset IDs.

---

## 2. Ground-Truth Record Schema and Tool Allowlist

Ground truth and predictions live in separate stores (`GroundTruthStore` and `PredictionStore`), never inside `data/telemetry/` or `TelemetryEventV1`.

### `GroundTruthRecord` (`apps/mission_data/isolation.py`)

- `mission_id`, `dataset_id` (required non-blank isolation key)
- `segment_id` and/or `(time_range_start, time_range_end)` with `start <= end`
- `label_kind`: `"anomaly" | "rare_nominal" | "telecommand" | "reference_answer"`
- `label_value`: scalar label value
- `split`: optional `"train" | "test"` (keeps `OPSSAT-AD` train/test flags out of telemetry tools)
- `annotation_source`, `provenance_version`

### Role-Based Tool Allowlists

| Role | Allowed tools | Forbidden |
|---|---|---|
| `investigation` | `query_telemetry`, `search_runbooks`, `search_postmortems` | `read_ground_truth`, `join_predictions_to_labels` |
| `evaluator` | `read_ground_truth`, `join_predictions_to_labels` | Must not inject labels into investigation state or prompts |

- `sanitize_telemetry_for_investigation()` applies a strict allowlist on top-level keys (`event_id`, `ts`, `channel`, `value`, `unit`, `subsystem`, `source`, `metadata`) and on `metadata` (`RESERVED_METADATA_KEYS`). Any annotation/label/split field is stripped.
- `GroundTruthStore.join_predictions_to_labels()` rejects open runs (`status != "closed"` or missing `closed_at`) and joins strictly on exact `(mission_id, dataset_id)` + segment/time locator.
- `validate_prompt_template_no_labels()` verifies that prompt templates in `prompts/registry.py` never interpolate ground-truth or label fields.

---

## 3. Minimal Historical Public-Data Model Egress Control

Implemented in `apps/mission_data/egress.py` and wired into `apps/llm_gateway.py`, `apps/llm_backends/http_common.py`, `apps/llm_backends/nim_client.py`, `apps/common/reranker.py`, `apps/mcp/kb_server/main.py`, and `apps/mcp/kb_server/index_kb.py`.

1. **Default-deny versioned approval registry:** `data/mission_registry/egress_approvals.json` (`approvals: []` by default). External processing of `historical_public` data is denied unless an explicit, non-expired `EgressApprovalRecord` matches `(dataset_id, version_or_checksum, purpose, provider, approved_endpoint, account_id, model_id, region)` and enables the requested `processing_kind` (`chat_completion`, `embeddings`, `reranking`, `judge`).
2. **Strict data-class enforcement:** `unknown`, `unlicensed`, `mixed`, `private`, `sensitive`, `customer`, `live`, and `operational` classes are always denied for external providers. Derived summaries use `inherit_egress_classification()` so restrictions propagate (mixing `synthetic_ci` and `historical_public` becomes `mixed` and is external-denied).
3. **Ground truth and sensitive-payload protection:** Ground truth, hidden references, forbidden label keys, credentials/tokens, emails, and local absolute paths are denied on external egress; when `redaction_required=True`, supported redaction rules (`mask_emails`, `mask_ip_addresses`, `mask_absolute_paths`) run before outbound verification.
4. **Local-only mode & no cloud fallback:** Setting `LLM_LOCAL_ONLY_MODE=true` (or `EgressContext(local_only=True)`) restricts all LLM calls, NIM health checks, embeddings, and LLM reranking to strict loopback endpoints (`localhost`, `127.0.0.1`, `[::1]`) and blocks `gpu -> openai` fallback with `LLMEgressDeniedError` (fail-closed; never swallowed by `rerank_llm` or `LLMGatewayProviderError`).
5. **Direct-call bypass guard & sanitized audit:** `enforce_transport_egress_guard()` blocks direct backend or embedding calls when `local_only` or `protected_egress_scope` is active without gateway verification. Every decision emits sanitized `EgressDecision` metadata with zero raw prompts, payloads, or tokens.
