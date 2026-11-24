# 03 - Real-World Mission Data

**Status:** Planned. This document does not implement the phase.
**Execution:** [03-real-world-mission-data/](03-real-world-mission-data/)

Move analysis from the synthetic fixture to cited, isolated historical mission datasets. Two public OPS-SAT products are the first pair. They are not the same dataset and their labels do not transfer.

## Why this phase exists

The lab can already ingest, store, retrieve, and reason over synthetic telemetry. It cannot yet show that those paths work on a real spacecraft recording without mixing missions or leaking labels into the agent.

## Reconciliation with the repository

`TelemetryEventV1.metadata` can carry provenance without a breaking field, but the contract has no mission, dataset, or license identity. `data/telemetry/telemetry.ndjson` stays the CI fixture. OPSSAT-AD (Zenodo 10.5281/zenodo.12588359, CC BY 4.0) is 2123 labeled univariate segments from nine channels, split 1594/529 by the `train` flag in the released CSV. That split is stratified random, not a chronological holdout. The re-entry UHF campaign (1-22 May 2024, [ESA UHF telemetry analysis](https://opssat.esa.int/ops-sat-1/docs/tm_analysis.html)) is a separate physical recording and its license was not stated on the analysis page during this pass. ESA-AD (Zenodo 10.5281/zenodo.12528696, CC BY 3.0 IGO) contains three anonymized missions; the published benchmark uses two. Rare nominal events are not anomalies, and telecommands are not anomaly labels.

## Exit gate

- Replay cited historical telemetry from at least two distinct missions through the existing ingest and telemetry MCP path. Both OPS-SAT products count as one mission. Record the mission IDs, replay run IDs, and agent analysis for each mission.
- Replay the RD4 historical cases with mission-scoped telemetry and knowledge retrieval. Verify that wrong-mission queries return no evidence and that only the evaluator can read reference answers.
- Record mission ID, dataset ID, version, and license for each replay. Keep ground truth in a separate evaluator-only store. Re-entry samples carry no OPSSAT-AD labels.
- The synthetic fixture and current eval jobs still pass without those datasets present.

## Non-goals

- Training a detector. That is phase 04.
- Live SatNOGS collection. That is phase 05.
- Declaring the agent correct because it read a real file.
- Committing the large ESA-AD files or any file whose license is not recorded.
