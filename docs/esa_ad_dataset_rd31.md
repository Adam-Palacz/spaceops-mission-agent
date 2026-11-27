# ESA-AD multi-mission slice (RD3.1)

ESA-AD is Zenodo [10.5281/zenodo.12528696](https://doi.org/10.5281/zenodo.12528696), license CC BY 3.0 IGO (`CC-BY-3.0-IGO`). The benchmark code at [kplabs-pl/ESA-ADB](https://github.com/kplabs-pl/ESA-ADB) is MIT and is not vendored. Mission names stay anonymized.

## What was checked

On 2026-11-26 the Zenodo file list showed `ESA-Mission1.zip` with `channels/channel_N.zip`, `labels.csv`, `anomaly_types.csv`, and `telecommands/telecommand_N.zip`. That listing stopped before later archives. Checksums were not captured. The benchmark README names folders `ESA-Mission1` and `ESA-Mission2` and says the published benchmark uses two of the three missions.

## What this repo does

`data/mission_registry/esa_ad_manifest.json` records three dataset contexts. `esa-ad-mission1` and `esa-ad-mission2` are the published benchmark members. `esa-ad-mission3` is held out. Including it requires the report text `override: Mission3 included in benchmark score`.

Real import refuses while `checksums_pinned` is false. The published experiment budget recorded from the benchmark README is 512 GB free for artifacts and 32 GB RAM. No archive is downloaded.

CI streams `tests/fixtures/esa_ad_lookalike/`, one invented row per mission key. A mission1 query does not return the mission2 row.
