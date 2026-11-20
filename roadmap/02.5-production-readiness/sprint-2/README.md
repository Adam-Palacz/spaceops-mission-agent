# PR2 - Data Durability, Secrets, and Security

**Goal:** harden the production data plane and control plane: backups, restore drills, secrets
rotation, audit integrity, trace/log retention, and security review.

## Outcomes

- Postgres has a production-pilot backup/restore path with measured RTO/RPO.
- Secrets are managed and rotated through the stage/prod path.
- OPA, approval, MCP, audit, LLM gateway, and platform ops boundaries pass security review.
- Trace/log retention and privacy policy are documented.

## Definition of done

- [x] PR2 board is complete.
- [x] Backup/restore drill evidence exists.
- [x] Secret rotation evidence exists.
- [x] Security review records findings and owners.
- [x] Retention/privacy decisions are documented.

See [BOARD.md](BOARD.md) and [SPRINT_REVIEW.md](SPRINT_REVIEW.md).

