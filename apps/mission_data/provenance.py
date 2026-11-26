"""Provenance carried beside TelemetryEventV1.

RD1.4 keeps the contract unchanged. These keys are reserved inside
``metadata`` and are not top-level fields: ``mission_id``, ``dataset_id``,
``license``, ``sample_kind``, ``segment_id``, ``sampling`` (RD2.1 addendum).
Anomaly labels and train/test flags do not belong here.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from apps.contracts.v1 import ContractBase

RESERVED_METADATA_KEYS: tuple[str, ...] = (
    "mission_id",
    "dataset_id",
    "license",
    "sample_kind",
    "segment_id",
    "sampling",
)

_ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")
_FILE_URI = re.compile(r"^file://", re.IGNORECASE)
_CREDENTIALS_IN_URL = re.compile(r"^[a-z][a-z0-9+.-]*://[^/\s]*@", re.IGNORECASE)
_CREDENTIAL_QUERY_PARAM = re.compile(
    r"(?:^|[?&;])(?:token|key|api_key|apikey|password|passwd|secret|auth|sig)=",
    re.IGNORECASE,
)


def require_non_blank(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be blank")
    return cleaned


def validate_source_url(value: str) -> str:
    cleaned = require_non_blank(value, "source_url")
    if (
        _ABSOLUTE_PATH.match(cleaned)
        or _FILE_URI.match(cleaned)
        or _CREDENTIALS_IN_URL.match(cleaned)
    ):
        raise ValueError("provenance source must not be a path or carry credentials")
    if _CREDENTIAL_QUERY_PARAM.search(cleaned):
        raise ValueError("provenance source must not carry credentials")
    return cleaned


class ProvenanceRecord(ContractBase):
    """Identity of a dataset version. Adapters do not download or accept a license."""

    dataset_id: str = Field(..., min_length=1)
    mission_id: str = Field(..., min_length=1)
    version: str | None = None
    checksum: str | None = None
    license_spdx: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    sample_kind: Literal["real", "synthetic"]

    @field_validator("dataset_id", "mission_id", "license_spdx")
    @classmethod
    def reject_blank_identifiers(cls, value: str, info: Any) -> str:
        return require_non_blank(value, info.field_name or "field")

    @field_validator("version", "checksum")
    @classmethod
    def normalize_optional_tokens(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_version_or_checksum(self) -> ProvenanceRecord:
        if not (self.version or self.checksum):
            raise ValueError("provenance requires a version or a checksum")
        return self

    @field_validator("source_url")
    @classmethod
    def reject_local_path_and_credentials(cls, value: str) -> str:
        return validate_source_url(value)

    def metadata(
        self,
        segment_id: str | None = None,
        *,
        sampling: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mission_id": self.mission_id,
            "dataset_id": self.dataset_id,
            "license": self.license_spdx,
            "sample_kind": self.sample_kind,
        }
        if segment_id is not None:
            cleaned_segment = str(segment_id).strip()
            if cleaned_segment:
                payload["segment_id"] = cleaned_segment
        if sampling is not None:
            cleaned_sampling = str(sampling).strip()
            if cleaned_sampling:
                payload["sampling"] = cleaned_sampling
        return payload
