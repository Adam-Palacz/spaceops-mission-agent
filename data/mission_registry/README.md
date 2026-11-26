# Mission Registry (`data/mission_registry`)

Git-versioned catalog of missions, spacecraft, subsystems, datasets, licenses, channel names, and default-deny model egress approvals loaded by `apps.mission_data`.

- **`registry.json`** — Declares `lab-synthetic` (committed CI fixture channels) and `ops-sat` / `opssat-ad` (channel names only; no downloaded telemetry samples or calibration curves).
- **`egress_approvals.json`** — Versioned default-deny approval registry (`approvals: []` by default) enforced by `apps.mission_data.egress` for isolated historical public-data experiments (RD1.3).
- No ground-truth anomaly labels or private/unlicensed mission recordings belong in this directory.
