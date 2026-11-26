# RD1 - Mission data architecture

**Status:** In progress. RD1.1, RD1.2, and RD1.4 are Done. RD1.3 is still Todo.

**Goal:** Give every future sample a source-agnostic envelope, a registry, and an isolation rule before any real file is imported.

## Outcomes

- An adapter interface that can emit `TelemetryEventV1` plus provenance.
- Registries for mission, spacecraft, subsystem, and channel metadata.
- A hard split between telemetry values and ground-truth annotations.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
