# Mission Data (`apps/mission_data`)

Source-agnostic telemetry adapters, provenance validation, and mission/channel registry loader for Phase 03 ([03-real-world-mission-data](../../roadmap/03-real-world-mission-data/README.md)).

## Modules

- **`provenance.py`** — `ProvenanceRecord` and `RESERVED_METADATA_KEYS` (`mission_id`, `dataset_id`, `license`, `sample_kind`, `segment_id`). Enforces version/checksum presence and rejects local paths, `file://` URIs, and credentials in `source_url`.
- **`registry.py`** — `MissionRegistry` and `load_registry()` for the git-versioned [data/mission_registry/registry.json](../../data/mission_registry/registry.json). Fails closed on unregistered channels, duplicate mission/dataset/channel IDs, or undeclared dataset channels.
- **`adapter.py`** — `TelemetryAdapter` protocol and `SyntheticFixtureAdapter`. Pure mapping to `TelemetryEventV1` without network access or license acceptance.
