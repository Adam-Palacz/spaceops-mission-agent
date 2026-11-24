# AV4 - Detection pipeline

**Status:** Todo. Not started.

**Goal:** Turn a selected detector into incidents the existing agent can investigate, with rollback and drift checks.

## Outcomes

- A detector window can create an incident without writing a command.
- The model id and a rollback path are part of the incident.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
