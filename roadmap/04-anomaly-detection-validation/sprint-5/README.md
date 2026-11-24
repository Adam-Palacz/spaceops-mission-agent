# AV5 - Agent reasoning benchmark

**Status:** Todo. Not started.

**Goal:** Score the current single agent on investigation quality, separate from whether a detector fired.

## Outcomes

- A metric table for triage, evidence, diagnosis, unsupported claims, unsafe recommendations, escalation, and cost.
- Diagnosis is reported only where RD4 says the cause is known.

## Scheduling and validity

AV5 is independent of AV2-AV4. Start metric implementation on synthetic cases immediately; historical scoring waits for RD4.3, the RD2.3 read-only profile, and an eligible model path. Report named, blinded and synthetic/perturbed cohorts separately, with identity-only and no-evidence controls. Freeze case families before model or prompt selection.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
