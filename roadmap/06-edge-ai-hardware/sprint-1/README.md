# EA1 - Edge detector runtime

**Status:** Todo. Not started.

**Goal:** Run one selected detector on a Jetson-class board, or record that the board is unavailable.

## Outcomes

- ONNX or TensorRT artifacts for the selected detector.
- A precision comparison that can be incomplete if the hardware is missing.

## Definition of done

- [ ] Every row on [BOARD.md](BOARD.md) is Done with the evidence its spec requires.
- [ ] Synthetic CI fixtures under `data/telemetry/` and `evals/fixtures/` are unchanged by historical or live data.
- [ ] No task is marked Done from this planning document.

## How to work

Read [the phase README](../README.md) and [the master roadmap](../../MASTER.md) before implementation.
