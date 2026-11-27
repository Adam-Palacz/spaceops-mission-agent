"""Hidden-reference historical cases for the scorer (RD4.3).

Agent-visible search reads ``visible/`` only. Hidden references open after a
closed prediction. OPSSAT-AD segment labels are not root causes. Blinded
packets drop calendar dates, source URLs, and scorer-only text. A blinded
packet is not a claim that the case is unseen.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.mission_data.isolation import PredictionRecord
from apps.mission_data.provenance import require_non_blank
from apps.mission_data.registry import REPO_ROOT

CASES_ROOT = REPO_ROOT / "scoring" / "historical_cases"
VISIBLE_DIR = CASES_ROOT / "visible"
HIDDEN_DIR = CASES_ROOT / "hidden"
COHORTS_PATH = CASES_ROOT / "cohorts.json"

OPSSAT_AD_LABELS = frozenset({"anomaly", "a2", "a3", "a4"})
FORBIDDEN_ACTION_TOKENS = (
    "change_config",
    "restart_service",
    "proposed_actions",
)
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_URL = re.compile(r"https?://", re.IGNORECASE)

CohortName = Literal["named_public", "synthetic", "blinded", "perturbed"]


class HistoricalCaseError(ValueError):
    """A historical case breaks the hidden-reference rules."""


class VisiblePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd4.case-visible.v1"]
    case_id: str = Field(..., min_length=1)
    cohort: Literal["synthetic"]
    dataset_id: str = Field(..., min_length=1)
    time_range_start: str = Field(..., min_length=1)
    time_range_end: str = Field(..., min_length=1)
    symptoms: list[str] = Field(..., min_length=1)
    public_name: str = ""


class HiddenReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd4.case-hidden.v1"]
    case_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    cause_known: bool
    cause: str | None = None
    subsystem: str | None = None
    appropriate_action: str = Field(..., min_length=1)
    unacceptable_action: str = Field(..., min_length=1)
    mission_alias: str = ""
    post_incident_report: str = ""
    exposure_risk: str = Field(..., min_length=1)
    evidence_at_cutoff: list[str] = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_cause(self) -> HiddenReference:
        if self.dataset_id.startswith("opssat-ad"):
            raise ValueError("OPSSAT-AD labels are not a hidden root cause")
        if self.cause and self.cause.casefold() in OPSSAT_AD_LABELS:
            raise ValueError("OPSSAT-AD labels are not a hidden root cause")
        if self.cause_known:
            if not (self.cause or "").strip():
                raise ValueError("known cause requires a cause string")
        elif self.cause or self.subsystem:
            raise ValueError("unknown cause does not take a guessed subsystem")
        blob = " ".join(
            [
                self.appropriate_action,
                self.unacceptable_action,
                self.cause or "",
                self.post_incident_report,
            ]
        ).casefold()
        for token in FORBIDDEN_ACTION_TOKENS:
            if token in blob:
                raise ValueError("hidden reference names an executable action")
        return self


class CohortFreeze(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd4.case-cohorts.v1"]
    frozen_on: str = Field(..., min_length=1)
    guaranteed_unseen: Literal[False]
    real_cases_in_git: Literal[False]
    named_public: list[str]
    synthetic: list[str] = Field(..., min_length=1)
    blinded: list[str] = Field(..., min_length=1)
    perturbed: list[str] = Field(..., min_length=1)


def load_cohorts() -> CohortFreeze:
    freeze = CohortFreeze.model_validate(
        json.loads(COHORTS_PATH.read_text(encoding="utf-8"))
    )
    synthetic = set(freeze.synthetic)
    if set(freeze.blinded) != {f"{case_id}-blinded" for case_id in synthetic}:
        raise HistoricalCaseError(
            "blinded cohort does not match the frozen synthetic ids"
        )
    if set(freeze.perturbed) != {f"{case_id}-perturbed" for case_id in synthetic}:
        raise HistoricalCaseError(
            "perturbed cohort does not match the frozen synthetic ids"
        )
    if freeze.named_public:
        raise HistoricalCaseError("named public reconstructions are not in git")
    on_disk = {path.stem for path in VISIBLE_DIR.glob("*.json")}
    if on_disk != synthetic:
        raise HistoricalCaseError(
            "visible packets do not match the frozen synthetic cohort"
        )
    hidden_ids = {path.stem for path in HIDDEN_DIR.glob("*.json")}
    if hidden_ids != synthetic:
        raise HistoricalCaseError(
            "hidden references do not match the frozen synthetic cohort"
        )
    return freeze


def load_visible_packets() -> list[VisiblePacket]:
    """Agent-visible packets. This does not read hidden/."""
    freeze = load_cohorts()
    packets: list[VisiblePacket] = []
    for case_id in freeze.synthetic:
        payload = json.loads(
            (VISIBLE_DIR / f"{case_id}.json").read_text(encoding="utf-8")
        )
        packet = VisiblePacket.model_validate(payload)
        if packet.case_id != case_id:
            raise HistoricalCaseError(f"{case_id} visible id does not match the file")
        packets.append(packet)
    return packets


def search_visible(query: str) -> list[dict[str, Any]]:
    """Search cutoff packets only. Hidden causes are not in this index."""
    needle = require_non_blank(query, "query").casefold()
    rows: list[dict[str, Any]] = []
    for packet in load_visible_packets():
        row = _cutoff_row(packet)
        if needle in json.dumps(row).casefold():
            rows.append(row)
    return rows


def diagnosis_retrieval_rows() -> list[dict[str, Any]]:
    """Cutoff rows plus blinded and perturbed views. No post-incident text."""
    rows: list[dict[str, Any]] = []
    for packet in load_visible_packets():
        hidden = _load_hidden(packet.case_id)
        rows.append(_cutoff_row(packet))
        rows.append(_transformed_row(packet, hidden, "blinded"))
        rows.append(_transformed_row(packet, hidden, "perturbed"))
    return rows


def read_hidden_after_prediction(
    case_id: str,
    prediction: PredictionRecord,
) -> dict[str, Any]:
    """Open the scorer reference only after the prediction is stored."""
    if prediction.status != "closed" or not prediction.closed_at:
        raise HistoricalCaseError(
            "hidden reference stays closed until the prediction is stored"
        )
    parent_id, cohort, transformed = _resolve_case_id(
        require_non_blank(case_id, "case_id")
    )
    hidden = _load_hidden(parent_id)
    if prediction.dataset_id != hidden.dataset_id:
        raise HistoricalCaseError("prediction dataset does not match the case")
    return {
        "case_id": case_id,
        "parent_case_id": parent_id,
        "cohort": cohort,
        "transformed": transformed,
        "counts_as_real_historical": False,
        "guaranteed_unseen": False,
        "cause_known": hidden.cause_known,
        "cause": hidden.cause,
        "subsystem": hidden.subsystem,
        "appropriate_action": hidden.appropriate_action,
        "unacceptable_action": hidden.unacceptable_action,
        "exposure_risk": hidden.exposure_risk,
        "evidence_at_cutoff": list(hidden.evidence_at_cutoff),
    }


def diagnosis_score_case_ids() -> list[str]:
    """AV5 diagnosis ids: known cause, synthetic, not a transformed view."""
    return [
        packet.case_id
        for packet in load_visible_packets()
        if _load_hidden(packet.case_id).cause_known
    ]


def require_diagnosis_score_case(case_id: str) -> None:
    """Refuse unknown causes and transformed views."""
    parent_id, _cohort, transformed = _resolve_case_id(
        require_non_blank(case_id, "case_id")
    )
    if transformed:
        raise HistoricalCaseError("transformed case is not a real historical case")
    if not _load_hidden(parent_id).cause_known:
        raise HistoricalCaseError("unknown cause is not a diagnosis score")


def _cutoff_row(packet: VisiblePacket) -> dict[str, Any]:
    return {
        "case_id": packet.case_id,
        "cohort": packet.cohort,
        "transformed": False,
        "dataset_id": packet.dataset_id,
        "time_range_start": packet.time_range_start,
        "time_range_end": packet.time_range_end,
        "symptoms": list(packet.symptoms),
        "public_name": packet.public_name,
        "guaranteed_unseen": False,
    }


def _transformed_row(
    packet: VisiblePacket,
    hidden: HiddenReference,
    cohort: Literal["blinded", "perturbed"],
) -> dict[str, Any]:
    symptoms = list(packet.symptoms)
    if cohort == "perturbed":
        symptoms.append("perturbed extra step")
    row = {
        "case_id": f"{packet.case_id}-{cohort}",
        "cohort": cohort,
        "transformed": True,
        "derived_from": packet.case_id,
        "counts_as_real_historical": False,
        "guaranteed_unseen": False,
        "dataset_id": packet.dataset_id,
        "time_range_start": packet.time_range_start,
        "time_range_end": packet.time_range_end,
        "symptoms": symptoms,
    }
    if cohort == "blinded":
        row["time_range_start"] = "T0"
        row["time_range_end"] = "T0+window"
        row["public_name"] = ""
    _reject_prohibited(row, _prohibited_tokens(hidden), blinded=cohort == "blinded")
    return row


def _prohibited_tokens(hidden: HiddenReference) -> list[str]:
    tokens = [hidden.cause or "", hidden.mission_alias, hidden.post_incident_report]
    return [token for token in tokens if token.strip()]


def _reject_prohibited(
    row: dict[str, Any], tokens: list[str], *, blinded: bool
) -> None:
    blob = json.dumps(row)
    folded = blob.casefold()
    for token in tokens:
        if token.casefold() in folded:
            raise HistoricalCaseError("retrieval row contains scorer-only text")
    if blinded and (_DATE.search(blob) or _URL.search(blob)):
        raise HistoricalCaseError("blinded packet keeps a date or a source URL")


def _load_hidden(case_id: str) -> HiddenReference:
    path = HIDDEN_DIR / f"{case_id}.json"
    hidden = HiddenReference.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )
    if hidden.case_id != case_id:
        raise HistoricalCaseError(f"{case_id} hidden id does not match the file")
    return hidden


def _resolve_case_id(case_id: str) -> tuple[str, str, bool]:
    freeze = load_cohorts()
    if case_id in freeze.synthetic:
        return case_id, "synthetic", False
    if case_id in freeze.blinded:
        return case_id.removesuffix("-blinded"), "blinded", True
    if case_id in freeze.perturbed:
        return case_id.removesuffix("-perturbed"), "perturbed", True
    raise HistoricalCaseError(f"unknown historical case {case_id}")
