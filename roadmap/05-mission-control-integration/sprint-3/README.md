# MC3 - Public telemetry stream

**Status:** Todo. Not started.

**Goal:** Exercise the existing NATS path with a live public stream that is not a benchmark dataset.

## Outcomes

- A SatNOGS or equivalent public connector with an explicit license.
- Duplicate, late, and missing frames are handled without corrupting historical datasets.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
