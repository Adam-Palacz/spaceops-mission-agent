# Phase 03: Real-World Mission Data

**Status:** In progress (RD1 Done; RD2 next).
**Priority:** P0 for RD1-RD2, then P1 for RD3-RD4
**Strategy:** [03-real-world-mission-data.md](../03-real-world-mission-data.md)
**Master roadmap:** [MASTER.md](../MASTER.md)

Move analysis from the synthetic fixture to cited, isolated historical mission datasets. Two public OPS-SAT products are the first pair. They are not the same dataset and their labels do not transfer.

## Sprint map

| Sprint | Folder | Goal |
|--------|--------|------|
| **RD1** | [sprint-1/](sprint-1/) | Mission data architecture |
| **RD2** | [sprint-2/](sprint-2/) | OPS-SAT historical products |
| **RD3** | [sprint-3/](sprint-3/) | ESA-ADB import |
| **RD4** | [sprint-4/](sprint-4/) | Historical incident knowledge |

## Model egress gate

See [LLM_DATA_POLICY.md](LLM_DATA_POLICY.md). RD1.3 owns the minimal control and RD2.3 exercises it. A local non-LLM replay verifies ingestion only; actual model-backed read-only analysis is required for the agent evidence.

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

Passing this gate does not change the production-admission decision and does not declare flight readiness.
