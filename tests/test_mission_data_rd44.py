"""RD4.4 SMAP/MSL stays waived and out of CI."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from apps.mission_data.smap_msl import (
    SmapMslError,
    load_smap_msl_manifest,
    refuse_import,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CI_FIXTURE = ROOT / "data" / "telemetry" / "telemetry.ndjson"
REGISTRY = ROOT / "data" / "mission_registry" / "registry.json"


def test_waiver_records_the_conflict_and_imports_nothing() -> None:
    before = hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest()
    manifest = load_smap_msl_manifest()
    assert manifest.decision == "waived"
    assert manifest.version == "v2.0"
    assert manifest.import_allowed is False
    assert manifest.files_in_ci is False
    assert manifest.channels_added is False
    assert manifest.samples_added is False
    assert manifest.third_party_mirror_used is False
    assert manifest.license_spdx == ""
    assert "Apache-2.0" in manifest.readme_software_license
    registry = REGISTRY.read_text(encoding="utf-8").casefold()
    assert "smap-telemanom" not in registry
    assert "msl-telemanom" not in registry
    with pytest.raises(SmapMslError, match="waived without data"):
        refuse_import()
    for folder in (ROOT / "data" / "telemetry", ROOT / "evals" / "fixtures"):
        names = " ".join(path.name.casefold() for path in folder.rglob("*"))
        assert "smap" not in names
        assert "telemanom" not in names
    assert hashlib.sha256(SYNTHETIC_CI_FIXTURE.read_bytes()).hexdigest() == before


def test_allow_decision_still_keeps_files_out_of_ci() -> None:
    allowed = load_smap_msl_manifest().model_copy(
        update={
            "decision": "allow",
            "import_allowed": True,
            "license_spdx": "LicenseRef-recorded",
        }
    )
    assert allowed.files_in_ci is False
    assert allowed.samples_added is False
    with pytest.raises(SmapMslError, match="out of CI"):
        refuse_import(allowed)
