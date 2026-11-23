"""PR4.4 managed logging, tracing, access, and teardown evidence tests."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "deploy" / "helm" / "spaceops"
TERRAFORM = ROOT / "infra" / "terraform" / "gcp"
SPRINT = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-4"
EVIDENCE = SPRINT / "evidence" / "PR4.4-managed-observability-2026-11-23.json"


def test_managed_backend_uses_keyless_least_privilege_identity() -> None:
    terraform = (TERRAFORM / "managed_observability.tf").read_text(encoding="utf-8")
    assert 'role    = "roles/cloudtrace.agent"' in terraform
    assert 'role    = "roles/logging.logWriter"' in terraform
    assert 'role               = "roles/iam.workloadIdentityUser"' in terraform
    assert "google_service_account_key" not in terraform
    assert "roles/logging.bucketWriter" not in terraform


def test_managed_overlay_exports_to_cloud_trace_without_jaeger() -> None:
    overlay = (CHART / "values-managed-observability.yaml").read_text(encoding="utf-8")
    template = (CHART / "templates" / "observability.yaml").read_text(
        encoding="utf-8"
    )
    service_accounts = (
        CHART / "templates" / "isolation-serviceaccounts.yaml"
    ).read_text(encoding="utf-8")
    assert "managed:\n    enabled: true" in overlay
    assert "jaeger:\n    enabled: false" in overlay
    assert "googlecloud:" in template
    assert "serviceAccountEmail" in service_accounts


def test_live_evidence_proves_query_denial_and_deletion() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["result"] == "pass"
    assert evidence["infrastructure"]["log_bucket_retention_days"] == 30
    assert evidence["authorized_query"]["log_records_found"] == 1
    assert evidence["authorized_query"]["trace_spans_found"] == 1
    assert evidence["authorized_query"]["correlation_present"] is True
    assert evidence["denied_query"]["separate_from_authorized_operator"] is True
    assert evidence["denied_query"]["http_status"] == 403
    assert evidence["denied_query"]["principal_deleted"] is True
    assert (
        evidence["deletion_expiry"]["log_bucket_lifecycle_after_destroy"]
        == "DELETE_REQUESTED"
    )
    assert evidence["teardown"]["retained_billable_runtime"] == []


def test_committed_evidence_is_sanitized() -> None:
    text = EVIDENCE.read_text(encoding="utf-8")
    lower = text.lower()
    assert "spaceops-project-" not in lower
    assert "adam.palacz" not in lower
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    assert "ya29." not in lower
    assert "bearer " not in lower
    assert '"credentials_included": false' in text
    assert '"raw_payload_included": false' in text


def test_pr44_is_done_and_links_evidence() -> None:
    spec = (SPRINT / "PR4.4-managed-observability.md").read_text(encoding="utf-8")
    board = (SPRINT / "BOARD.md").read_text(encoding="utf-8")
    assert "| **Status** | Done |" in spec
    assert "PR4.4-managed-observability-2026-11-23.json" in spec
    assert "| PR4.4 | Managed logging and tracing evidence | Done |" in board
