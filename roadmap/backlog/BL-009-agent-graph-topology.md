# BL-009 - One agent graph topology

| Field | Value |
|-------|-------|
| **Backlog ID** | BL-009 |
| **Source** | RD2.4 disposition of the 2026-11-26 review |
| **Owner** | Unassigned |
| **Target** | Deferred |
| **Scheduled task** | None. Trigger is the next edit to agent graph edges. |

## Description

`apps/agent/graph.py` describes transitions in the LangGraph builder and again in the checkpoint loop. RD2.4 does not unify them. The next person who changes an edge should make those two descriptions match, or add a parity test, in that same change.

## Requirements

- Do not change the running path while this item is deferred: triage, investigate, escalation check, decide, act, report.
- Do not add specialist nodes.
- Do not start this item only to tidy the file.

## Test requirements

- After the trigger, one test shows that checkpointed and non-checkpointed runs follow the same edges.
