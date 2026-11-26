"""RD2.3 read-only profile and OPSSAT-AD lookalike plumbing pass."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from apps.agent.nodes import act
from apps.mission_data.isolation import READONLY_TOOL_PROFILE
from apps.mission_data.opssat_ad import OPSSAT_AD_LOOKALIKE_DATASET_ID
from apps.mission_data.readonly_pass import (
    REENTRY_EXCLUSION,
    CitationError,
    require_report_channels,
    run_opssat_ad_lookalike_pass,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"


def _state(plan: list[dict]) -> dict:
    return {
        "incident_id": "inc-rd23",
        "trace_id": "trace-rd23",
        "tool_profile": READONLY_TOOL_PROFILE,
        "plan": plan,
        "citations": [
            {"doc_id": "rb-1", "snippet_id": "s1"},
            {"doc_id": "rb-2", "snippet_id": "s2"},
        ],
        "escalated": False,
    }


def test_readonly_profile_blocks_pr_ticket_and_approval(monkeypatch) -> None:
    def _forbidden(*_args, **_kwargs):
        raise AssertionError("write tool was called")

    monkeypatch.setattr("apps.agent.nodes.call_create_ticket", _forbidden)
    monkeypatch.setattr("apps.agent.nodes.call_create_pr", _forbidden)
    monkeypatch.setattr("apps.agent.nodes.approval_store_create", _forbidden)
    monkeypatch.setattr("apps.agent.nodes.opa_allow", _forbidden)

    result = act(
        _state(
            [
                {
                    "safe": True,
                    "action_type": "create_ticket",
                    "action": "Open a ticket",
                    "doc_ids": ["rb-1"],
                    "snippet_ids": ["s1"],
                },
                {
                    "safe": True,
                    "action_type": "create_pr",
                    "action": "Open a pull request",
                    "doc_ids": ["rb-1"],
                    "snippet_ids": ["s1"],
                },
                {
                    "safe": False,
                    "action_type": "change_config",
                    "action": "Change a limit",
                    "doc_ids": ["rb-2"],
                    "snippet_ids": ["s2"],
                },
            ]
        )
    )
    assert result.get("approval_requests") == []
    assert result.get("escalated") is not True
    tools = [row["tool"] for row in result["act_results"]]
    assert tools == ["create_ticket", "create_pr", "approval_request"]
    assert all(row["outcome"] == "failure" for row in result["act_results"])
    assert all(
        row["result"] == {"blocked": READONLY_TOOL_PROFILE}
        for row in result["act_results"]
    )


def test_report_cannot_cite_a_channel_the_tool_did_not_return() -> None:
    queried = {"CADC0872", "CADC0873"}
    known = queried | {"CADC0894", "Battery_Voltage"}
    require_report_channels(
        "Queried channels: CADC0872, CADC0873.",
        queried_channels=queried,
        known_channels=known,
    )
    with pytest.raises(CitationError, match="CADC0894"):
        require_report_channels(
            "Also see CADC0894.",
            queried_channels=queried,
            known_channels=known,
        )


def test_lookalike_pass_is_plumbing_and_leaves_synthetic_evals_alone() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    report = run_opssat_ad_lookalike_pass()
    assert report.status == "plumbing_only"
    assert report.model_backed is False
    assert report.model is None
    assert report.dataset_id == OPSSAT_AD_LOOKALIKE_DATASET_ID
    assert report.write_tool_calls == 0
    assert report.policy_revision == "2026-11-26.v1"
    assert report.channels_queried == ["CADC0872", "CADC0873", "CADC0884"]
    assert "CADC0872" in report.table_markdown
    assert "Battery_Voltage" not in report.report_text
    assert REENTRY_EXCLUSION in report.report_text
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before
    eval_hits = [
        path
        for path in (ROOT / "evals").rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".json", ".yml", ".yaml", ".md"}
        and "opssat-ad" in path.read_text(encoding="utf-8")
    ]
    assert eval_hits == []
