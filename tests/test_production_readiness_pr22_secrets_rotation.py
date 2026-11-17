"""PR2.2 - secrets rotation and external-secret proof."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CHART = REPO_ROOT / "deploy" / "helm" / "spaceops"
RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "secrets_rotation_pr22.md"
DOCS_INDEX = REPO_ROOT / "docs" / "README.md"
PORTFOLIO = REPO_ROOT / "docs" / "portfolio" / "README.md"
BOARD = REPO_ROOT / "roadmap" / "02.5-production-readiness" / "sprint-2" / "BOARD.md"
PR22 = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "PR2.2-secrets-rotation.md"
)
EVIDENCE = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "evidence"
    / "PR2.2-local-eso-rotation-2026-09-26.json"
)


def _helm_available() -> bool:
    return shutil.which("helm") is not None


def _render(environment: str) -> list[dict]:
    result = subprocess.run(
        [
            "helm",
            "template",
            "spaceops",
            str(CHART),
            "-f",
            str(CHART / "values.yaml"),
            "-f",
            str(CHART / f"values-{environment}.yaml"),
            "--set",
            "externalSecrets.enabled=true",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc]


@pytest.mark.skipif(not _helm_available(), reason="helm CLI not installed")
@pytest.mark.parametrize("environment", ("stage", "prod"))
def test_stage_prod_render_external_secret_without_plaintext_secret(
    environment: str,
) -> None:
    docs = _render(environment)
    assert not [doc for doc in docs if doc.get("kind") == "Secret"]
    external = [doc for doc in docs if doc.get("kind") == "ExternalSecret"]
    assert len(external) == 1
    assert external[0]["apiVersion"] == "external-secrets.io/v1"
    assert "stringData" not in external[0]

    secret_keys = {item["secretKey"] for item in external[0]["spec"]["data"]}
    assert {
        "postgres-password",
        "OPENAI_API_KEY",
        "APPROVAL_API_KEY",
        "GITHUB_TOKEN",
        "NGC_API_KEY",
        "CURSOR_SH_API_KEY",
        "GPU_LLM_API_KEY",
    } == secret_keys


def test_pr22_local_evidence_records_rotation_without_raw_values() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["schema_version"] == "pr22.secret_rotation.v1"
    assert evidence["status"] == "local_pass_live_pending"
    assert evidence["sync"]["external_secret_reason"] == "SecretSynced"
    assert evidence["sync"]["resource_version_changed"] is True
    assert evidence["rollout"]["pod_uid_changed"] is True
    assert all(item["changed"] for item in evidence["hashes"].values())
    assert evidence["leak_scan"]["raw_synthetic_value_matches"] == 0
    assert evidence["helm"]["stage_plain_secret_kinds"] == 0
    assert evidence["helm"]["prod_plain_secret_kinds"] == 0

    text = EVIDENCE.read_text(encoding="utf-8")
    assert not re.search(
        r"pr22-v[12]-(postgres|llm|approval|gitops|mcp)-synthetic", text
    )


def test_pr22_docs_board_and_boundaries_are_explicit() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = PR22.read_text(encoding="utf-8")
    board = BOARD.read_text(encoding="utf-8")

    assert (
        "| PR2.2 | Secrets rotation and external secret proof | In progress |" in board
    )
    assert "## Status\n\nIn progress" in spec
    assert "Live ESO/GSM workload rotation" in spec
    assert "MCP authentication is not implemented" in spec
    for required in (
        "Secret inventory",
        "Controlled live stage procedure",
        "Database password rotation",
        "Leak check",
        "Rollback",
        "explicit confirmation",
    ):
        assert required in runbook
    assert "secrets_rotation_pr22.md" in DOCS_INDEX.read_text(encoding="utf-8")
    assert "secrets_rotation_pr22.md" in PORTFOLIO.read_text(encoding="utf-8")


def test_pr22_local_markdown_links_resolve() -> None:
    for doc in (RUNBOOK, PR22):
        text = doc.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)#][^)]+)\)", text)
        for href in links:
            target = href.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert (doc.parent / target).resolve().exists(), f"{doc}: {href}"
