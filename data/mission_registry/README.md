# Mission Registry (`data/mission_registry`)

Git-versioned catalog of missions, spacecraft, subsystems, datasets, licenses, channel names, checksum manifests, and default-deny model egress approvals loaded by `apps.mission_data`.

- **`registry.json`** — Declares `lab-synthetic` (committed CI fixture channels) and `ops-sat` (`opssat-ad` real channel names + `opssat-ad-lookalike` synthetic CI fixture scope; no downloaded telemetry samples or calibration curves).
- **`opssat_ad_manifest.json`** — Records OPSSAT-AD citation (`10.5281/zenodo.12588359`, `10.1038/s41597-025-05035-3`), CC BY 4.0 license, published Zenodo MD5 checksums for `dataset.csv` and `segments.csv`, and official `2123 / 1594 / 529` expected audit counts (RD2.1).
- **`egress_approvals.json`** — Versioned default-deny approval registry (`approvals: []` by default) enforced by `apps.mission_data.egress` for isolated historical public-data experiments (RD1.3).
- No ground-truth anomaly labels or private/unlicensed mission recordings belong in this directory.
