# Mission Registry (`data/mission_registry`)

Git-versioned catalog of missions, spacecraft, subsystems, datasets, licenses, channel names, checksum manifests, and default-deny model egress approvals loaded by `apps.mission_data`.

- **`registry.json`** — Declares `lab-synthetic`, `ops-sat`, and `esa-ad`. No downloaded telemetry samples or calibration curves. The re-entry dataset license is `UNRECORDED`. ESA-AD mission names stay anonymized.
- **`opssat_ad_manifest.json`** — Records OPSSAT-AD citation (`10.5281/zenodo.12588359`, `10.1038/s41597-025-05035-3`), CC BY 4.0 license, published Zenodo MD5 checksums for `dataset.csv` and `segments.csv`, and official `2123 / 1594 / 529` expected audit counts (RD2.1).
- **`opssat_reentry_manifest.json`** — Column map for the May 2024 UHF campaign (RD2.2). `license_status` is `unrecorded`, so real rows are not read. Derived orbit fields are marked `derived`.
- **`esa_ad_manifest.json`** — Three anonymized ESA-AD contexts (RD3.1). Checksums are not pinned. Mission3 is outside the published benchmark. The lookalike registry marks `channel_1` as target and `channel_status` as categorical and non-target (RD3.2).
- **`cited_sources.json`** — Curated public citation targets (RD4.1). No scraped report bodies.
- **`failure_modes.json`** — One cited battery mode (RD4.2). No stored procedure.
- **`smap_msl_manifest.json`** — RD4.4 waiver for the Telemanom SMAP/MSL telemetry. No samples and no registry channels.
- **`experiments.json`** — AV1.1 experiment registry. One official OPSSAT-AD split. No raw samples.
- **`egress_approvals.json`** — Versioned default-deny approval registry (`approvals: []` by default) enforced by `apps.mission_data.egress` for isolated historical public-data experiments (RD1.3).
- No ground-truth anomaly labels or private/unlicensed mission recordings belong in this directory.
