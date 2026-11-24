"""Master roadmap structure, deferred next-gen, and link integrity."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "roadmap"
REQUIRED = (
    "## Objective and rationale",
    "## Existing implementation and gaps",
    "## Functional and non-functional requirements",
    "## Architecture and affected components",
    "## Dependencies",
    "## Implementation checklist",
    "## Testing requirements",
    "## Security and safety requirements",
    "## Acceptance criteria",
    "## Required execution evidence",
    "## Definition of Done",
)
PHASE_DIRS = (
    "03-real-world-mission-data",
    "04-anomaly-detection-validation",
    "05-mission-control-integration",
    "06-edge-ai-hardware",
    "07-external-validation",
    "08-next-gen-autonomy",
)


def _local_links(path: Path) -> list[str]:
    links = re.findall(r"\[[^\]]+\]\(([^)#][^)]+)\)", path.read_text(encoding="utf-8"))
    cleaned = []
    for href in links:
        target = href.split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        cleaned.append(target)
    return cleaned


def test_master_roadmap_keeps_admission_and_corrections() -> None:
    text = (ROADMAP / "MASTER.md").read_text(encoding="utf-8")
    assert "No-go - remain reference/stage only" in text
    assert "1594 train" in text
    assert "529 test" in text
    assert "CC BY 4.0" in text
    assert "CC BY 3.0 IGO" in text
    assert "not flight readiness" in text.lower() or "Not flight readiness" in text
    assert "stratified random" in text


def test_new_phases_have_boards_and_no_done_tasks() -> None:
    for name in PHASE_DIRS:
        phase = ROADMAP / name
        assert (phase / "README.md").is_file()
        for board in phase.glob("sprint-*/BOARD.md"):
            body = board.read_text(encoding="utf-8")
            assert "| Todo |" in body
            for line in body.splitlines():
                if (
                    not line.startswith("| ")
                    or line.startswith("| Task ")
                    or line.startswith("|---")
                ):
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) >= 3:
                    assert cells[2] != "Done", line
        for spec in phase.glob("sprint-*/*-*.md"):
            if spec.name in {"README.md", "BOARD.md"}:
                continue
            body = spec.read_text(encoding="utf-8")
            assert "| **Status** | Todo |" in body
            for heading in REQUIRED:
                assert heading in body, f"{spec}: missing {heading}"


def test_historical_next_gen_specs_remain() -> None:
    historical = ROADMAP / "deprecated-03-next-gen-autonomy"
    for name in (
        "sprint-1/NG1.1-supervisor-graph-adr.md",
        "sprint-2/NG2.1-plan-edit-api.md",
        "sprint-3/NG3.1-redaction-policy-adr.md",
        "sprint-4/NG4.1-dual-mode-gateway.md",
        "sprint-5/NG5.1-dependency-graph-model.md",
    ):
        assert (historical / name).is_file()
    ng_readme = (historical / "README.md").read_text(encoding="utf-8")
    assert "NG1-NG2 may continue" in ng_readme
    assert "Execution priority (2026-11-24):** deferred" in ng_readme


def test_new_roadmap_links_resolve() -> None:
    documents = [ROADMAP / "MASTER.md", ROADMAP / "README.md"]
    documents.extend((ROADMAP / name).rglob("*.md") for name in PHASE_DIRS)
    flat: list[Path] = []
    for item in documents:
        if isinstance(item, Path):
            flat.append(item)
        else:
            flat.extend(item)
    missing: list[str] = []
    for doc in flat:
        for target in _local_links(doc):
            if not (doc.parent / target).resolve().exists():
                missing.append(f"{doc}: {target}")
    assert not missing, missing
