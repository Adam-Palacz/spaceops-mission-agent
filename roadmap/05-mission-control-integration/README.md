# Phase 05: Mission Control Integration

**Status:** Planned. Not started.
**Priority:** P2. After the RD1 contract and, for streaming detection, after AV4.
**Strategy:** [05-mission-control-integration.md](../05-mission-control-integration.md)
**Master roadmap:** [MASTER.md](../MASTER.md)

Sit beside a mission control system as a read-only analyst. Yamcs is the local stand-in. SpaceOps does not replace it and does not send commands.

## Sprint map

| Sprint | Folder | Goal |
|--------|--------|------|
| **MC1** | [sprint-1/](sprint-1/) | Local Yamcs read-only connector |
| **MC2** | [sprint-2/](sprint-2/) | Mission metadata |
| **MC3** | [sprint-3/](sprint-3/) | Public telemetry stream |
| **MC4** | [sprint-4/](sprint-4/) | Operator investigation view |

## Exit gate

- An operator can browse parameters and alarms from a local Yamcs and open a SpaceOps investigation without a command path.
- The connector's license decision is recorded before any combined distribution.
- Live public telemetry, historical benchmarks, and synthetic CI fixtures remain three separate flows.

## Non-goals

- Sending telecommands or becoming the system of record for a mission.
- Flight certification of the connector.
- Mixing SatNOGS frames into the OPSSAT-AD or ESA-AD benchmarks.

Passing this gate does not change the production-admission decision and does not declare flight readiness.
