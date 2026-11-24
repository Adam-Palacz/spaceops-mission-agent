# Phase 08: Next-Gen Autonomy

**Status:** Planned. Not started.
**Priority:** Deferred. Not the next implementation phase.
**Strategy:** [08-next-gen-autonomy.md](../08-next-gen-autonomy.md)
**Master roadmap:** [MASTER.md](../MASTER.md)

Keep the L3/L4 specifications and do not build them until a measurement or an operator record says the current agent is the wrong shape.

## Sprint map

| Sprint | Folder | Goal |
|--------|--------|------|
| **NG1** | [sprint-1/](sprint-1/) | Flight Director disposition |
| **NG2** | [sprint-2/](sprint-2/) | Collaborative planning disposition |
| **NG3** | [sprint-3/](sprint-3/) | Compliance gateway disposition |
| **NG4** | [sprint-4/](sprint-4/) | Offline model moved to edge |
| **NG5** | [sprint-5/](sprint-5/) | GraphRAG disposition |

## Exit gate

- NG1 starts only if AV6.2 documents a measured cross-subsystem miss that a single agent fails and a specialist split is expected to fix.
- NG2 starts only after EV3 or MC4.2 has operator feedback that approve/reject cannot express.
- NG3's full gateway stays deferred. The reviewed minimum egress/redaction control for isolated historical public-data experiments is tracked in RD1.3/RD2.3; all stricter live, confidential and pilot gates remain in force.
- NG4 is implemented, if at all, as EA2, and the NG4 board is updated only when EA2 is actually done.
- NG5 starts only if AV6 shows a cited retrieval failure that vector search cannot answer.

## Non-goals

- Implementing Flight Director, specialists, GraphRAG, or a new agent loop in this restructuring.
- Marking any NG task Done.
- Deleting or rewriting the historical specifications.

Passing this gate does not change the production-admission decision and does not declare flight readiness.
