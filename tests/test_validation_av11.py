"""AV1.1 experiment registry and leakage checks."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.mission_data.experiments import (
    ExperimentError,
    ExperimentRecord,
    FeatureSpec,
    load_experiment_registry,
    reject_leaky_features,
    require_reported_run,
    resolve_split,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"
REGISTRY_FILE = ROOT / "data" / "mission_registry" / "experiments.json"


def test_official_split_is_stratified_random_and_stable() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    record = load_experiment_registry().experiments[0]
    assert record.dataset_id == "opssat-ad"
    assert record.split_name == "published_train_flag"
    assert record.split_basis == "stratified_random"
    assert record.role == "official"
    assert record.seed is None
    text = REGISTRY_FILE.read_text(encoding="utf-8")
    assert "sample" not in text
    assert "CADC" not in text
    assert "anomaly" not in text
    first = resolve_split(record.experiment_id, record.code_revision)
    second = resolve_split(record.experiment_id, record.code_revision)
    assert first == second
    assert first["checksum"] == "c12fb83863afa4463dec07303a20bb14"
    require_reported_run(record.experiment_id)
    with pytest.raises(ExperimentError, match="registry id"):
        require_reported_run("missing-experiment")
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_test_segment_statistic_and_label_feature_are_rejected() -> None:
    with pytest.raises(ExperimentError, match="test-segment statistic"):
        reject_leaky_features(
            [
                FeatureSpec(
                    name="test_mean",
                    column="value",
                    uses_test_segment_statistics=True,
                )
            ]
        )
    with pytest.raises(ExperimentError, match="ground-truth"):
        reject_leaky_features([FeatureSpec(name="anomaly_flag", column="anomaly")])
    payload = load_experiment_registry().experiments[0].model_dump()
    payload["feature_set"] = [
        {
            "name": "copied_label",
            "column": "label",
            "uses_test_segment_statistics": False,
        }
    ]
    with pytest.raises(ValidationError, match="ground-truth"):
        ExperimentRecord.model_validate(payload)
