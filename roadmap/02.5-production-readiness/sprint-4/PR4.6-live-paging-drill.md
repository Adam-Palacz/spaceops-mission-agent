# PR4.6 - Live paging integration drill

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Closes** | BL-006 |
| **Owner** | On-call lead |
| **Depends on** | PR4.4 |

## Description

Schedule and execute the live notification work defined by
[BL-006](../../backlog/BL-006-live-paging-integration-drill.md), proving delivery,
acknowledgement, escalation, and resolution through the selected paging service.

## Requirements

- Select the approved Alertmanager-to-paging integration and manage its secret through the
  stage/prod secret path.
- Route a synthetic SpaceOps alert through the real destination during an agreed test window.
- Record delivery, acknowledgement, escalation, and resolution timestamps and sanitized IDs.
- Exercise failed-delivery behavior or the provider-supported equivalent.
- Verify payload redaction, notification retention, responder privacy, and escalation ownership.
- Disable and remove temporary integration resources after the drill unless retained by the pilot
  plan.

## Checklist

- [ ] On-call owner, test window, and destination are approved privately.
- [ ] Integration secret and routing are configured without repository disclosure.
- [ ] Synthetic page reaches and is acknowledged through the real channel.
- [ ] Escalation, resolution, and failed-delivery behavior are verified.
- [ ] Evidence and leak scans contain no contact details or secret values.
- [ ] BL-006 is closed or a named owner approves a time-boxed exception.

## Test requirements

- End-to-end timestamps stay within the pilot's notification threshold.
- Incorrect/missing routing secret fails closed and alerts operators through a fallback.
- Resolved notification reaches the expected destination.
- Teardown or retained-integration inventory is recorded.

## Done gate

Prometheus rule evaluation or a local webhook alone is insufficient. A real paging destination and
human acknowledgement are required unless the final review accepts a named, expiring exception.
