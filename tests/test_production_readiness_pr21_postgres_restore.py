"""PR2.1 - Postgres HA posture and backup/restore drill docs."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR = REPO_ROOT / "docs" / "adr" / "0012-postgres-production-pilot-ha-backup.md"
RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "postgres_backup_restore.md"
ADR_INDEX = REPO_ROOT / "docs" / "adr" / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "README.md"
BOARD = REPO_ROOT / "roadmap" / "02.5-production-readiness" / "sprint-2" / "BOARD.md"
PR21 = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "PR2.1-postgres-ha-backup-restore.md"
)
BLOCKED_EVIDENCE = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "evidence"
    / "PR2.1-postgres-restore-drill-2026-07-03.json"
)
EVIDENCE = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "evidence"
    / "PR2.1-postgres-restore-drill-2026-09-26.json"
)


def test_pr21_adr_selects_managed_postgres_and_staged_transition() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert "managed cloud Postgres service" in text
    assert "Cloud SQL for PostgreSQL" in text
    assert "postgres.enabled=false" in text
    assert "external Postgres mode" in text
    assert "RPO target | <= 15 minutes" in text
    assert "RTO target | <= 60 minutes" in text


def test_pr21_runbook_documents_backup_restore_and_integrity_checks() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for required in (
        "Production pilot targets managed Postgres HA",
        "Automated backups",
        "PITR/WAL",
        "pg_dump --format=custom",
        "pg_restore --clean --if-exists",
        "agent_graph_checkpoints",
        "agent_run_queue",
        "dlq_events",
        "llm_usage_ledger",
        "Approval decisions are visible in audit",
        "Data-Loss Boundaries",
    ):
        assert required in text


def test_pr21_evidence_records_completed_restore_and_measurements() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["schema_version"] == "pr21.postgres_restore_drill.v1"
    assert evidence["status"] == "pass"
    assert evidence["rto_rpo"]["target_rto_minutes"] == 60
    assert evidence["rto_rpo"]["measured_rto_seconds"] == 10.32
    assert evidence["rto_rpo"]["measured_rpo_minutes"] == 0
    assert evidence["representative_data"]["llm_usage_ledger"] == 1
    assert evidence["integrity_checks"]["source_restore_counts_match"] is True
    assert evidence["integrity_checks"]["append_only_audit_trigger_restored"] is True
    assert evidence["integrity_checks"]["alembic_revision"] == "20260603_0003"
    assert evidence["result"]["restore"] == "pass"


def test_pr21_preserves_initial_blocker_evidence() -> None:
    evidence = json.loads(BLOCKED_EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["status"] == "blocked"
    assert "Docker daemon is not running" in evidence["attempt"]["blocker"]


def test_pr21_indexes_board_and_spec_are_updated() -> None:
    assert "0012-postgres-production-pilot-ha-backup.md" in ADR_INDEX.read_text(
        encoding="utf-8"
    )
    assert "postgres_backup_restore.md" in DOCS_INDEX.read_text(encoding="utf-8")
    assert "| PR2.1 | Postgres HA posture and backup/restore drill | Done |" in (
        BOARD.read_text(encoding="utf-8")
    )
    pr_text = PR21.read_text(encoding="utf-8")
    assert "## Status\n\nDone" in pr_text
    assert "0012-postgres-production-pilot-ha-backup.md" in pr_text
    assert "postgres_backup_restore.md" in pr_text
    assert "PR2.1-postgres-restore-drill-2026-09-26.json" in pr_text


def test_pr21_local_markdown_links_resolve() -> None:
    for doc in (ADR, RUNBOOK, PR21):
        text = doc.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)#][^)]+)\)", text)
        for href in links:
            target = href.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert (doc.parent / target).resolve().exists(), f"{doc}: {href}"
