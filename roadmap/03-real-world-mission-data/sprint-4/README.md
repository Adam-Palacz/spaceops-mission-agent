# RD4 - Historical incident knowledge

**Status:** Done. RD4.1 records two public sources. RD4.2 records one cited failure mode and stores no procedure. RD4.3 freezes two synthetic hidden-reference cases. RD4.4 waives SMAP/MSL without data. The holdout is not a phase exit.

**Goal:** Add cited public failure knowledge and hidden-reference cases without pretending the anomaly labels are root causes.

## Outcomes

- Every KB addition has a source, license, and citation.
- Hidden reference answers are invisible to the agent under test.
- SMAP/MSL is optional and is not required to exit the phase.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
