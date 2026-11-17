"""PR2.3 focused security-boundary regression tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.mcp.gitops_server.main import (
    MAX_FILE_CONTENT_BYTES,
    MAX_FILES_PER_REQUEST,
    _resolve_ops_config_dir,
    _validate_create_pr_arguments,
    create_pr,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW = REPO_ROOT / "docs" / "security_control_review_pr23.md"
SPEC = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "PR2.3-security-review.md"
)
EVIDENCE = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "evidence"
    / "PR2.3-security-review-2026-09-26.json"
)


def test_pr23_review_records_all_boundaries_findings_and_phase_blockers() -> None:
    text = REVIEW.read_text(encoding="utf-8")
    for boundary in (
        "OPA fail-closed",
        "Approval authentication",
        "MCP tool and argument boundary",
        "Append-only audit",
        "Platform operations gating",
        "LLM budget, circuit breaker, and fallback",
    ):
        assert boundary in text
    for finding in range(1, 7):
        assert f"PR23-00{finding}" in text
    assert "A production-pilot decision is `No-go`" in text
    assert "PR23-002" in text and "PR23-003" in text
    assert "blocks production-pilot phase closure" in text
    assert EVIDENCE.is_file()


def test_pr23_agent_has_no_arbitrary_shell_execution_helper() -> None:
    agent_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / "apps" / "agent").glob("*.py")
    )
    assert "subprocess." not in agent_sources
    assert "os.system(" not in agent_sources
    assert "shell=True" not in agent_sources


def test_pr23_mcp_client_dispatches_only_fixed_tool_names() -> None:
    source = (REPO_ROOT / "apps" / "agent" / "mcp_client.py").read_text(
        encoding="utf-8"
    )
    assert 'session.call_tool(\n                            "query_telemetry"' in source
    assert 'session.call_tool(\n                        "search_runbooks"' in source
    assert 'session.call_tool(\n                        "search_postmortems"' in source
    assert 'session.call_tool(\n                        "create_ticket"' in source
    assert 'session.call_tool(\n                        "create_pr"' in source
    assert "session.call_tool(tool" not in source


def test_pr23_gitops_rejects_arbitrary_repository_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="SpaceOps repository or ops-config"):
        _resolve_ops_config_dir(str(tmp_path))


@pytest.mark.parametrize(
    "branch",
    [
        "",
        "main",
        "--upload-pack=bad",
        "agent/../bad",
        "agent/bad branch",
    ],
)
def test_pr23_gitops_rejects_unsafe_branch_names(branch: str) -> None:
    with pytest.raises(ValueError, match="branch must start"):
        _validate_create_pr_arguments(
            branch, [{"path": "alerts/test.yaml", "content": "ok"}]
        )


def test_pr23_gitops_rejects_empty_or_excessive_file_sets() -> None:
    with pytest.raises(ValueError, match="files must contain"):
        _validate_create_pr_arguments("agent/test", [])
    with pytest.raises(ValueError, match="files must contain"):
        _validate_create_pr_arguments(
            "agent/test",
            [
                {"path": f"alerts/{index}.yaml", "content": "ok"}
                for index in range(MAX_FILES_PER_REQUEST + 1)
            ],
        )


@pytest.mark.parametrize("path", ["", "../escape.yaml", "alerts/../../escape.yaml"])
def test_pr23_gitops_rejects_empty_or_traversing_paths(path: str) -> None:
    with pytest.raises(ValueError, match="path|Invalid"):
        create_pr(
            repo_path=None,
            branch="agent/security-test",
            files=[{"path": path, "content": "ok"}],
        )


def test_pr23_gitops_rejects_oversized_content() -> None:
    with pytest.raises(ValueError, match="exceeds"):
        create_pr(
            repo_path=None,
            branch="agent/security-test",
            files=[
                {
                    "path": "alerts/large.yaml",
                    "content": "x" * (MAX_FILE_CONTENT_BYTES + 1),
                }
            ],
        )


def test_pr23_spec_is_closed_as_review_but_preserves_no_go_boundary() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "| **Status** | Done |" in text
    assert "PR23-002" in text and "PR23-003" in text
    assert "does not mean production-pilot approval" in text
