# RD4.1 - Cited source registry for public failure reports

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

The current KB is a lab corpus. A historical case is only usable if the report can be cited and its license allows the stored excerpt.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- KB MCP searches runbooks and postmortems. Those documents are project-authored, not a NASA or ESA corpus.
- `CitationV1` already has `doc_id` and `snippet_id`.

## Requirements

- A source registry records title, publisher, date, URL, license, and whether an excerpt may be stored.
- Candidate sources start with public NASA lessons-learned entries and public ESA anomaly or mission reports. Each item is accepted individually.
- Paywalled, export-controlled, or operational procedures are out of scope. Do not work around access controls.
- No bulk scrape. The registry is a curated list.

## Functional and non-functional requirements

- A source registry records title, publisher, date, URL, license, and whether an excerpt may be stored.
- Candidate sources start with public NASA lessons-learned entries and public ESA anomaly or mission reports. Each item is accepted individually.
- Paywalled, export-controlled, or operational procedures are out of scope. Do not work around access controls.
- No bulk scrape. The registry is a curated list.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- `kb/` and the KB indexer. New documents get stable ids.

## Dependencies

- RD1.3 so evaluation references can live outside the agent-visible KB.

## Implementation checklist

- [ ] Define the registry fields.
- [ ] Add two public, license-checked examples or document that no example passed the license check.
- [ ] Refuse a source with an empty license.

## Test requirements

- Indexer output cites the registry id.
- A missing license fails the import.

## Testing requirements

- Indexer output cites the registry id.
- A missing license fails the import.

## Security and safety requirements

- Store short quotations only when the license allows them.
- Do not include personal data from public reports beyond the published author or role.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- A reviewer can open the registry and see why each document is present.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
