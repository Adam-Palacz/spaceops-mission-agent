"""PR4 production-admission remediation roadmap tests."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "roadmap" / "02.5-production-readiness"
SPRINT = PHASE / "sprint-4"
BOARD = SPRINT / "BOARD.md"
REVIEW = PHASE / "PHASE_REVIEW.md"


def test_pr4_board_has_ordered_todo_tasks() -> None:
    board = BOARD.read_text(encoding="utf-8")
    for number in range(1, 8):
        assert f"| PR4.{number} |" in board
    assert board.count("| Todo |") == 7


def test_pr4_specs_exist_and_start_todo() -> None:
    specs = sorted(SPRINT.glob("PR4.*.md"))
    assert len(specs) == 7
    for spec in specs:
        text = spec.read_text(encoding="utf-8")
        assert "| **Status** | Todo |" in text
        assert "## Requirements" in text
        assert "## Test requirements" in text


def test_pr4_covers_every_no_go_gate() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in SPRINT.glob("*.md")
    )
    for gate in (
        "PR23-002",
        "PR23-003",
        "PR23-004",
        "PR23-005",
        "PR23-006",
        "BL-006",
        "Managed Postgres",
        "Managed logging and tracing",
    ):
        assert gate in combined


def test_phase_review_schedules_pr4_without_changing_no_go() -> None:
    review = REVIEW.read_text(encoding="utf-8")
    assert "**Decision:** **No-go - remain reference/stage only**" in review
    assert "PR4 remediation is scheduled but not started" in review
    for number in range(1, 8):
        assert f"[PR4.{number}]" in review


def test_pr4_requires_real_drills_and_new_decision() -> None:
    postgres = (SPRINT / "PR4.5-managed-postgres-ha-pitr.md").read_text(
        encoding="utf-8"
    )
    paging = (SPRINT / "PR4.6-live-paging-drill.md").read_text(encoding="utf-8")
    decision = (SPRINT / "PR4.7-production-admission-review.md").read_text(
        encoding="utf-8"
    )
    assert "actual managed HA/PITR drill" in postgres.replace("\n", " ")
    assert "real paging destination" in paging
    assert "does not require or imply a Go outcome" in decision
