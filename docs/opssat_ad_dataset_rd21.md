# OPSSAT-AD Labeled-Segment Adapter and Import Audit (RD2.1)

**Task:** [RD2.1](../roadmap/03-real-world-mission-data/sprint-2/RD2.1-opssat-ad-adapter.md)  
**Manifest:** [data/mission_registry/opssat_ad_manifest.json](../data/mission_registry/opssat_ad_manifest.json)  
**Status:** Implemented offline adapter and synthetic CI lookalike. Real Zenodo CSV files are downloaded manually and are not committed to git. Does not change the `2026-11-23` No-go admission verdict.

---

## 1. Citation, License, and Published Checksums

- **Citation:** B. Ruszczak, K. Kotowski, D. Evans, and J. Nalepa, *"The OPS-SAT benchmark for detecting anomalies in satellite telemetry,"* *Scientific Data* (2025), DOI: `10.1038/s41597-025-05035-3`.
- **Dataset:** Zenodo record `10.5281/zenodo.12588359` (https://doi.org/10.5281/zenodo.12588359).
- **License:** `CC-BY-4.0`.
- **Published Zenodo MD5 checksums (record `12588359`):**
  - `dataset.csv`: `c12fb83863afa4463dec07303a20bb14`
  - `segments.csv`: `1f4b6ffd0359efac96a6698ff557e0f9`

Newer Zenodo revisions intentionally fail checksum verification unless explicitly reconciled in `opssat_ad_manifest.json`.

---

## 2. Official Import Audit Counts and Split Caveat

| Metric | Official `dataset.csv` count | Notes |
|---|---:|---|
| Total segments | **2,123** | 9 channels: magnetometers `CADC0872`–`CADC0874`, photodiodes `CADC0884`, `CADC0886`, `CADC0888`, `CADC0890`, `CADC0892`, `CADC0894` |
| Training (`train=1`) | **1,594** | 1,273 nominal + 321 anomalous (paper prints 1,494 in the training total while its class counts sum to 1,594) |
| Test (`train=0`) | **529** | Held-out evaluation split |

- **Preserve the source flag:** Train/test membership strictly follows the released `train` column (`1 -> "train"`, `0 -> "test"`). Never re-split randomly.
- **Generalization caveat:** The released split is stratified random, not chronological. Passing scores on this split do **not** prove time-separated unseen-event generalization.
- **Safety caveat:** Labeled anomalies describe telemetry shapes, gaps, zeros, and peaks for operator notification — never recommended spacecraft commands.

---

## 3. Dataset Separation and Telemetry vs. Ground-Truth Contract

- **`opssat-ad`** (`sample_kind="real"`, `license_spdx="CC-BY-4.0"`): real Zenodo import (`--source-dir <local-dir>`).
- **`opssat-ad-lookalike`** (`sample_kind="synthetic"`, `license_spdx="LicenseRef-SpaceOps-Synthetic"`): tiny 4-segment synthetic CI fixture under `tests/fixtures/opssat_ad_lookalike/` so CI never downloads Zenodo and never conflates synthetic tests with real telemetry.
- **`opssat-reentry-uhf`**: distinct OPS-SAT May 2024 re-entry campaign. Re-entry columns (`Battery_Voltage`, `Battery_Temp`, `PD*_CSS_theta`, `RSSI`, `altitude`, `latitude`, `longitude`, `coarse_spin`) are rejected fail-closed by `OPSSATADAdapter`.
- **Telemetry emission (`TelemetryEventV1`):** Preserves `segment_id`, `channel`, `sampling` (reserved metadata key, RD2.1 addendum to `RD1.4` without modifying `TelemetryEventV1`), and normalized UTC ISO8601 `ts` without resampling. Zero labels or `train` flags enter telemetry.
- **Ground-truth emission (`GroundTruthRecord`):** Stored separately with `segment_id` set and `time_range_start=None, time_range_end=None` so evaluator joins match segment-keyed `PredictionRecord` entries strictly within `(mission_id, dataset_id)`.

---

## 4. Offline Manual Import Workflow

```bash
# Dry-run audit against manually downloaded Zenodo files (reports explicit "skipped" if absent)
python scripts/import_opssat_ad.py --source-dir /path/to/opssat-ad

# Write separated telemetry and evaluator-only ground-truth NDJSON outputs
python scripts/import_opssat_ad.py \
  --source-dir /path/to/opssat-ad \
  --telemetry-out var/opssat_ad/telemetry \
  --ground-truth-out var/opssat_ad/ground_truth

# Verify offline against the synthetic CI lookalike
python scripts/import_opssat_ad.py --lookalike
```
