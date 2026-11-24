# RD3.3 - Reproducible import and bounded replay

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

A 12 GB class dataset is useless if the next run silently resamples or mixes missions. Replay must name its slice and its code revision.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Lab replay is built for small fixtures. It has no slice manifest, checksum, or mission pin.

## Requirements

- An import manifest records file checksums, code revision, mission ids, and row counts.
- A replay manifest records the time or segment slice. Rerunning it returns the same event ids.
- Out-of-budget imports stop before filling the disk. The budget is written down before the run.
- CI covers the manifest logic on the tiny slice only.

## Functional and non-functional requirements

- An import manifest records file checksums, code revision, mission ids, and row counts.
- A replay manifest records the time or segment slice. Rerunning it returns the same event ids.
- Out-of-budget imports stop before filling the disk. The budget is written down before the run.
- CI covers the manifest logic on the tiny slice only.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Existing replay runbook, plus a manifest format next to it.
- No new cluster and no paid warehouse.

## Dependencies

- RD3.1
- RD3.2

## Implementation checklist

- [ ] Specify the manifest schema.
- [ ] Make two slice replays identical.
- [ ] Make an over-budget request fail before write.

## Test requirements

- Same manifest and code revision produce the same ids.
- A changed checksum fails the manifest check.
- Synthetic replay tests still pass.

## Testing requirements

- Same manifest and code revision produce the same ids.
- A changed checksum fails the manifest check.
- Synthetic replay tests still pass.

## Security and safety requirements

- Manifests contain checksums and ids, not sample values from the real missions.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A third party can repeat the documented slice without guessing which files were used.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
