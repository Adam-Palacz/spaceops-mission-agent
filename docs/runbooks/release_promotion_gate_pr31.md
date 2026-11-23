# PR3.1 release promotion gate

This runbook defines the blocking gate used before promoting a SpaceOps release candidate to stage
or production. The canonical command is `scripts/release_gate_pr31.py`; every run writes JSON
evidence under `artifacts/release-gates/` unless another path is supplied.

## Gate coverage

The CI portion checks:

- Ruff, mypy, and the full pytest suite;
- approval flow and OPA deny/fail-closed tests;
- Helm lint for stage and production plus a rendered stage chart;
- an offline Alembic `upgrade head --sql` migration dry-run.

The stage portion additionally checks:

- API health;
- live Scenario A/B behavior;
- telemetry persister availability and a zero-row DLQ threshold by default;
- a Helm values snapshot and deployed API image snapshot for rollback.

The rollback snapshots are evidence inputs, not an automatic rollback. An operator must still use
the tested [rollout/rollback procedure](k8s_rollout_rollback.md).

## Commands

Plan the gate without credentials or external writes:

```bash
make release-gate-pr31
```

Run blocking CI/static checks:

```bash
python scripts/release_gate_pr31.py --mode ci \
  --release-id <immutable-commit-sha> \
  --evidence artifacts/release-gates/<sha>-ci.json
```

Run against an existing stage deployment:

```bash
python scripts/release_gate_pr31.py --mode stage \
  --api-url https://<stage-api> \
  --release-id <immutable-commit-sha> \
  --operator <name> \
  --evidence artifacts/release-gates/<sha>-stage.json
```

On Windows hosts where Application Control blocks the repository Python runtime, use the equivalent
PowerShell stage runner after a passing static artifact exists:

```powershell
.\scripts\pr31_live_release_gate.ps1 `
  -ApiUrl http://<stage-api>:8000 `
  -ReleaseId <immutable-release-id> `
  -StaticEvidencePath artifacts/release-gates/<release>-ci.json `
  -EvidencePath artifacts/release-gates/<release>-stage.json
```

The stage command uses the current `kubectl`/Helm context and does not create infrastructure. The
release candidate must already be deployed. Use a temporary stage window and tear it down according
to the [stage operating policy](stage_operating_policy.md).

## Blocking behavior

- Steps execute in order and stop on the first failure.
- A failed command, unreachable endpoint, malformed DLQ response, or DLQ count above the configured
  threshold produces exit code `1`.
- Promotion is forbidden unless the final JSON has `"result": "pass"` and every step is `pass`.
- Dry-run output is only a plan and is never promotion evidence.
- A waiver requires the emergency process in [CI gating policy](ci_gating_policy.md); the failed
  artifact must remain attached to the release decision.

## Evidence handling

Keep the CI and stage JSON files together using the immutable release ID. The report contains command
arguments, timestamps, return codes, bounded output tails, and SHA-256 hashes of full command output.
It must not contain secret values. Before publication, run the engineering-book redaction checks from
PR3.5.

The GitHub workflow uploads the dry-run report for pull requests and supports an explicit blocking
`ci` run through `workflow_dispatch`. Live stage evidence is intentionally operator-triggered because
it needs a deployed cluster and authenticated context.

## Promotion decision

1. Verify the release ID matches the deployed image/commit.
2. Require passing CI and stage artifacts.
3. Record the approver and links to both artifacts.
4. Confirm the rollback snapshots and rollback runbook.
5. Promote, monitor SLOs, and retain evidence with the release record.
