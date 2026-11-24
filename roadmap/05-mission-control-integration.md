# 05 - Mission Control Integration

**Status:** Planned. This document does not implement the phase.
**Execution:** [05-mission-control-integration/](05-mission-control-integration/)

Sit beside a mission control system as a read-only analyst. Yamcs is the local stand-in. SpaceOps does not replace it and does not send commands.

## Why this phase exists

Historical files do not exercise parameter definitions, alarms, or a live public stream. A connector makes those operational objects visible without taking control of the spacecraft.

## Reconciliation with the repository

NATS, telemetry MCP, the approval API, and the Next.js UI already exist. Yamcs does not. Yamcs server is AGPL-3.0 and its API and clients are LGPL, with a commercial alternative from the copyright holder. The first integration is a local read-only process: Parameter Archive, alarm list, and Mission Database or XTCE export. Command stacks in Yamcs are out of scope. SatNOGS is a later public stream, not a source of ESA housekeeping and not a substitute for OPSSAT-AD.

## Exit gate

- An operator can browse parameters and alarms from a local Yamcs and open a SpaceOps investigation without a command path.
- The connector's license decision is recorded before any combined distribution.
- Live public telemetry, historical benchmarks, and synthetic CI fixtures remain three separate flows.

## Non-goals

- Sending telecommands or becoming the system of record for a mission.
- Flight certification of the connector.
- Mixing SatNOGS frames into the OPSSAT-AD or ESA-AD benchmarks.
