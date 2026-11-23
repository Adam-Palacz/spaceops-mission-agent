# PR3.3 - Production pilot deployment plan

## Status

Done

## Description

Define what "production" means for this project. The pilot plan should be explicit, bounded, and
honest: no real spacecraft connectivity unless separately approved.

## Requirements

- Define pilot environment, data classification, users, owners, support hours, cost limits, and
  rollback/teardown criteria.
- Define what actions are allowed, what remains read-only, and what requires approval.
- Define external integrations: telemetry source, ticketing, GitOps repo, identity provider, and
  LLM provider.
- Define success metrics and exit criteria.
- Define legal/compliance assumptions and non-goals.

## Checklist

- [x] Pilot scope documented.
- [x] Owners and support model assigned.
- [x] Integration contracts listed.
- [x] Success metrics and exit criteria defined.
- [x] Non-goals and safety limits explicit.

## Test requirements

- Review checklist signed off in production readiness review.
- Links to runbooks, ADRs, and gates verified.

## Implementation

The canonical [production pilot plan](../../../docs/production_pilot_plan_pr33.md) defines:

- a ten-business-day, staffed, low-volume pilot with no public or unattended operation;
- role ownership, support hours, cost limits, teardown authority, and private named-roster gate;
- data classification, retention, legal assumptions, and an explicit real-spacecraft prohibition;
- allowed/read-only/prohibited actions and fail-closed behavior;
- contracts and admission gates for telemetry, ticketing, GitOps, identity, approvals, LLM,
  observability, and Postgres;
- release, rollback, immediate-stop, success, and exit criteria;
- a PR3.4 sign-off checklist.

The plan deliberately records the current default as `No-go`: PR23-002, PR23-003, and managed
trace/log gates remain unresolved unless PR3.4 approves explicit, time-boxed waivers and
compensating controls.

