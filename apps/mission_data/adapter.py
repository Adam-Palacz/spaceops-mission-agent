"""Pure adapters from an external record to TelemetryEventV1.

Download and license acceptance stay outside this package. An adapter never
opens a socket.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from apps.contracts.v1 import TelemetryEventV1
from apps.mission_data.provenance import ProvenanceRecord
from apps.mission_data.registry import MissionRegistry, RegisteredChannel


class TelemetryAdapter(Protocol):
    def adapt(
        self, record: Mapping[str, Any], provenance: ProvenanceRecord
    ) -> list[TelemetryEventV1]:
        """Return zero or more events for one raw record."""


class AdapterError(ValueError):
    """The raw record cannot be mapped onto the registry."""


def _require_registered(
    registry: MissionRegistry, provenance: ProvenanceRecord, channel_id: str
) -> RegisteredChannel:
    registered = registry.require(
        provenance.mission_id, provenance.dataset_id, channel_id
    )
    if provenance.sample_kind != registered.sample_kind:
        raise AdapterError(
            f"provenance sample_kind {provenance.sample_kind!r} does not match "
            f"registered {registered.sample_kind!r} for "
            f"{provenance.mission_id}/{provenance.dataset_id}"
        )
    if provenance.license_spdx != registered.license_spdx:
        raise AdapterError(
            f"provenance license {provenance.license_spdx!r} does not match "
            f"registered {registered.license_spdx!r} for "
            f"{provenance.mission_id}/{provenance.dataset_id}"
        )
    return registered


class SyntheticFixtureAdapter:
    """Map one committed CI fixture row. Does not read or rewrite the fixture file."""

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry

    def adapt(
        self, record: Mapping[str, Any], provenance: ProvenanceRecord
    ) -> list[TelemetryEventV1]:
        if provenance.sample_kind != "synthetic":
            raise AdapterError("synthetic fixture adapter rejects a real dataset")
        channel_id = str(record.get("channel") or "").strip()
        timestamp = str(record.get("ts") or "").strip()
        if not channel_id or not timestamp or "value" not in record:
            raise AdapterError("fixture row requires channel, ts, and value")
        registered = _require_registered(self._registry, provenance, channel_id)
        raw_subsystem = record.get("subsystem")
        if raw_subsystem is not None and str(raw_subsystem) != registered.subsystem_id:
            raise AdapterError(
                f"subsystem for {channel_id} does not match the registry"
            )
        raw_unit = record.get("unit")
        if raw_unit is not None and (
            registered.unit is None or str(raw_unit) != registered.unit
        ):
            raise AdapterError(f"unit for {channel_id} does not match the registry")
        segment = record.get("segment_id")
        segment_id: str | None = None
        if segment is not None:
            cleaned_segment = str(segment).strip()
            if cleaned_segment:
                segment_id = cleaned_segment
        return [
            TelemetryEventV1(
                event_id=f"{provenance.dataset_id}:{channel_id}:{timestamp}",
                ts=timestamp,
                channel=channel_id,
                value=record["value"],
                subsystem=registered.subsystem_id,
                unit=registered.unit,
                source="telemetry",
                metadata=provenance.metadata(segment_id),
            )
        ]
