# Preface: problem, goals, and scope

## Why

Space operations produce incomplete telemetry, ambiguous symptoms, operational pressure, and a
high cost of unsafe action. SpaceOps Mission Agent Lab explores whether an evidence-first agent can
reduce triage time without pretending that a language model is a flight controller.

The target is assisted decision support: ingest an incident, investigate through bounded tools,
apply policy, request human approval where required, and produce either a supported report or an
explicit escalation packet.

## Decision

The project chose a safety-first L1/L2 baseline before adding deeper autonomy:

- evidence is required before conclusions;
- uncertainty becomes escalation, not invented certainty;
- restricted actions require OPA and human approval;
- all external capabilities use named MCP tools;
- production-like operation is proven with tests and drills, not labels.

Canonical goals and requirements live in
[roadmap goals](../../../roadmap/goals.md), while execution history lives in the
[roadmap index](../../../roadmap/README.md).

## Implementation

The repository combines FastAPI, LangGraph, MCP services, OPA, Postgres/pgvector, NATS, OpenTelemetry,
Prometheus/Grafana, Docker, Helm, and Terraform. Environment policy separates local development,
isolated stage, and a future bounded production pilot.

## Verification

Verification layers include unit/integration tests, semantic and safety evals, replay/golden checks,
Helm/Terraform validation, live stage scenarios, backup/restore, secret rotation, failure injection,
release gates, and an incident rollback game day.

## Evidence

Start with the [Production Scale phase review](../../../roadmap/02-production-scale/PHASE_REVIEW.md)
and the current [Production Readiness review](../../../roadmap/02.5-production-readiness/PHASE_REVIEW.md).

## Limitations

The current production-pilot decision is No-go. Real spacecraft command/control, unattended L3/L4
operation, public multi-tenancy, and regulatory certification are outside the demonstrated scope.

## Lessons learned

Roadmap status is not operational proof. The most valuable project results often came from failed
live attempts that exposed cloud naming, storage affinity, rollback, identity, or tooling
assumptions before they became production incidents.
