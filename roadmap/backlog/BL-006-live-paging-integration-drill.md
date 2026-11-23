# BL-006 - Live paging integration drill

| Field | Value |
|-------|-------|
| **Backlog ID** | BL-006 |
| **Source** | PR3.2 game-day action PR3.2-A2 |
| **Owner** | On-call lead |
| **Target** | Before production pilot |
| **Scheduled task** | [PR4.6](../02.5-production-readiness/sprint-4/PR4.6-live-paging-drill.md) |

## Description

Connect stage alert routing to an approved paging destination and prove end-to-end delivery,
acknowledgement, escalation, and resolution without storing personal contact details in the public
repository.

The 2026-11-23 drill delivered, acknowledged, and resolved one synthetic page. This item stays
open: Alertmanager did not emit that page, the trial policy has one escalation level, and a key
checked after service deletion still received HTTP 202.

## Requirements

- Select managed Alertmanager/PagerDuty-equivalent integration and secret-management path.
- Route a synthetic SpaceOps page through the real delivery channel.
- Record delivery, acknowledgement, escalation, and resolved timestamps.
- Verify redaction and retention policy for notification payloads.
- Disable or retain the integration according to the production-pilot decision.

## Test requirements

- Synthetic page reaches the configured destination.
- Evidence records IDs/timestamps only, with no contact details or secret values.
- Failed delivery blocks the production-pilot go decision or receives an explicit owner/expiry.
