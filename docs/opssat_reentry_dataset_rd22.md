# OPS-SAT re-entry UHF campaign (RD2.2)

The May 2024 UHF campaign is a separate product from OPSSAT-AD. Public column names are mapped in `data/mission_registry/opssat_reentry_manifest.json`. Dataset id `opssat-reentry-uhf` does not share segment labels or `CADC*` channel ids with `opssat-ad`.

## License gate

No machine-readable license was found on the public analysis page (`https://opssat.esa.int/ops-sat-1/docs/tm_analysis.html`). The manifest records `license_status: unrecorded` and an empty checksum list. `import_opssat_reentry(..., mode="real")` refuses before it reads a file. A recorded flag without pinned checksums still does not read rows.

The registry placeholder `UNRECORDED` is not a license.

## Time and derived fields

`Timestamp` is ground receipt time (`metadata.time_basis = ground_receipt`), not necessarily onboard generation time. `Days_Elapsed`, `Altitude`, `Bstar_drag`, `lat`, and `lng` are `role: derived`, not spacecraft sensors. Temperature columns are mapped as degrees Celsius because the public names are temperatures. No calibration curve is stored. RSSI, spin, and photodiode-angle columns keep a null unit.

## CI lookalike

`tests/fixtures/opssat_reentry_lookalike/uhf_telemetry.csv` is one invented row under `opssat-reentry-uhf-lookalike` and `LicenseRef-SpaceOps-Synthetic`. It is not a reception frame.

```text
python scripts/import_opssat_reentry.py --lookalike --telemetry-out <dir>
```

The command writes telemetry NDJSON only. It does not write ground truth, and it does not write into `data/telemetry/`.
