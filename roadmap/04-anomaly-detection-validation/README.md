# Phase 04: Anomaly Detection and Scientific Validation

**Status:** In progress. AV1.1 registers the official OPSSAT-AD split and rejects leaky features. AV1.2 and later sprints stay Todo.
**Priority:** P1. Starts after RD1, and uses RD2 or RD3 data only under that phase's isolation rules.
**Strategy:** [04-anomaly-detection-validation.md](../04-anomaly-detection-validation.md)
**Master roadmap:** [MASTER.md](../MASTER.md)

Measure detection and agent reasoning separately. Publish a comparison that is allowed to show the agent is not better than a simpler baseline.

## Sprint map

| Sprint | Folder | Goal |
|--------|--------|------|
| **AV1** | [sprint-1/](sprint-1/) | Benchmark method |
| **AV2** | [sprint-2/](sprint-2/) | Statistical and classical baselines |
| **AV3** | [sprint-3/](sprint-3/) | Representative learned detectors |
| **AV4** | [sprint-4/](sprint-4/) | Detection pipeline |
| **AV5** | [sprint-5/](sprint-5/) | Agent reasoning benchmark |
| **AV6** | [sprint-6/](sprint-6/) | Comparative study |

## Independent evaluation tracks

AV5.1 may start on synthetic scorer cases while RD4 is being prepared. The historical AV5 runs require RD4.3, the RD2.3 read-only profile and an eligible model path, not AV2-AV4. AV6 combines the independent detector and agent tracks. Public-report reconstruction and blinded/perturbed reasoning cohorts must be reported separately with memorization controls; no public historical score proves unseen-event generalization.

## Exit gate

- A reproducible report compares the named baselines on a frozen test split.
- Detection, localisation, root cause, agent reasoning, and action planning are separate tables.
- The report states limitations, including leakage and any case where a simpler baseline wins.
- No model or prompt is selected by looking at the official test split.

## Non-goals

- Implementing every architecture in the literature.
- Declaring an operational detector ready for a spacecraft.
- Using the production-admission review as a substitute for this report.

Passing this gate does not change the production-admission decision and does not declare flight readiness.
