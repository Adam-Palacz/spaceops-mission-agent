# PR4.8 - SBOM, vulnerability scan, and image signing

| Field | Value |
|-------|-------|
| **Status** | Todo |
| **Owner** | Unassigned |
| **Implements code** | No. This file is a specification only. |

## Objective and rationale

Admission needs a recorded view of what is in the image and which known vulnerabilities were accepted. The repo has Dependabot and a Docker build. It does not have an SBOM, a vulnerability report, or a signature.

## Existing implementation and gaps

The running agent is the single LangGraph path in `apps/agent/graph.py` (triage, investigate, check escalation, decide, act, report). `POST /ingest` in `apps/api/main.py` validates NDJSON and is not behind the approval OIDC dependency. `TelemetryEventV1` in `apps/contracts/v1.py` has `event_id`, `ts`, `channel`, `value`, `subsystem`, `unit`, `source`, and `metadata`, and forbids extra fields. Committed telemetry is the synthetic fixture `data/telemetry/telemetry.ndjson`. NATS JetStream is the ingest boundary (ADR 0002); Postgres stores `telemetry_events`. Replay is described in `docs/runbooks/replay_workflow.md`. MCP tools cover telemetry, KB, ticketing, and GitOps. OPA is fail-closed and the approval API guards restricted actions. Evals live under `evals/`. There is no mission registry, no detector interface, no Yamcs connector, and no edge runtime. Next-gen code is not on this branch. Its specifications remain under `roadmap/deprecated-03-next-gen-autonomy/` and stay Todo.

Gaps for this task:

- `.github/dependabot.yml` opens weekly pip and GitHub Actions updates with a limit of five each. That is not an SBOM.
- CI builds an image. No Syft, Grype, Trivy, or cosign step is in the workflows.

## Requirements

- Generate an SBOM for the API image and for the Python lock inputs that the image actually uses.
- Run a vulnerability scanner and record severities. A finding is either fixed, or accepted with an owner and an expiry.
- Sign the image or document why the current registry cannot verify a signature. Do not claim signing without a verification command.
- Dependency updates stay reviewable. A scanner report does not auto-merge.

## Functional and non-functional requirements

- Generate an SBOM for the API image and for the Python lock inputs that the image actually uses.
- Run a vulnerability scanner and record severities. A finding is either fixed, or accepted with an owner and an expiry.
- Sign the image or document why the current registry cannot verify a signature. Do not claim signing without a verification command.
- Dependency updates stay reviewable. A scanner report does not auto-merge.

- Non-functional: reproducible from a clean checkout, bounded cost, no secrets in git, and no claim that a plan or a unit test is operational evidence.

## Architecture and affected components

- CI workflow and the existing image build. No new cluster.

## Dependencies

- The current CI image build. This task does not wait for RD or AV.

## Implementation checklist

- [ ] Add the scan in CI or record a manual command and its output location.
- [ ] Publish a sanitized summary.
- [ ] List accepted vulnerabilities with an expiry.

## Test requirements

- The summary names the tool version and the image id.
- A critical finding without an owner fails the checklist.

## Testing requirements

- The summary names the tool version and the image id.
- A critical finding without an owner fails the checklist.

## Security and safety requirements

- Scanner output committed to git is sanitized. It must not include registry credentials.
- Do not weaken an existing CI gate to make the scan pass.

- Do not send real or historical mission samples to an external LLM until a reviewed redaction control exists. The synthetic CI fixture is the only telemetry that may enter existing eval jobs.
- Restricted actions stay behind OPA and the approval API. This task adds no command uplink.

## Acceptance criteria

- PR4.7 can cite the summary or an explicit waiver.

## Required execution evidence

- A sanitized note under this sprint's future `evidence/` directory: dataset or tool versions, license record, commands, results, and what was torn down.
- The note must not contain project identifiers, tokens, contact details, or unredacted operational data.

## Definition of Done

Remains Todo until the checklist, the tests named above, and a sanitized evidence note exist. Writing this specification does not implement the task and does not change the 2026-11-23 No-go decision.
