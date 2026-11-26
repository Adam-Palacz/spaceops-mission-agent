# Mission Registry (`data/mission_registry`)

Git-versioned catalog of missions, spacecraft, subsystems, datasets, licenses, and channel names loaded by `apps.mission_data.registry.load_registry()`.

- **`registry.json`** — Declares `lab-synthetic` (committed CI fixture channels) and `ops-sat` / `opssat-ad` (channel names only; no downloaded telemetry samples or calibration curves).
- No ground-truth anomaly labels or private/unlicensed mission recordings belong in this directory.
