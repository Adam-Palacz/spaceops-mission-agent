"""Git-versioned mission, spacecraft, subsystem, and channel registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.mission_data.provenance import require_non_blank, validate_source_url

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "data" / "mission_registry" / "registry.json"


class RegistryError(ValueError):
    """A channel, mission, or dataset is not in the registry."""


class ChannelEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str = Field(..., min_length=1)
    source_name: str = Field(..., min_length=1)
    unit: str | None = None
    kind: Literal["numeric", "categorical"]
    sampling: str = Field(..., min_length=1)

    @field_validator("channel_id", "source_name", "sampling")
    @classmethod
    def reject_blank(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")


class SubsystemEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subsystem_id: str = Field(..., min_length=1)
    channels: list[ChannelEntry] = Field(..., min_length=1)

    @field_validator("subsystem_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        return require_non_blank(value, "subsystem_id")


class SpacecraftEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spacecraft_id: str = Field(..., min_length=1)
    subsystems: list[SubsystemEntry] = Field(..., min_length=1)

    @field_validator("spacecraft_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        return require_non_blank(value, "spacecraft_id")


class DatasetEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    license_spdx: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    citation: str = Field(..., min_length=1)
    channel_ids: list[str] = Field(..., min_length=1)

    @field_validator("dataset_id", "license_spdx", "citation")
    @classmethod
    def reject_blank(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    @field_validator("source_url")
    @classmethod
    def check_source_url(cls, value: str) -> str:
        return validate_source_url(value)

    @field_validator("channel_ids")
    @classmethod
    def reject_blank_channel_ids(cls, values: list[str]) -> list[str]:
        return [require_non_blank(item, "channel_id") for item in values]


class MissionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    sample_kind: Literal["real", "synthetic"]
    spacecraft: list[SpacecraftEntry] = Field(..., min_length=1)
    datasets: list[DatasetEntry] = Field(..., min_length=1)

    @field_validator("mission_id", "name")
    @classmethod
    def reject_blank(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")


class RegistryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"]
    citation: str = Field(..., min_length=1)
    missions: list[MissionEntry] = Field(..., min_length=1)

    @field_validator("citation")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        return require_non_blank(value, "citation")


class RegisteredChannel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_id: str
    spacecraft_id: str
    subsystem_id: str
    dataset_id: str
    license_spdx: str
    channel_id: str
    source_name: str
    unit: str | None
    kind: Literal["numeric", "categorical"]
    sampling: str
    sample_kind: Literal["real", "synthetic"]


class MissionRegistry:
    def __init__(self, document: RegistryDocument) -> None:
        self.document = document
        self._channels: dict[tuple[str, str, str], RegisteredChannel] = {}
        seen_missions: set[str] = set()
        seen_datasets: set[str] = set()
        declared: dict[str, set[str]] = {}
        for mission in document.missions:
            if mission.mission_id in seen_missions:
                raise RegistryError(f"duplicate mission {mission.mission_id}")
            seen_missions.add(mission.mission_id)
            for dataset in mission.datasets:
                if dataset.dataset_id in seen_datasets:
                    raise RegistryError(f"duplicate dataset {dataset.dataset_id}")
                seen_datasets.add(dataset.dataset_id)
                declared.setdefault(mission.mission_id, set()).update(
                    dataset.channel_ids
                )
            seen: set[str] = set()
            for craft in mission.spacecraft:
                for subsystem in craft.subsystems:
                    for channel in subsystem.channels:
                        if channel.channel_id in seen:
                            raise RegistryError(
                                f"duplicate channel {channel.channel_id} in {mission.mission_id}"
                            )
                        seen.add(channel.channel_id)
                        for dataset in mission.datasets:
                            if channel.channel_id not in dataset.channel_ids:
                                continue
                            key = (
                                mission.mission_id,
                                dataset.dataset_id,
                                channel.channel_id,
                            )
                            self._channels[key] = RegisteredChannel(
                                mission_id=mission.mission_id,
                                spacecraft_id=craft.spacecraft_id,
                                subsystem_id=subsystem.subsystem_id,
                                dataset_id=dataset.dataset_id,
                                license_spdx=dataset.license_spdx,
                                channel_id=channel.channel_id,
                                source_name=channel.source_name,
                                unit=channel.unit,
                                kind=channel.kind,
                                sampling=channel.sampling,
                                sample_kind=mission.sample_kind,
                            )
            missing = declared.get(mission.mission_id, set()) - seen
            if missing:
                raise RegistryError(
                    f"dataset channels missing from {mission.mission_id}: {sorted(missing)}"
                )

    def require(
        self, mission_id: str, dataset_id: str, channel_id: str
    ) -> RegisteredChannel:
        found = self._channels.get((mission_id, dataset_id, channel_id))
        if found is None:
            raise RegistryError(
                f"channel {channel_id} is not registered for {mission_id}/{dataset_id}"
            )
        return found

    def channels_for_mission(self, mission_id: str) -> frozenset[str]:
        return frozenset(
            item.channel_id
            for (mission, _dataset, _channel), item in self._channels.items()
            if mission == mission_id
        )

    def channels_for_dataset(self, dataset_id: str) -> frozenset[str]:
        return frozenset(
            item.channel_id
            for (_, dataset, _), item in self._channels.items()
            if dataset == dataset_id
        )


def load_registry(path: Path | None = None) -> MissionRegistry:
    registry_path = path or DEFAULT_REGISTRY
    payload: Any = json.loads(registry_path.read_text(encoding="utf-8"))
    return MissionRegistry(RegistryDocument.model_validate(payload))
