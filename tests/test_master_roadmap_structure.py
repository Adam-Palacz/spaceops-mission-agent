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


def test_new_phases_have_consistent_boards_and_evidenced_done_tasks() -> None:
    allowed_statuses = {"Todo", "In progress", "Done", "Blocked"}
    for name in PHASE_DIRS:
        phase = ROADMAP / name
        assert (phase / "README.md").is_file()
        for board in phase.glob("sprint-*/BOARD.md"):
            body = board.read_text(encoding="utf-8")
            board_statuses: dict[str, str] = {}
            for line in body.splitlines():
                if (
                    not line.startswith("| ")
                    or line.startswith("| Task ")
                    or line.startswith("|---")
                ):
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) < 4:
                    continue
                status = cells[2]
                assert status in allowed_statuses, f"{board}: {line}"
                spec_name = re.search(r"\(([^)]+\.md)\)", cells[3])
                assert spec_name, f"{board}: {line}"
                board_statuses[spec_name.group(1)] = status
                spec_body = (board.parent / spec_name.group(1)).read_text(
                    encoding="utf-8"
                )
                if status == "Done":
                    assert "| **Status** | Done |" in spec_body, f"{board}: {line}"
                    evidence = re.search(r"\((evidence/[^)]+)\)", spec_body)
                    assert evidence, spec_body
                    assert (board.parent / evidence.group(1)).is_file()
            assert board_statuses, f"{board}: no task rows found"
            for spec in board.parent.glob("*-*.md"):
                if spec.name in {"README.md", "BOARD.md"}:
                    continue
                spec_body = spec.read_text(encoding="utf-8")
                if "| **Status** | Done |" in spec_body:
                    assert (
                        board_statuses.get(spec.name) == "Done"
                    ), f"{spec} is Done but not marked Done in {board}"
        for spec in phase.glob("sprint-*/*-*.md"):
            if spec.name in {"README.md", "BOARD.md"}:
                continue
            body = spec.read_text(encoding="utf-8")
            assert re.search(
                r"\| \*\*Status\*\* \| (Todo|In progress|Done|Blocked) \|", body
            )
            if "| **Status** | Done |" in body:
                evidence = re.search(r"\((evidence/[^)]+)\)", body)
                assert evidence and (spec.parent / evidence.group(1)).is_file(), spec
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


def test_historical_validation_tracks_and_egress_policy() -> None:
    master = (ROADMAP / "MASTER.md").read_text(encoding="utf-8")
    assert "RD4 --> AV5" in master
    assert "AV5 --> AV6" in master
    assert "before AV2-AV4 finish" in master
    phase = ROADMAP / "03-real-world-mission-data"
    policy = (phase / "LLM_DATA_POLICY.md").read_text(encoding="utf-8")
    assert "stage remains synthetic-only" in policy
    assert "External denied" in policy
    assert "No exception under this policy" in policy
    assert "Ground truth, hidden references" in policy
    assert "cloud fallback" in policy
    av5 = ROADMAP / "04-anomaly-detection-validation" / "sprint-5"
    scoring = (av5 / "AV5.2-historical-case-scoring.md").read_text(encoding="utf-8")
    assert "identity-only/no-telemetry baseline" in scoring
    assert "no-evidence control" in scoring
    assert "do not claim unseen-event generalization" in scoring
