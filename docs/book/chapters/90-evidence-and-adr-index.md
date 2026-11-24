# Appendix: evidence, ADR, and review index

## Canonical sources

- [Project goals](../../../roadmap/goals.md)
- [Production Scale strategy](../../../roadmap/02-production-scale.md)
- [Production Readiness strategy](../../../roadmap/02.5-production-readiness.md)
- [Deprecated next-gen vision](../../../roadmap/deprecated-03-next-gen-autonomy.md)
- [ADR index](../../adr/README.md)
- [Documentation index](../../README.md)

## Phase and sprint reviews

- [Production Scale phase review](../../../roadmap/02-production-scale/PHASE_REVIEW.md)
- [PR1 sprint review](../../../roadmap/02.5-production-readiness/sprint-1/SPRINT_REVIEW.md)
- [PR2 sprint review](../../../roadmap/02.5-production-readiness/sprint-2/SPRINT_REVIEW.md)
- [PR3 closure note](../../../roadmap/02.5-production-readiness/sprint-3/SPRINT_REVIEW.md)
- [Production Readiness phase review](../../../roadmap/02.5-production-readiness/PHASE_REVIEW.md)

## Operational runbooks

- [Environment promotion](../../runbooks/environment_promotion.md)
- [Release gate](../../runbooks/release_promotion_gate_pr31.md)
- [Incident/on-call game day](../../runbooks/incident_oncall_game_day_pr32.md)
- [Stage operation](../../runbooks/stage_operating_policy.md)
- [Backup/restore](../../runbooks/postgres_backup_restore.md)
- [Secret rotation](../../runbooks/secrets_rotation_pr22.md)
- [Kubernetes rollback](../../runbooks/k8s_rollout_rollback.md)
- [Queue/DLQ recovery](../../runbooks/queue_dlq_recovery.md)

## Machine-readable evidence

Evidence files listed in `book.yml` are hashed into the generated manifest:

- PR1.4 pilot-short soak/failure run;
- PR2.2 live GSM rotation;
- PR2.3 security review;
- PR3.1 static and live release gates;
- PR3.2 API-outage rollback game day.

The manifest proves which source/evidence bytes were used for one generated edition. It does not
prove the truth of unexecuted claims and does not replace artifact signatures or a trusted
timestamp.

## Publication checklist

- Build private and public editions from the same commit.
- Verify source links and evidence hashes.
- Confirm public private-block removal and secret scan.
- Review screenshots and captions.
- Record the generated manifest with CI/release artifacts.
- Obtain human editorial and security approval before publication.
