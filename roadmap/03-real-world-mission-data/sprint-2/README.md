# RD2 - OPS-SAT historical products

**Status:** Done. RD2.1, RD2.2, RD2.3, and RD2.4 are Done. RD2.2 keeps the real UHF campaign unread. RD2.3 has a loopback model report on checksum-verified OPSSAT-AD. The RD2.4 deferral condition is met. RD3.2 is Done on the ESA-AD lookalike. RD3.3, RD4, and phase 04 stay Todo.

**Goal:** Import two cited OPS-SAT products through the RD1 adapters and read one replay with the current agent, without training a model.

## Outcomes

- OPSSAT-AD segments are addressable with the official train flag left intact.
- The re-entry UHF campaign is addressable only after its license is recorded.
- A read-only agent pass cites channels it actually queried.
- Post-`RD2.3` reassessment records explicit keep/redefine/defer/add decisions on architectural debt, governance weight, and downstream tasks before `RD3–RD4` and Phase 04.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
