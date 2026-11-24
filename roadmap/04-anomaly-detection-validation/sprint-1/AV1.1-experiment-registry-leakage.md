# AV1.1 - Experiment registry and leakage controls

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Later model work is comparable only if the split, code revision, and features are pinned before the run.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Evals today score lab fixtures. They do not record a dataset checksum or a forbidden-column list.
- The official OPSSAT-AD split is not chronological. A random re-split would make published numbers incomparable.

## Requirements

- Registry fields: dataset id, checksum, split name, code revision, feature set, and seed.
- The official OPSSAT-AD score uses the published `train` flag. Any other split is labeled exploratory.
- Features computed with test-segment statistics fail the leakage check.
- Ground-truth columns are in the forbidden feature list.

## Functional and non-functional requirements

- Registry fields: dataset id, checksum, split name, code revision, feature set, and seed.
- The official OPSSAT-AD score uses the published `train` flag. Any other split is labeled exploratory.
- Features computed with test-segment statistics fail the leakage check.
- Ground-truth columns are in the forbidden feature list.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- RD1 provenance and RD3 manifests. A local file or SQLite registry is enough. MLflow is AV1.2.

## Dependencies

- RD1. RD2.1 for the OPSSAT-AD audit counts. RD3 before an ESA-ADB experiment is registered.

## Implementation checklist

- [ ] Specify the registry and the forbidden-column check.
- [ ] Add a failing test for a feature that uses the label.
- [ ] Record that the official split is stratified random.

## Test requirements

- A test-set statistic in a training feature is rejected.
- Two runs with the same registry id and revision resolve the same split.

## Testing requirements

- A test-set statistic in a training feature is rejected.
- Two runs with the same registry id and revision resolve the same split.

## Security and safety requirements

- The registry stores ids and metrics, not raw mission samples.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- AV2 cannot start a reported run without a registry id.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
