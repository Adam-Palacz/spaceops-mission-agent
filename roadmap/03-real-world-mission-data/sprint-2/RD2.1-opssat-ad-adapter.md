# RD2.1 - OPSSAT-AD labeled-segment adapter

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

This is the detection dataset: short univariate segments with an official split and segment labels. It is not a root-cause corpus and it is not the re-entry campaign.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- No OPS-SAT files are in the repo.
- The nine channels are magnetometer `CADC0872`, `CADC0873`, `CADC0874` and photodiodes `CADC0884`, `CADC0886`, `CADC0888`, `CADC0890`, `CADC0892`, `CADC0894`.
- The released dataset.csv has 1594 rows with train=1 and 529 with train=0. The paper prints 1494 in the training total, while its training class counts sum to 1594. Preserve the released flag.

## Requirements

- Download is manual. The repo stores the adapter and a checksum, not `segments.csv` (about 18 MB) unless a later decision accepts the CC BY 4.0 file.
- Labels and the `train` flag go to the ground-truth store, not into the telemetry tool.
- Preserve segment id, channel, sampling, and timestamp. Do not resample in this task.
- Cite Ruszczak, Kotowski, Evans, and Nalepa, Zenodo 10.5281/zenodo.12588359, and the Scientific Data article.

## Functional and non-functional requirements

- Download is manual. The repo stores the adapter and a checksum, not `segments.csv` (about 18 MB) unless a later decision accepts the CC BY 4.0 file.
- Labels and the `train` flag go to the ground-truth store, not into the telemetry tool.
- Preserve segment id, channel, sampling, and timestamp. Do not resample in this task.
- Cite Ruszczak, Kotowski, Evans, and Nalepa, Zenodo 10.5281/zenodo.12588359, and the Scientific Data article.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- RD1 adapter plus the OPSSAT-AD channel registry from RD1.2.
- Dataset id distinct from the re-entry product.

## Dependencies

- RD1.1
- RD1.2
- RD1.3
- RD1.4

## Implementation checklist

- [ ] Record license CC BY 4.0 and the two file checksums published on Zenodo.
- [ ] Implement the adapter against a tiny checked-in synthetic lookalike, not the real file, for CI.
- [ ] Document the official 1594/529 counts as the expected import audit.

## Test requirements

- The lookalike maps values to telemetry and labels to ground truth.
- Train and test membership follows the source flag, not a new random split.
- CI does not download Zenodo.

## Testing requirements

- The lookalike maps values to telemetry and labels to ground truth.
- Train and test membership follows the source flag, not a new random split.
- CI does not download Zenodo.

## Security and safety requirements

- Do not treat a labeled anomaly as a recommended spacecraft command. The paper describes shapes, gaps, zeros, and peaks that should notify an operator.
- Do not claim the random split proves time-separated generalization.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- An import report can show 2123 segments when the real file is present, or an explicit skipped state when it is absent.
- No re-entry column appears in this dataset id.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
