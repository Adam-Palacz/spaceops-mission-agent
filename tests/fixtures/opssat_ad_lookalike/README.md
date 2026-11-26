# Synthetic OPSSAT-AD Lookalike Fixture (CI Only)

Tiny hand-crafted synthetic CSV files (`segments.csv` and `dataset.csv`) mirroring the OPSSAT-AD column structure for CI unit tests (`tests/test_mission_data_rd21.py`).

- **Not spacecraft telemetry:** Contains 4 invented segments across `CADC0872`, `CADC0873`, and `CADC0884` covering both `train=1` and `train=0` as well as `anomaly=0` and `anomaly=1`, plus a space-separated UTC timestamp and a duplicate-timestamp point to exercise adapter edge cases.
- **License:** `LicenseRef-SpaceOps-Synthetic` (`dataset_id = "opssat-ad-lookalike"`).
- **Real OPSSAT-AD dataset:** Manual download from Zenodo `10.5281/zenodo.12588359` (CC BY 4.0); never committed to git.
