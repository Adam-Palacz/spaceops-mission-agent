# PR3.1 - Release smoke/e2e promotion gates

## Status

Done

## Description

Define and automate promotion gates so releases cannot move to stage/prod without health, scenario,
safety, and rollback evidence.

## Requirements

- Gate includes lint/tests, Helm template/lint, migration dry-run, health check, demo scenarios A/B,
  approval flow, OPA deny/fail-closed check, queue/DLQ check, and rollback readiness.
- Gate can run in CI or as a documented pre-promotion command.
- Gate output is stored as release evidence.
- Failed gate blocks promotion.

## Checklist

- [x] Release gate command or CI workflow added.
- [x] Gate covers health, scenarios, safety, queue, migration, and rollback readiness.
- [x] Evidence artifact path documented.
- [x] Environment promotion runbook updated.
- [x] Failure behavior documented.

## Test requirements

- CI-safe dry-run where cloud credentials are absent.
- Stage execution evidence before phase closure.

## Implementation

- `scripts/release_gate_pr31.py` provides `dry-run`, blocking `ci`, and blocking `stage` modes.
- `.github/workflows/release-gate.yml` stores JSON artifacts and fails when an executed gate fails.
- `make release-gate-pr31` is the credential-free planning command.
- [Release promotion gate runbook](../../../docs/runbooks/release_promotion_gate_pr31.md) defines
  operator use, evidence retention, failure semantics, and rollback handling.
- [Environment promotion](../../../docs/runbooks/environment_promotion.md) requires passing CI and
  stage reports for the same immutable release ID.

## Live evidence - 2026-11-22

Release candidate `pr31-5101260278813f9c` was exercised on a temporary GKE stage using one
non-preemptible `e2-standard-4` node:

- [Static gate evidence](evidence/PR3.1-static-ci-2026-11-22.json): lint, mypy, 482 tests
  (4 skipped), approval/OPA checks, Helm stage/prod lint and template, and offline migration SQL all
  passed.
- [Live stage evidence](evidence/PR3.1-live-stage-2026-11-22.json): health, telemetry ingest,
  Scenario A report/evidence, Scenario B `no_evidence` escalation, telemetry persister readiness,
  DLQ threshold (`0` rows), Helm rollback values snapshot, and immutable image reference snapshot
  all passed.
- The first static attempt correctly blocked on three failures. Two were caused by the validation
  container lacking a `gcloud` executable; the actionable repository failure was the missing
  portfolio link for the new runbook. The link was added before the passing rerun.
- Stage used synthetic non-production credentials except for the existing lab OpenAI key; no secret
  values are stored in evidence.
- After evidence capture, Helm workloads and all paid GCP resources were removed. Final checks
  returned zero clusters, repositories, instances, disks, forwarding rules, reserved addresses, and
  GSM secrets. Terraform retains only the billing budget, notification channel, and their APIs.

