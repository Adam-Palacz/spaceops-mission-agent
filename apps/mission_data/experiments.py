"""Experiment registry and leakage checks (AV1.1).

A reported run names a registry id. The official OPSSAT-AD score keeps the
published train flag. That split is stratified random. Features may not use
ground-truth columns or statistics taken from test segments.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.mission_data.isolation import FORBIDDEN_LABEL_KEYS
from apps.mission_data.provenance import require_non_blank
from apps.mission_data.registry import REPO_ROOT

DEFAULT_EXPERIMENT_REGISTRY = (
    REPO_ROOT / "data" / "mission_registry" / "experiments.json"
)
_MD5 = re.compile(r"^[0-9a-f]{32}$")


class ExperimentError(ValueError):
    """An experiment record breaks the registry or leakage rules."""


class FeatureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    column: str = Field(..., min_length=1)
    uses_test_segment_statistics: bool = False


class ExperimentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    checksum: str = Field(..., min_length=32, max_length=32)
    split_name: Literal["published_train_flag", "exploratory"]
    split_basis: Literal["stratified_random", "other"]
    role: Literal["official", "exploratory"]
    code_revision: str = Field(..., min_length=1)
    feature_set: list[FeatureSpec] = Field(..., min_length=1)
    seed: int | None = None

    @model_validator(mode="after")
    def check_split_and_features(self) -> ExperimentRecord:
        require_non_blank(self.experiment_id, "experiment_id")
        require_non_blank(self.dataset_id, "dataset_id")
        require_non_blank(self.code_revision, "code_revision")
        if not _MD5.match(self.checksum):
            raise ValueError("checksum must be a 32-character md5")
        if self.split_name == "published_train_flag":
            if self.role != "official" or self.split_basis != "stratified_random":
                raise ValueError(
                    "the published train flag is a stratified-random official split"
                )
            if self.seed is not None:
                raise ValueError("the published train flag is not a resample")
        elif self.role != "exploratory" or self.seed is None:
            raise ValueError(
                "an exploratory split needs a seed and an exploratory role"
            )
        reject_leaky_features(self.feature_set)
        return self


class ExperimentRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["av1.experiments.v1"]
    experiments: list[ExperimentRecord] = Field(..., min_length=1)


def load_experiment_registry(path: Path | None = None) -> ExperimentRegistry:
    payload = json.loads(
        (path or DEFAULT_EXPERIMENT_REGISTRY).read_text(encoding="utf-8")
    )
    registry = ExperimentRegistry.model_validate(payload)
    keys = [(item.experiment_id, item.code_revision) for item in registry.experiments]
    if len(keys) != len(set(keys)):
        raise ExperimentError("duplicate experiment id and code revision")
    return registry


def reject_leaky_features(features: list[FeatureSpec]) -> None:
    """Reject test-segment statistics and ground-truth columns."""
    for feature in features:
        if feature.uses_test_segment_statistics:
            raise ExperimentError(
                f"{feature.name} uses a test-segment statistic in a training feature"
            )
        column = feature.column.casefold()
        name = feature.name.casefold()
        if column in FORBIDDEN_LABEL_KEYS or name in FORBIDDEN_LABEL_KEYS:
            raise ExperimentError(f"{feature.name} uses a ground-truth column")


def resolve_split(
    experiment_id: str, code_revision: str
) -> dict[str, str | int | None]:
    """Return the pinned split. The same id and revision always match."""
    cleaned_id = require_non_blank(experiment_id, "experiment_id")
    cleaned_revision = require_non_blank(code_revision, "code_revision")
    matches = [
        item
        for item in load_experiment_registry().experiments
        if item.experiment_id == cleaned_id and item.code_revision == cleaned_revision
    ]
    if len(matches) != 1:
        raise ExperimentError("experiment id and revision do not resolve one split")
    item = matches[0]
    return {
        "experiment_id": item.experiment_id,
        "dataset_id": item.dataset_id,
        "checksum": item.checksum,
        "split_name": item.split_name,
        "split_basis": item.split_basis,
        "role": item.role,
        "code_revision": item.code_revision,
        "seed": item.seed,
    }


def require_reported_run(experiment_id: str) -> ExperimentRecord:
    """AV2 cannot start a reported run without a registry id."""
    cleaned = require_non_blank(experiment_id, "experiment_id")
    matches = [
        item
        for item in load_experiment_registry().experiments
        if item.experiment_id == cleaned
    ]
    if not matches:
        raise ExperimentError("a reported run needs a registry id")
    return matches[0]
