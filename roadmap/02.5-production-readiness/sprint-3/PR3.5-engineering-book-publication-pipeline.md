# PR3.5 - Engineering book and publication pipeline

## Description

Turn the repository's sprint reviews, ADRs, runbooks, diagrams, tests, and evidence artifacts into
one understandable English-language engineering book. The book is a durable memory aid for
maintainers and can be published externally after automated redaction and a small editorial pass.

The canonical source remains Markdown in the repository. PDF, EPUB, and HTML are generated outputs,
not independently edited documents.

## Audience and editions

- **Private engineering edition:** complete implementation details, operational lessons, drill
  evidence, commands, limitations, and internal environment context.
- **Public edition:** the same technical narrative with secrets, project identifiers, addresses,
  internal paths, and sensitive operational details removed or generalized.
- Readers include maintainers returning to the project, engineers evaluating the architecture, and
  non-code stakeholders who need a clear problem -> decision -> implementation -> proof narrative.

## Requirements

- Add an English book source under `docs/book/` with a versioned table of contents.
- Cover problem/goals, architecture, agent workflow, evidence and safety, data durability,
  observability, Kubernetes/cloud, production readiness, testing/evals, operational drills,
  decisions/trade-offs, lessons learned, current limitations, and evidence/ADR appendices.
- Use one source tree to generate navigable HTML plus downloadable PDF and EPUB artifacts.
- Build private and public editions; public generation must redact configured sensitive fields and
  fail when common secret patterns or unapproved private blocks remain.
- Link claims to canonical ADRs, runbooks, sprint/phase reviews, tests, and machine-readable evidence
  instead of copying untraceable facts into the book.
- Provide a repeatable command such as `make book`, plus public and verification variants.
- Collect selected local/stage screenshots through an automated browser workflow where practical:
  SpaceOps UI, Grafana, Prometheus, and Jaeger. Cloud-console screenshots remain optional; prefer
  redacted CLI/IaC evidence for reproducibility.
- Stamp generated artifacts with build date, git commit SHA, edition, and evidence manifest version.
- Publish generated files as CI/release artifacts or documentation-site output; do not commit large
  generated binaries unless the release policy explicitly requires it.

## Chapter pattern

Each substantial chapter should answer:

1. **Why** - the problem and operational risk.
2. **Decision** - what was selected and which alternatives were rejected.
3. **Implementation** - how the system works.
4. **Verification** - tests, drills, and acceptance thresholds.
5. **Evidence** - links to machine-readable artifacts and selected visuals.
6. **Limitations** - what is not yet proven.
7. **Lessons learned** - failures, corrections, and reusable guidance.

## Checklist

- [ ] Book toolchain and `docs/book/` structure selected and documented.
- [ ] Initial English chapters generated and editorially reviewed.
- [ ] Private HTML/PDF/EPUB build is repeatable.
- [ ] Public edition redaction and secret scan pass.
- [ ] Evidence/ADR/sprint-review indexes are generated or validated.
- [ ] Screenshot collector produces deterministic, captioned assets where environments are available.
- [ ] CI or release workflow stores the generated artifacts.
- [ ] Maintenance policy requires book updates at sprint/phase closure.

## Test requirements

- Build smoke test for HTML and at least one downloadable format.
- Local Markdown link and cross-reference validation.
- Public artifact secret/redaction scan using synthetic sensitive fixtures.
- Deterministic manifest test for commit SHA, edition, source list, and evidence hashes.
- Screenshot workflow dry-run when the target services are unavailable.

## Non-goals

- Replacing canonical runbooks, ADRs, sprint reviews, or evidence JSON with prose.
- Automatically publishing without a human review.
- Requiring authenticated cloud-console automation or storing cloud credentials in CI artifacts.
- Generating a separate manually maintained PDF for every sprint.

## Status

Todo.
