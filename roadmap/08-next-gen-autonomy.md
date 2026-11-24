# 08 - Next-Gen Autonomy

**Status:** Planned. This document does not implement the phase.
**Execution:** [08-next-gen-autonomy/](08-next-gen-autonomy/)

Keep the L3/L4 specifications and do not build them until a measurement or an operator record says the current agent is the wrong shape.

## Why this phase exists

Multi-agent routing, collaborative replanning, and GraphRAG are expensive ways to answer a question the benchmark has not asked yet. The specifications remain the design reference so the work is not lost.

## Reconciliation with the repository

The vision file `roadmap/deprecated-03-next-gen-autonomy.md` is already titled as a later phase. The execution specs and Todo boards under `roadmap/deprecated-03-next-gen-autonomy/` are unchanged and are the historical reference. No NG code is on this branch. NG4's execution moves to EA2. The minimum redaction needed before real samples reach an external model is an input to RD2.3, AV6, and the existing privacy work, not a reason to implement the full NG3 gateway now.

## Exit gate

- NG1 starts only if AV6.2 documents a measured cross-subsystem miss that a single agent fails and a specialist split is expected to fix.
- NG2 starts only after EV3 or MC4.2 has operator feedback that approve/reject cannot express.
- NG3's full gateway stays deferred. Real-sample redaction is tracked where the data leaves the machine.
- NG4 is implemented, if at all, as EA2, and the NG4 board is updated only when EA2 is actually done.
- NG5 starts only if AV6 shows a cited retrieval failure that vector search cannot answer.

## Non-goals

- Implementing Flight Director, specialists, GraphRAG, or a new agent loop in this restructuring.
- Marking any NG task Done.
- Deleting or rewriting the historical specifications.
