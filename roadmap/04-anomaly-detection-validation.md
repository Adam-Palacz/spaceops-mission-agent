# 04 - Anomaly Detection and Scientific Validation

**Status:** Planned. This document does not implement the phase.
**Execution:** [04-anomaly-detection-validation/](04-anomaly-detection-validation/)

Measure detection and agent reasoning separately. Publish a comparison that is allowed to show the agent is not better than a simpler baseline.

## Why this phase exists

A mission-ops demo that cannot be scored against a fixed split and a dumb baseline does not support a scientific or operational claim. This phase builds the measurement before it adds models.

## Reconciliation with the repository

The repository has semantic evals, golden replays, and behavior metrics for the lab agent. It has no detector interface, no MLflow tracking, no Isolation Forest, and no ESA metric implementation. OPSSAT-AD's official comparison split is the `train` flag: 1594 train and 529 test segments, counted from the released CSV. That split is stratified random, so a score on it is not a chronological-operations claim. ESA-ADB publishes its own operational metrics and currently treats rare nominal events as anomalies in its algorithm runner. SpaceOps reports that convention separately and does not adopt it as the only score. Agent diagnosis is scored only on RD4 cases with a known cause, never on a binary segment label.

## Exit gate

- A reproducible report compares the named baselines on a frozen test split.
- Detection, localisation, root cause, agent reasoning, and action planning are separate tables.
- The report states limitations, including leakage and any case where a simpler baseline wins.
- No model or prompt is selected by looking at the official test split.

## Non-goals

- Implementing every architecture in the literature.
- Declaring an operational detector ready for a spacecraft.
- Using the production-admission review as a substitute for this report.
