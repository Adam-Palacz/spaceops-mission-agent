# Architecture and agent workflow

## Why

An agent that can call tools needs stronger boundaries than a chat interface. It must separate
reasoning from execution, preserve evidence lineage, survive dependency failure, and make unsafe
states visible to operators.

## Decision

SpaceOps uses a LangGraph state machine behind a FastAPI API. External capabilities are exposed as
small MCP services. OPA evaluates restricted actions before approval, and the approval result is
audited. Postgres is the durable state boundary; NATS decouples telemetry ingestion.

The architecture favors explicit services and contracts over an unrestricted agent shell. See the
[architecture overview](../../architecture.md), [agent graph](../../agent/langgraph_state_flow.mmd),
and [ADR index](../../adr/README.md).

## Implementation

The main flow is:

1. ingest and validate telemetry;
2. triage and classify the incident;
3. investigate through telemetry/knowledge MCP tools;
4. decide with confidence and evidence checks;
5. send restricted actions through OPA and approval;
6. return a structured report or escalation packet;
7. emit audit, metrics, logs, and traces.

The strict output envelope is described in [output schema](../../output_schema.md). Durable
checkpoint and worker variants are documented in
[ADR 0003](../../adr/0003-langgraph-durable-checkpoint-postgres.md).

## Verification

Graph behavior, schema, OPA failure, approval transitions, checkpoint recovery, MCP resilience, and
tool guardrails are exercised under `tests/`. Release promotion additionally runs live Scenario A
(report/evidence) and Scenario B (controlled escalation).

## Evidence

The [PR3.1 release evidence](../../../roadmap/02.5-production-readiness/sprint-3/PR3.1-release-gates.md)
connects static tests with the same release candidate exercised on temporary GKE.

## Limitations

Approval identity still relies on a shared-key model, and approval execution is not atomically
claimed across replicas. These are High findings PR23-002 and PR23-003, not documentation gaps.

## Lessons learned

Fail-closed behavior must exist at every boundary. OPA defaults, provider errors, missing evidence,
budget exhaustion, malformed output, and unavailable approvals cannot depend on the model choosing
the safe interpretation.
