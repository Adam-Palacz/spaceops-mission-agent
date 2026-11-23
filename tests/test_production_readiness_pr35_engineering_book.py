"""PR3.5 engineering-book source, redaction, manifest, and pipeline tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import book_build, book_screenshots


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "docs" / "book" / "book.yml"
README = ROOT / "docs" / "book" / "README.md"
SPEC = (
    ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-3"
    / "PR3.5-engineering-book-publication-pipeline.md"
)
BOARD = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-3" / "BOARD.md"
WORKFLOW = ROOT / ".github" / "workflows" / "engineering-book.yml"
MAKEFILE = ROOT / "Makefile"


def run_verify(tmp_path: Path, edition: str) -> tuple[dict, str]:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "1795392000"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "book_build.py"),
            "--edition",
            edition,
            "--output-root",
            str(tmp_path),
            "--verify-only",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    manifest = json.loads(
        (tmp_path / edition / "manifest.json").read_text(encoding="utf-8")
    )
    book = (tmp_path / edition / "book.md").read_text(encoding="utf-8")
    assert json.loads(proc.stdout)["result"] == "pass"
    return manifest, book


def test_private_and_public_verify_builds_are_deterministic(tmp_path: Path) -> None:
    private, private_book = run_verify(tmp_path / "one", "private")
    public, public_book = run_verify(tmp_path / "one", "public")
    public_again, _ = run_verify(tmp_path / "two", "public")

    assert private["schema_version"] == "spaceops.engineering-book.v1"
    assert private["edition"] == "private"
    assert public["edition"] == "public"
    assert public == public_again
    assert private["git_commit"] == public["git_commit"]
    assert private["evidence"] == public["evidence"]
    assert len(public["chapters"]) == 8
    assert len(public["evidence"]) >= 6
    assert "Private engineering evidence" in private_book
    assert "Private engineering evidence" not in public_book
    assert "<!-- private:" not in public_book


def test_public_redaction_and_secret_scan_with_synthetic_fixture() -> None:
    redactions = [
        {
            "name": "project",
            "pattern": r"demo-project-[0-9]+",
            "replacement": "[redacted-project]",
        }
    ]
    source = (
        "before\n<!-- private:start -->internal<!-- private:end -->\n"
        "project=demo-project-123"
    )
    public, counts = book_build.process_public(source, redactions)
    assert "internal" not in public
    assert "demo-project-123" not in public
    assert "[redacted-project]" in public
    assert counts == {"private_blocks": 1, "project": 1}

    with pytest.raises(ValueError, match="public secret scan failed"):
        book_build.process_public("token sk-" + "a" * 32, [])
    with pytest.raises(ValueError, match="unmatched private"):
        book_build.process_public("<!-- private:start -->", [])


def test_book_config_sources_and_chapter_pattern() -> None:
    config = book_build.load_config(CONFIG)
    for chapter_name in config["chapters"]:
        chapter = CONFIG.parent / chapter_name
        text = chapter.read_text(encoding="utf-8")
        if not chapter.name.startswith("90-"):
            for heading in (
                "## Why",
                "## Decision",
                "## Implementation",
                "## Verification",
                "## Evidence",
                "## Limitations",
                "## Lessons learned",
            ):
                assert heading in text, f"{chapter}: {heading}"
        else:
            assert "## Canonical sources" in text
        book_build.validate_local_links(chapter, text)
    for evidence in config["evidence"]:
        assert (CONFIG.parent / evidence).resolve().is_file()


def test_screenshot_collector_dry_run_is_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1795392000")
    output_one = tmp_path / "one"
    output_two = tmp_path / "two"
    assert (
        book_screenshots.main(["--mode", "dry-run", "--output", str(output_one)]) == 0
    )
    assert (
        book_screenshots.main(["--mode", "dry-run", "--output", str(output_two)]) == 0
    )
    first = json.loads((output_one / "screenshots.json").read_text(encoding="utf-8"))
    second = json.loads((output_two / "screenshots.json").read_text(encoding="utf-8"))
    assert first == second
    assert len(first["items"]) == 4
    assert all(item["status"] == "dry-run" for item in first["items"])
    assert all(item["caption"] for item in first["items"])
    assert first["cloud_console_automation"] is False


def test_pipeline_commands_workflow_and_status_are_wired() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    for target in ("book:", "book-private:", "book-public:", "book-verify:"):
        assert target in makefile
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for expected in (
        "pandoc",
        "weasyprint",
        "make book-verify",
        "make book",
        "upload-artifact@v4",
    ):
        assert expected in workflow
    readme = README.read_text(encoding="utf-8")
    assert "Maintenance policy" in readme
    assert "human editorial/security review" in readme
    assert (
        "| PR3.5 | Engineering book and publication pipeline | Done |"
        in BOARD.read_text(encoding="utf-8")
    )
    assert "## Status\n\nDone" in SPEC.read_text(encoding="utf-8")


def test_built_artifacts_when_toolchain_has_run() -> None:
    build = ROOT / "build" / "book"
    for edition in ("private", "public"):
        directory = build / edition
        if not directory.exists():
            pytest.skip("book artifact build is exercised by engineering-book workflow")
        for extension in ("html", "pdf", "epub"):
            artifact = directory / f"spaceops-engineering-book-{edition}.{extension}"
            assert artifact.is_file()
            assert artifact.stat().st_size > 500
