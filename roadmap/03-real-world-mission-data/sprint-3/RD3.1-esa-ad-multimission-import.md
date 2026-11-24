# RD3.1 - Multi-mission ESA-AD import

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

ESA-AD is the large curated telemetry set behind ESA-ADB. The dataset has three anonymized missions. The benchmark protocol uses two. Those facts must stay visible in the import.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- Nothing in the repo streams multi-gigabyte mission archives.
- Published scale is on the order of 224 channels and hundreds of millions of points per mission. The files must not be committed.

## Requirements

- Import Mission1, Mission2, and Mission3 as separate dataset contexts from Zenodo 10.5281/zenodo.12528696.
- Record CC BY 3.0 IGO for the data and MIT for the `kplabs-pl/ESA-ADB` code. Do not vendor the benchmark framework just to read the files.
- Anonymized mission names stay anonymized. Do not try to identify the spacecraft.
- The benchmark membership flag is explicit: Mission1 and Mission2 are in the published benchmark; Mission3 is held out of that score.

## Functional and non-functional requirements

- Import Mission1, Mission2, and Mission3 as separate dataset contexts from Zenodo 10.5281/zenodo.12528696.
- Record CC BY 3.0 IGO for the data and MIT for the `kplabs-pl/ESA-ADB` code. Do not vendor the benchmark framework just to read the files.
- Anonymized mission names stay anonymized. Do not try to identify the spacecraft.
- The benchmark membership flag is explicit: Mission1 and Mission2 are in the published benchmark; Mission3 is held out of that score.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- RD1 adapter and registry. Postgres or file partitions keyed by mission.
- Existing NATS path only if a bounded replay slice is published. Bulk load may bypass NATS and still emit `TelemetryEventV1`.

## Dependencies

- RD1 complete. RD2 is not a technical blocker, but RD1 isolation must already exist.

## Implementation checklist

- [ ] Document the Zenodo layout and checksums after download.
- [ ] Implement a streaming reader that can be tested on a tiny generated slice.
- [ ] Record disk and runtime budgets before any full import.

## Test requirements

- A slice from mission A is invisible to a mission B query.
- The full files are absent in CI.
- Mission3 cannot be included in a benchmark score without an explicit override that the report prints.

## Testing requirements

- A slice from mission A is invisible to a mission B query.
- The full files are absent in CI.
- Mission3 cannot be included in a benchmark score without an explicit override that the report prints.

## Security and safety requirements

- Do not attempt to de-anonymize missions.
- Local import only. No upload of ESA-AD to an external service.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reviewer can see three contexts, two of which are marked benchmark members.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
