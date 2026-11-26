"""Source-agnostic mission telemetry adapters and the channel registry."""

from apps.mission_data.adapter import (
    AdapterError,
    SyntheticFixtureAdapter,
    TelemetryAdapter,
)
from apps.mission_data.provenance import RESERVED_METADATA_KEYS, ProvenanceRecord
from apps.mission_data.registry import (
    MissionRegistry,
    RegisteredChannel,
    RegistryError,
    load_registry,
)

__all__ = [
    "AdapterError",
    "MissionRegistry",
    "ProvenanceRecord",
    "RESERVED_METADATA_KEYS",
    "RegisteredChannel",
    "RegistryError",
    "SyntheticFixtureAdapter",
    "TelemetryAdapter",
    "load_registry",
]
