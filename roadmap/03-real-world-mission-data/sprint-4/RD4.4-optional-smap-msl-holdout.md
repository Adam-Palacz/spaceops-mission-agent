# RD4.4 - Optional SMAP/MSL external holdout

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Owner** | Unassigned |
| **Implements code** | Yes. The decision is a waiver. No samples were downloaded. |

## Objective and rationale

The NASA SMAP and MSL telemetry used by the public anomaly-detection literature is a useful later holdout. It is not part of the phase exit, and its license is not assumed.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The repo has no SMAP or MSL data and no license note for the Hundman et al. telemetry release.

## Requirements

- Before any download, record the exact distribution, version, and license.
- If the license is missing or incompatible, close this task as waived without data.
- If accepted, store it as its own dataset id and do not tune prompts or models on it before the phase 04 report.
- Do not make RD4 or phase 03 exit depend on this task.

## Functional and non-functional requirements

- Before any download, record the exact distribution, version, and license.
- If the license is missing or incompatible, close this task as waived without data.
- If accepted, store it as its own dataset id and do not tune prompts or models on it before the phase 04 report.
- Do not make RD4 or phase 03 exit depend on this task.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- Same adapter interface. No new detector.

## Dependencies

- RD1. A license record is the real gate.

## Implementation checklist

- [x] Write the license decision, including a no-go decision if the terms are unclear.
- [x] Do not add channels or samples until that decision is allow.

## Test requirements

- The task can complete as an explicit waiver.
- An allow decision still keeps the files out of CI.

## Testing requirements

- The task can complete as an explicit waiver.
- An allow decision still keeps the files out of CI.

## Security and safety requirements

- No attempt to obtain the data from an unofficial mirror.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The phase review states either a license citation or a waiver. It does not imply the data was used.

## Required execution evidence

- Sanitized note: [evidence/RD4.4-smap-msl-waiver-2026-11-27.json](evidence/RD4.4-smap-msl-waiver-2026-11-27.json).
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Telemanom v2.0 is the distribution that was checked. The README calls the software Apache-2.0. `LICENSE.txt` is a 2018 Caltech software notice that reserves all rights. The README points at a third-party Kaggle dataset for the telemetry, and that mirror was not used. No separate sample license was recorded, so the task is waived without data. Reserved dataset ids are not in the mission registry. An allow decision still refuses CI files. This does not change the 2026-11-23 No-go decision, and phase 03 does not depend on this holdout.
