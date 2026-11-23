# PR3.2 - Incident, on-call, and rollback drills

## Status

Done

## Description

Convert runbooks into executed operational practice. A production pilot needs proof that operators
can detect, triage, mitigate, and roll back failures.

## Requirements

- Define incident classes: API outage, worker stuck, OPA unavailable, Postgres degraded, queue/DLQ
  growth, LLM backend outage, budget cap hit, unsafe-action regression.
- Run at least one game day covering detection, escalation, mitigation, and rollback.
- Define on-call roles, escalation path, and communication templates.
- Record timelines and improvements.

## Checklist

- [x] Incident drill plan added.
- [x] On-call/escalation roles documented.
- [x] At least one game day executed.
- [x] Rollback drill executed or reused from release gate evidence.
- [x] Post-drill action-item schema and ownership policy defined.

## Test requirements

- Drill evidence and follow-up issue/task links.
- Alert firing or synthetic evidence for at least one incident class.

## Implementation

- [Incident/on-call game-day runbook](../../../docs/runbooks/incident_oncall_game_day_pr32.md)
  defines all required incident classes, severity targets, roles, escalation, communication
  templates, evidence handling, and follow-up ownership.
- `scripts/pr32_game_day.ps1` automates a local kind API-outage drill and actual Helm rollback.

## Game-day evidence - 2026-11-23

[Local kind evidence](evidence/PR3.2-game-day-local-2026-11-23.json) records a passing SEV-2 API
outage drill:

- healthy Helm revision 1 was verified;
- a game-day marker created revision 2;
- API replicas were scaled to zero and a synthetic `APIUnavailable` signal fired;
- the primary on-call captured deployment/pod state and the simulated IC selected rollback;
- `helm rollback spaceops 1` restored API health and removed the marker in 15.46 seconds;
- the timeline covers preparation, injection, detection, triage, escalation, mitigation, and
  verification.

No production traffic, cloud infrastructure, or secrets were involved. Action PR3.2-A1 is complete.
Deferred real paging delivery is tracked as
[BL-006](../../backlog/BL-006-live-paging-integration-drill.md), owned by the on-call lead and due
before the production pilot.

