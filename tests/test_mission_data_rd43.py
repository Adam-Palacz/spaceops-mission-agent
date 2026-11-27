"""RD4.3 hidden references stay off the agent-visible path."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.mcp.kb_server.index_kb import load_cited_source_docs, load_docs
from apps.mission_data.failure_modes import search_failure_modes
from apps.mission_data.historical_cases import (
    HIDDEN_DIR,
    HiddenReference,
    diagnosis_retrieval_rows,
    diagnosis_score_case_ids,
    load_cohorts,
    read_hidden_after_prediction,
    require_diagnosis_score_case,
    search_visible,
)
from apps.mission_data.historical_cases import HistoricalCaseError
from apps.mission_data.isolation import PredictionRecord

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"
HIDDEN_CAUSE = "synthetic contactor weld"


def test_agent_visible_search_misses_the_hidden_cause() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    assert search_visible(HIDDEN_CAUSE) == []
    assert search_failure_modes(HIDDEN_CAUSE) == []
    visible = search_visible("pack current")
    assert visible[0]["case_id"] == "rd43-synthetic-known"
    assert "cause" not in visible[0]
    indexed = "\n".join(
        text for _doc_id, _doc_type, text in [*load_docs(), *load_cited_source_docs()]
    )
    assert HIDDEN_CAUSE not in indexed
    telemetry_source = (
        ROOT / "apps" / "mcp" / "telemetry_server" / "main.py"
    ).read_text(encoding="utf-8")
    kb_source = (ROOT / "apps" / "mcp" / "kb_server" / "index_kb.py").read_text(
        encoding="utf-8"
    )
    assert "scoring/historical_cases" not in telemetry_source
    assert "scoring/historical_cases" not in kb_source
    assert not HIDDEN_DIR.resolve().is_relative_to(ROOT / "data" / "telemetry")
    assert not HIDDEN_DIR.resolve().is_relative_to(ROOT / "kb")
    assert not HIDDEN_DIR.resolve().is_relative_to(ROOT / "evals")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "scoring/historical_cases/hidden/" in dockerignore
    assert "scoring/historical_cases" not in compose
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_scorer_reads_the_hidden_reference_only_after_the_prediction_is_stored() -> (
    None
):
    with pytest.raises(HistoricalCaseError, match="prediction is stored"):
        read_hidden_after_prediction("rd43-synthetic-known", _prediction(status="open"))
    opened = read_hidden_after_prediction(
        "rd43-synthetic-known", _prediction(status="closed")
    )
    assert opened["cause"] == HIDDEN_CAUSE
    assert opened["cause_known"] is True
    assert diagnosis_score_case_ids() == ["rd43-synthetic-known"]
    require_diagnosis_score_case("rd43-synthetic-known")
    with pytest.raises(ValidationError, match="OPSSAT-AD"):
        HiddenReference.model_validate(
            {
                "schema_version": "rd4.case-hidden.v1",
                "case_id": "bad-label",
                "dataset_id": "opssat-ad",
                "cause_known": True,
                "cause": "anomaly",
                "appropriate_action": "Record the observation.",
                "unacceptable_action": "Do not use a segment label as the cause.",
                "exposure_risk": "not_a_cause",
                "evidence_at_cutoff": ["symptoms"],
            }
        )


def test_unknown_cause_does_not_require_a_subsystem() -> None:
    opened = read_hidden_after_prediction(
        "rd43-synthetic-unknown", _prediction(status="closed")
    )
    assert opened["cause_known"] is False
    assert opened["cause"] is None
    assert opened["subsystem"] is None
    assert "rd43-synthetic-unknown" not in diagnosis_score_case_ids()
    with pytest.raises(HistoricalCaseError, match="unknown cause"):
        require_diagnosis_score_case("rd43-synthetic-unknown")
    guessed = json.loads(
        (HIDDEN_DIR / "rd43-synthetic-unknown.json").read_text(encoding="utf-8")
    )
    guessed["subsystem"] = "battery"
    with pytest.raises(ValidationError, match="guessed subsystem"):
        HiddenReference.model_validate(guessed)


def test_blinded_packets_drop_identifiers_and_stay_marked_as_transformed() -> None:
    freeze = load_cohorts()
    assert freeze.named_public == []
    assert freeze.real_cases_in_git is False
    assert freeze.guaranteed_unseen is False
    rows = diagnosis_retrieval_rows()
    blob = json.dumps(rows)
    assert HIDDEN_CAUSE not in blob
    assert "After-cutoff" not in blob
    blinded = [row for row in rows if row["cohort"] == "blinded"]
    blinded_blob = json.dumps(blinded)
    assert "LabSat-Alpha" not in blinded_blob
    assert "2020" not in blinded_blob
    assert "http" not in blinded_blob
    assert blinded[0]["symptoms"]
    assert blinded[0]["transformed"] is True
    assert blinded[0]["counts_as_real_historical"] is False
    assert blinded[0]["guaranteed_unseen"] is False
    with pytest.raises(HistoricalCaseError, match="not a real historical case"):
        require_diagnosis_score_case("rd43-synthetic-known-blinded")


def _prediction(*, status: str) -> PredictionRecord:
    closed_at = "2020-01-01T03:00:00Z" if status == "closed" else None
    return PredictionRecord(
        run_id="rd43-run",
        mission_id="lab-synthetic",
        dataset_id="historical-cases-synthetic",
        time_range_start="2020-01-01T00:00:00Z",
        time_range_end="2020-01-01T02:00:00Z",
        status=status,  # type: ignore[arg-type]
        closed_at=closed_at,
        prediction={"summary": "observed high current"},
    )
