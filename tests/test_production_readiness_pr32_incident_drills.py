"""PR3.2 incident/on-call/game-day documentation and evidence tests."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "runbooks" / "incident_oncall_game_day_pr32.md"
SCRIPT = ROOT / "scripts" / "pr32_game_day.ps1"
SPEC = (
    ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-3"
    / "PR3.2-incident-oncall-drills.md"
)
BOARD = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "BOARD.md"
EVIDENCE = (
    ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-3"
    / "evidence"
    / "PR3.2-game-day-local-2026-11-23.json"
)


def test_runbook_covers_incident_classes_roles_and_communications() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for expected in (
        "API outage",
        "Worker stuck",
        "OPA unavailable",
        "Postgres degraded",
        "Queue/DLQ growth",
        "LLM backend outage",
        "Budget cap hit",
        "Unsafe-action regression",
        "Primary on-call",
        "Incident commander",
        "Communications lead",
        "Initial:",
        "Resolved:",
    ):
        assert expected in text


def test_game_day_script_has_safety_and_rollback_controls() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for expected in (
        'if ($context -notlike "kind-*")',
        "available replicas = 0",
        '"rollback", $Release',
        "Test-ApiHealth",
        "action_items",
        "production_traffic = $false",
        "secrets_in_evidence = $false",
    ):
        assert expected in text


def test_pr32_status_and_evidence() -> None:
    assert EVIDENCE.exists()
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8-sig"))
    assert evidence["schema_version"] == "pr32.game-day.v1"
    assert evidence["result"] == "pass"
    assert evidence["detection"]["fired"] is True
    assert evidence["rollback"]["api_health_after"] == "ok"
    assert evidence["rollback"]["marker_removed"] is True
    assert (
        evidence["rollback"]["incident_revision"]
        > evidence["rollback"]["baseline_revision"]
    )
    assert {item["status"] for item in evidence["action_items"]} == {
        "done",
        "backlog",
    }
    assert all(item["owner"] for item in evidence["action_items"])
    backlog_item = next(
        item for item in evidence["action_items"] if item["status"] == "backlog"
    )
    assert (ROOT / backlog_item["tracking"]).exists()
    assert (
        "| PR3.2 | Incident, on-call, and rollback drills | Done |"
        in BOARD.read_text(encoding="utf-8")
    )
    assert "## Status\n\nDone" in SPEC.read_text(encoding="utf-8")
