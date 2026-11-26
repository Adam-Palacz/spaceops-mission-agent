# RD2.2 - OPS-SAT re-entry telemetry adapter

| Field | Value |
|-------|-------|
| **Status** | Done |
| **Owner** | Unassigned |
| **Implements code** | Yes. `apps/mission_data/opssat_reentry.py` maps the public columns and refuses the real file. |

## Objective and rationale

The May 2024 UHF campaign is physical end-of-life telemetry: temperatures, battery voltage, coarse spin, photodiode angles, and derived orbit fields. It has no OPSSAT-AD labels.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- The public analysis lists `uhf_telemetry.csv` columns including `Battery_Voltage`, `Battery_Temp`, coarse spin, six `PD*_CSS_theta` values, several temperatures, RSSI, and derived altitude.
- This roadmap pass did not find a machine-readable license on the analysis page. Ingest of the real file stays blocked until that license is written down.
- Photodiode names resemble OPSSAT-AD channels but come from another campaign. They must not share segment labels.

## Requirements

- Separate dataset id and registry entries from RD2.1.
- Map only columns described by the public analysis. Derived latitude, longitude, and altitude stay marked derived, not spacecraft sensors.
- Reception timestamp is ground receipt time, not necessarily onboard generation time. Record that distinction.
- No anomaly labels are created for this file.

## Functional and non-functional requirements

- Separate dataset id and registry entries from RD2.1.
- Map only columns described by the public analysis. Derived latitude, longitude, and altitude stay marked derived, not spacecraft sensors.
- Reception timestamp is ground receipt time, not necessarily onboard generation time. Record that distinction.
- No anomaly labels are created for this file.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- RD1 adapter. Replay through existing ingest once the license gate is open.
- Do not join to OPSSAT-AD on channel name.

## Dependencies

- RD1.1
- RD1.2
- RD1.3
- A recorded license or an explicit decision to keep the adapter offline.

## Implementation checklist

- [x] Write the column map and the ground-receipt-time caveat.
- [x] Block the real import behind a license record.
- [x] Add a fixture test that a re-entry row cannot receive an OPSSAT-AD label.

## Test requirements

- License missing means the loader refuses the real path.
- A mapped battery-voltage sample keeps its unit and dataset id.
- Cross-join to OPSSAT-AD labels returns empty.

## Testing requirements

- License missing means the loader refuses the real path.
- A mapped battery-voltage sample keeps its unit and dataset id.
- Cross-join to OPSSAT-AD labels returns empty.

## Security and safety requirements

- Amateur-collected frames are public observations, not an authorization to command or to reconstruct restricted procedures.
- Do not publish station-operator identities from frame metadata.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- The dataset can be replayed or is explicitly blocked with the missing license named.
- Phase exit can count it as a second product only after the license gate passes.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Done for the license gate: the column map, the refusal tests, and [evidence/RD2.2-reentry-license-gate-2026-11-26.json](evidence/RD2.2-reentry-license-gate-2026-11-26.json) are in place. The real campaign is still unread. This does not change the 2026-11-23 No-go decision, and phase exit still cannot count the campaign as a second imported product.
