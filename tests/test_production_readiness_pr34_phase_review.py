"""PR3.4 production-readiness review tests."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE_REVIEW = ROOT / "roadmap" / "02.5-production-readiness" / "PHASE_REVIEW.md"
SPRINT_REVIEW = (
    ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "SPRINT_REVIEW.md"
)
SPEC = (
    ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-3"
    / "PR3.4-production-readiness-review.md"
)
BOARD = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "BOARD.md"
NG_README = ROOT / "roadmap" / "deprecated-03-next-gen-autonomy" / "README.md"


def test_review_records_explicit_no_go_and_phase_status() -> None:
    text = PHASE_REVIEW.read_text(encoding="utf-8")
    assert "**Decision:** **No-go - remain reference/stage only**" in text
    assert "No waiver is approved" in text
    assert "planned pr1-pr3 delivery is complete" in text.lower()
    assert "phase outcome remains **No-go**" in " ".join(text.split())


def test_review_imports_security_and_managed_observability_gates() -> None:
    text = PHASE_REVIEW.read_text(encoding="utf-8")
    for finding in (
        "PR23-001",
        "PR23-002",
        "PR23-003",
        "PR23-004",
        "PR23-005",
        "PR23-006",
    ):
        assert finding in text
    for gate in (
        "Cloud Logging retention",
        "Cloud Trace/OTel exporter",
        "Authorized operator",
        "Unauthorized principal",
        "Deletion/expiry drill",
        "NG3 masking disposition",
    ):
        assert gate in text


def test_review_has_exit_assessment_risk_owners_and_deadlines() -> None:
    text = PHASE_REVIEW.read_text(encoding="utf-8")
    assert "Hard exit criteria assessment" in text
    assert "Additional residual risks" in text
    assert "Re-review entry criteria" in text
    assert text.count("**Owner:**") >= 4
    assert text.count("**Deadline:**") >= 4
    for risk in (
        "Managed Postgres HA/PITR",
        "Real paging delivery",
        "Worker has no standalone metrics endpoint",
        "No named pilot roster",
    ):
        assert risk in text


def test_review_references_all_sprint_reviews_or_closure_notes() -> None:
    text = PHASE_REVIEW.read_text(encoding="utf-8")
    for review in (
        "sprint-1/SPRINT_REVIEW.md",
        "sprint-2/SPRINT_REVIEW.md",
        "sprint-3/SPRINT_REVIEW.md",
    ):
        assert review in text


def test_ng_dependency_and_pr34_status_are_updated() -> None:
    ng = NG_README.read_text(encoding="utf-8")
    assert "No-go - reference/stage only" in ng
    assert "NG1-NG2 may continue" in ng
    assert "NG3+" in ng
    assert "| PR3.4 | Production readiness review | Done |" in BOARD.read_text(
        encoding="utf-8"
    )
    spec = SPEC.read_text(encoding="utf-8")
    assert "## Status\n\nDone - decision: No-go" in spec
    assert "PHASE_REVIEW.md" in spec


def test_new_review_links_resolve() -> None:
    for doc in (PHASE_REVIEW, SPRINT_REVIEW, SPEC):
        text = doc.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)#][^)]+)\)", text)
        for href in links:
            target = href.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert (doc.parent / target).resolve().exists(), f"{doc}: {href}"
