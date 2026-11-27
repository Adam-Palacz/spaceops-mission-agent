# AV1 - Benchmark method

**Status:** In progress. AV1.1 registers the official OPSSAT-AD split. AV1.2 is not started.

**Goal:** Freeze datasets, splits, and metrics before any model is trained.

## Outcomes

- An experiment registry that can rerun a named configuration.
- Official OPSSAT-AD and ESA-ADB metrics implemented as functions, with leakage checks.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
