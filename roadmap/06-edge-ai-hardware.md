# 06 - Edge AI and Hardware Research

**Status:** Planned. This document does not implement the phase.
**Execution:** [06-edge-ai-hardware/](06-edge-ai-hardware/)

Measure a selected detector and a local model on hardware the project can actually access. Jetson Orin Nano is the first target. Thor is conditional. A lab board is not flight hardware.

## Why this phase exists

Offline and power-limited inference is a different claim from a cloud agent demo. The NG4 specifications already describe the offline agent and move here as the execution path.

## Reconciliation with the repository

The LLM gateway can select a backend, and an optional GPU backend exists for NVIDIA NIM in compose. There is no ONNX runtime, TensorRT build, Jetson image, or power measurement. NG4's dual-mode gateway, local SLM adapter, and degraded-mode runbook remain the specifications for EA2. They are not implemented. No radiation, thermal, or flight-computer comparison has been done.

## Exit gate

- A detector or a documented waiver runs locally on the target board, with latency, throughput, memory, and power or an explanation of which instruments were missing.
- Offline mode has a test that does not fall back to a cloud model.
- The feasibility note says the result is not flight readiness.

## Non-goals

- Buying or assuming access to Jetson Thor.
- Qualifying hardware for orbit.
- Training large models on EuroHPC. That is an optional later capacity note in phase 07.
