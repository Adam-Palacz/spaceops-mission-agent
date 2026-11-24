# AV2 - Statistical and classical baselines

**Status:** Todo. Not started.

**Goal:** Put thresholds, EWMA, isolation forest, and local outlier factor behind one detector interface.

## Outcomes

- One interface for batch detection on registered windows or segments.
- A baseline table on the official OPSSAT-AD test partition, or an explicit blocked state if the dataset is absent.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
