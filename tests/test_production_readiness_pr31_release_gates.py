"""PR3.1 release promotion gate tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import release_gate_pr31

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_gate_pr31.py"
RUNBOOK = ROOT / "docs" / "runbooks" / "release_promotion_gate_pr31.md"
SPEC = (
    ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-3"
    / "PR3.1-release-gates.md"
)
BOARD = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "BOARD.md"
WORKFLOW = ROOT / ".github" / "workflows" / "release-gate.yml"
MAKEFILE = ROOT / "Makefile"
LIVE_RUNNER = ROOT / "scripts" / "pr31_live_release_gate.ps1"
EVIDENCE_DIR = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "evidence"


def test_dry_run_contains_every_required_gate(tmp_path: Path) -> None:
    evidence = tmp_path / "gate.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mode",
            "dry-run",
            "--evidence",
            str(evidence),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["result"] == "planned"
    assert report["blocking"] is True
    ids = {step["id"] for step in report["steps"]}
    assert {
        "lint",
        "typecheck",
        "tests",
        "approval_opa_fail_closed",
        "helm_lint_stage",
        "helm_lint_prod",
        "helm_template_stage",
        "migration_offline_sql",
    } <= ids
    assert json.loads(evidence.read_text(encoding="utf-8")) == report


def test_stage_plan_covers_live_and_rollback_checks() -> None:
    ids = {
        step["id"]
        for step in release_gate_pr31.stage_steps(
            "https://stage.example.test", "spaceops-stage"
        )
    }
    assert {
        "stage_health",
        "stage_scenarios_a_b",
        "queue_stream_status",
        "rollback_helm_snapshot",
        "rollback_image_snapshot",
    } <= ids


def test_dlq_gate_uses_api_count(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return b'{"dlq_events": [{"event_id": "one"}], "count": 1}'

    monkeypatch.setattr(
        release_gate_pr31.request, "urlopen", lambda *_a, **_k: Response()
    )
    result = release_gate_pr31.check_dlq("https://stage.example.test", max_rows=0)
    assert result["status"] == "fail"
    assert result["observed_rows"] == 1


def test_failed_step_is_blocking(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        release_gate_pr31,
        "static_steps",
        lambda: [
            {
                "id": "forced_failure",
                "command": [sys.executable, "-c", "raise SystemExit(7)"],
            }
        ],
    )
    rc = release_gate_pr31.main(
        ["--mode", "ci", "--evidence", str(tmp_path / "failed.json")]
    )
    report = json.loads((tmp_path / "failed.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert report["result"] == "fail"
    assert report["steps"][0]["returncode"] == 7


def test_docs_workflow_makefile_and_status_are_wired() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    for text in (
        "Blocking behavior",
        "Scenario A/B",
        "DLQ",
        "rollback",
        "artifacts/release-gates/",
    ):
        assert text in runbook
    assert "release-gate-pr31" in MAKEFILE.read_text(encoding="utf-8")
    assert "release_gate_pr31.py" in WORKFLOW.read_text(encoding="utf-8")
    assert "upload-artifact@v4" in WORKFLOW.read_text(encoding="utf-8")
    assert "StaticEvidencePath" in LIVE_RUNNER.read_text(encoding="utf-8")
    assert "| PR3.1 | Release smoke/e2e promotion gates | Done |" in BOARD.read_text(
        encoding="utf-8"
    )
    spec = SPEC.read_text(encoding="utf-8")
    assert "## Status\n\nDone" in spec
    assert "PR3.1-live-stage-2026-11-22.json" in spec


def test_live_and_static_release_evidence_pass_for_same_candidate() -> None:
    static = json.loads(
        (EVIDENCE_DIR / "PR3.1-static-ci-2026-11-22.json").read_text(
            encoding="utf-8-sig"
        )
    )
    live = json.loads(
        (EVIDENCE_DIR / "PR3.1-live-stage-2026-11-22.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert static["result"] == "pass"
    assert live["result"] == "pass"
    assert static["release_id"] == live["release_id"]
    assert all(step["status"] == "pass" for step in static["steps"])
    assert all(step["status"] == "pass" for step in live["steps"])
    assert (
        next(step for step in live["steps"] if step["id"] == "dlq_threshold")[
            "observed_rows"
        ]
        == 0
    )
