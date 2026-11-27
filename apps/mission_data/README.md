# Mission Data (`apps/mission_data`)

Source-agnostic telemetry adapters, provenance validation, mission/channel registry, dataset/ground-truth isolation, minimal historical-data model egress controls, and dataset adapters for Phase 03 ([03-real-world-mission-data](../../roadmap/03-real-world-mission-data/README.md)).

## Modules

- **`provenance.py`** — `ProvenanceRecord` and `RESERVED_METADATA_KEYS` (`mission_id`, `dataset_id`, `license`, `sample_kind`, `segment_id`, `sampling`, `time_basis`). Enforces version/checksum presence and rejects local paths, `file://` URIs, and credentials in `source_url`.
- **`registry.py`** — `MissionRegistry` and `load_registry()` for the git-versioned [data/mission_registry/registry.json](../../data/mission_registry/registry.json). Fails closed on unregistered channels, duplicate mission/dataset/channel IDs, or undeclared dataset channels.
- **`adapter.py`** — `TelemetryAdapter` protocol and `SyntheticFixtureAdapter`. Pure mapping to `TelemetryEventV1` without network access or license acceptance.
- **`isolation.py`** — `(mission_id, dataset_id)` isolation, `InvestigationTelemetryView`, evaluator-only `GroundTruthStore` / `PredictionStore`, role tool allowlists, OPS-SAT product separation (`opssat-ad` vs `opssat-reentry-uhf`), and prompt-template label checks (RD1.3).
- **`egress.py`** — Default-deny historical public-data model egress evaluation, derived-summary restriction inheritance, redaction rules, strict loopback verification, and direct-call/local-only transport guards (RD1.3).
- **`opssat_ad.py`** — Offline `OPSSATADAdapter`, Zenodo MD5 manifest loader, and separated telemetry/ground-truth importer for OPSSAT-AD (`opssat-ad` and synthetic CI `opssat-ad-lookalike`, RD2.1).
- **`opssat_reentry.py`** — Offline re-entry column map (RD2.2). Real UHF rows stay unread until a license and file checksums are recorded. The synthetic lookalike is `opssat-reentry-uhf-lookalike` and it does not write ground truth.
- **`readonly_pass.py`** — RD2.3 read-only lookalike query and channel-citation check. It does not call a model and does not mark the task Done.
- **`esa_ad.py`** — RD3.1 streaming lookalike for three anonymized ESA-AD contexts, plus the RD3.2 annotation split. Real archives stay unread until checksums are pinned. Mission3 is outside the published benchmark unless the report prints an override.
