"""SMAP/MSL holdout gate (RD4.4).

The Telemanom v2.0 notices do not license the telemetry samples. Import stays
refused. An allow decision still keeps files out of CI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.mission_data.provenance import require_non_blank
from apps.mission_data.registry import REPO_ROOT

DEFAULT_SMAP_MSL_MANIFEST = (
    REPO_ROOT / "data" / "mission_registry" / "smap_msl_manifest.json"
)


class SmapMslError(ValueError):
    """SMAP/MSL samples are not imported."""


class SmapMslManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rd4.smap-msl.v1"]
    decision: Literal["waived", "allow"]
    distribution_url: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    license_file_url: str = Field(..., min_length=1)
    readme_software_license: str = Field(..., min_length=1)
    license_file_kind: str = Field(..., min_length=1)
    license_spdx: str = ""
    license_note: str = Field(..., min_length=1)
    third_party_mirror_used: Literal[False]
    import_allowed: bool
    files_in_ci: Literal[False]
    channels_added: Literal[False]
    samples_added: Literal[False]
    reserved_dataset_ids: list[str] = Field(..., min_length=2)

    @model_validator(mode="after")
    def check_decision(self) -> SmapMslManifest:
        require_non_blank(self.distribution_url, "distribution_url")
        require_non_blank(self.version, "version")
        require_non_blank(self.license_note, "license_note")
        if self.decision == "waived" and self.import_allowed:
            raise ValueError("a waiver does not allow import")
        if self.decision == "allow" and not self.license_spdx.strip():
            raise ValueError("an allow decision needs a license")
        return self


def load_smap_msl_manifest(path: Path | None = None) -> SmapMslManifest:
    payload = json.loads(
        (path or DEFAULT_SMAP_MSL_MANIFEST).read_text(encoding="utf-8")
    )
    return SmapMslManifest.model_validate(payload)


def refuse_import(manifest: SmapMslManifest | None = None) -> None:
    """Refuse the samples. Files stay out of CI even after an allow decision."""
    active = manifest or load_smap_msl_manifest()
    if active.decision != "allow" or not active.import_allowed:
        raise SmapMslError("SMAP/MSL is waived without data")
    raise SmapMslError("SMAP/MSL files stay out of CI")
