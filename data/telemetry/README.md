# Telemetry NDJSON

Sample and ingest-output **telemetry** lines for `POST /ingest?source=telemetry` and agent triage.

| File | Role |
|------|------|
| `telemetry.ndjson` | Committed fixture (ts, channel, value, subsystem, unit). |
| `ingest_*.ndjson` | Written by ingest when NATS is off (legacy lab path). |

Schema and curl examples: [../README.md](../README.md).

Historical mission datasets, live public streams, and this CI fixture stay in separate flows.
Do not add OPS-SAT, ESA-AD, or SatNOGS samples to `telemetry.ndjson`. The plan is
[phase 03](../../roadmap/03-real-world-mission-data/README.md).

Historical mission datasets, live public streams, and this CI fixture stay in separate flows.
Do not add OPS-SAT, ESA-AD, or SatNOGS samples to `telemetry.ndjson`. The plan is
[phase 03](../../roadmap/03-real-world-mission-data/README.md).

Historical mission datasets, live public streams, and this CI fixture stay in separate flows.
Do not add OPS-SAT, ESA-AD, or SatNOGS samples to `telemetry.ndjson`. The plan is
[phase 03](../../roadmap/03-real-world-mission-data/README.md).
