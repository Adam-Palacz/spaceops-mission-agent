"""PR3.3 bounded production-pilot plan tests."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "production_pilot_plan_pr33.md"
SPEC = (
    ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-3"
    / "PR3.3-production-pilot-plan.md"
)
BOARD = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "BOARD.md"


def test_pilot_plan_has_scope_owners_support_cost_and_data_boundaries() -> None:
    text = PLAN.read_text(encoding="utf-8")
    for expected in (
        "ten staffed business days",
        "09:00-17:00",
        "no 24/7 support claim",
        "Production-pilot owner",
        "Primary on-call",
        "Terraform billing budget",
        "Postgres budget mode",
        "synthetic or explicitly approved",
        "Real spacecraft",
        "No-go",
    ):
        assert expected in text


def test_pilot_plan_has_actions_integrations_metrics_and_exit_criteria() -> None:
    text = PLAN.read_text(encoding="utf-8")
    for expected in (
        "Allowed actions and safety limits",
        "Direct cluster/config mutation by agent",
        "Spacecraft/ground-segment command",
        "External integration contracts",
        "Telemetry source",
        "Identity provider",
        "Approval store",
        "Immediate pilot stop criteria",
        "API availability at least 99%",
        "p95 run duration at most 60 seconds",
        "zero unsafe or unauthorized actions",
        "Pilot exit criteria",
        "Legal/compliance assumptions and non-goals",
    ):
        assert expected in text


def test_pilot_plan_preserves_security_and_privacy_blockers() -> None:
    text = PLAN.read_text(encoding="utf-8")
    for finding in ("PR23-002", "PR23-003", "PR23-004", "PR23-005"):
        assert finding in text
    for gate in (
        "managed trace/log",
        "authorized/denied query",
        "deletion/expiry",
        "time-boxed waivers",
        "compensating controls",
    ):
        assert gate in text


def test_pilot_plan_local_links_resolve() -> None:
    text = PLAN.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)#][^)]+)\)", text)
    for href in links:
        target = href.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        assert (PLAN.parent / target).resolve().exists(), href


def test_pr33_is_done_and_linked() -> None:
    assert "| PR3.3 | Production pilot deployment plan | Done |" in BOARD.read_text(
        encoding="utf-8"
    )
    spec = SPEC.read_text(encoding="utf-8")
    assert "## Status\n\nDone" in spec
    assert "production_pilot_plan_pr33.md" in spec
