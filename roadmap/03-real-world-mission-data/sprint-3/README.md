# RD3 - ESA-ADB import

**Status:** In progress. RD3.1 streams a lookalike and holds Mission3 out of the published benchmark. RD3.2 is Done on that slice: anomalies, rare nominal events, and telecommands stay separate, and Mission3 may have zero telecommands. The Zenodo archives are not downloaded. RD3.3 stays Todo.

**Goal:** Import the ESA anomaly dataset at its real volume, keeping missions, rare nominal events, and telecommands distinct.

## Outcomes

- Mission1 and Mission2 can be replayed under the published benchmark's mission selection.
- Mission3 remains available as data but is not silently added to the benchmark score.
- Rare nominal events and telecommands have their own records.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
