# Phase 06: Edge AI and Hardware Research

**Status:** Planned. Not started.
**Priority:** P3 research. Not on the critical path to admission or to the first benchmark report.
**Strategy:** [06-edge-ai-hardware.md](../06-edge-ai-hardware.md)
**Master roadmap:** [MASTER.md](../MASTER.md)

Measure a selected detector and a local model on hardware the project can actually access. Jetson Orin Nano is the first target. Thor is conditional. A lab board is not flight hardware.

## Sprint map

| Sprint | Folder | Goal |
|--------|--------|------|
| **EA1** | [sprint-1/](sprint-1/) | Edge detector runtime |
| **EA2** | [sprint-2/](sprint-2/) | Offline local model |
| **EA3** | [sprint-3/](sprint-3/) | Hardware measurements |
| **EA4** | [sprint-4/](sprint-4/) | Feasibility, not flight readiness |

## Exit gate

- A detector or a documented waiver runs locally on the target board, with latency, throughput, memory, and power or an explanation of which instruments were missing.
- Offline mode has a test that does not fall back to a cloud model.
- The feasibility note says the result is not flight readiness.

## Non-goals

- Buying or assuming access to Jetson Thor.
- Qualifying hardware for orbit.
- Training large models on EuroHPC. That is an optional later capacity note in phase 07.

Passing this gate does not change the production-admission decision and does not declare flight readiness.
