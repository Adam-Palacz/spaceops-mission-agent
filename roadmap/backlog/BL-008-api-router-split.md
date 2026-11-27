# BL-008 - Split the API module into routers

| Field | Value |
|-------|-------|
| **Backlog ID** | BL-008 |
| **Source** | RD2.4 disposition of the 2026-11-26 review |
| **Owner** | Unassigned |
| **Target** | Deferred |
| **Scheduled task** | None. Trigger is the first implementation edit inside PR4.9. |

## Description

`apps/api/main.py` mixes ingest, runs, replay, approvals, and operational routes. Splitting it is real work, and RD2.4 does not do it. The split waits until PR4.9 starts changing authorization on those routes, so the boundaries are drawn once.

## Requirements

- Keep OPA, approval checks, and the unauthenticated-ingest gap visible. Do not hide the gap by moving code.
- Leave `data/telemetry/telemetry.ndjson` unchanged.
- Do not start this item before PR4.9 implementation.

## Test requirements

- Existing API tests pass after any split.
- A route that is protected today stays protected.
