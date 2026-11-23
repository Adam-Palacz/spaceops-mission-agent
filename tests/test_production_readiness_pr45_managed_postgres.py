"""PR4.5 managed PostgreSQL HA/PITR configuration and evidence tests."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TERRAFORM = ROOT / "infra" / "terraform" / "gcp"
SPRINT = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-4"
EVIDENCE = SPRINT / "evidence" / "PR4.5-cloud-sql-ha-pitr-2026-11-23.json"


def test_cloud_sql_profile_requires_ha_pitr_private_network_and_iam() -> None:
    terraform = (TERRAFORM / "managed_postgres.tf").read_text(encoding="utf-8")
    for expected in (
        'database_version = "POSTGRES_15"',
        'availability_type = "REGIONAL"',
        "point_in_time_recovery_enabled = true",
        "transaction_log_retention_days = 7",
        "private_network",
        'ssl_mode                                      = "ENCRYPTED_ONLY"',
        '"cloudsql.iam_authentication"',
        'role    = "roles/cloudsql.client"',
        'role    = "roles/cloudsql.instanceUser"',
        'type     = "CLOUD_IAM_USER"',
    ):
        assert expected in terraform
    assert "google_sql_database_instance" in terraform
    assert "deletion_protection = false" in terraform


def test_live_drill_proves_failover_pitr_and_negative_access() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["result"] == "pass_with_provider_cleanup_pending"
    assert evidence["ha_failover"]["result"] == "pass"
    assert evidence["ha_failover"]["duration_seconds"] == 42
    assert evidence["ha_failover"]["active_zone_changed"] is True
    assert evidence["pitr"]["result"] == "pass"
    assert evidence["pitr"]["pre_boundary_rows"] == 1
    assert evidence["pitr"]["post_boundary_rows"] == 0
    assert evidence["pitr"]["alembic_connectivity_smoke"] == "pass"
    assert evidence["pitr"]["rto_target_met"] is True
    assert evidence["pitr"]["rpo_target_met"] is True
    assert evidence["negative_authorization"]["instance_api_http_status"] == 403
    assert evidence["negative_authorization"]["backup_api_http_status"] == 403
    assert evidence["negative_authorization"]["database_login"] == "denied"


def test_paid_resources_are_gone_but_provider_network_hold_is_explicit() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    teardown = evidence["teardown"]
    assert teardown["cloud_sql_instances_present"] == 0
    assert teardown["billable_database_runtime_present"] is False
    assert teardown["temporary_proxies_present"] == 0
    assert teardown["temporary_principals_present"] == 0
    assert teardown["provider_recovery_hold"]["status"] == "pending"
    assert teardown["provider_recovery_hold"]["provider_maximum_days"] == 4
    assert evidence["done_gate"]["status"] == "blocked"


def test_pr45_evidence_contains_no_identifying_or_secret_material() -> None:
    text = EVIDENCE.read_text(encoding="utf-8")
    lower = text.lower()
    assert "spaceops-project-" not in lower
    assert "adam.palacz" not in lower
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    assert "ya29." not in lower
    assert "postgresql://" not in lower
    assert '"credentials_included": false' in text
    assert '"network_addresses_included": false' in text


def test_pr45_stays_in_progress_until_provider_hold_clears() -> None:
    spec = (SPRINT / "PR4.5-managed-postgres-ha-pitr.md").read_text(
        encoding="utf-8"
    )
    board = (SPRINT / "BOARD.md").read_text(encoding="utf-8")
    assert "| **Status** | In progress |" in spec
    assert "PR4.5-cloud-sql-ha-pitr-2026-11-23.json" in spec
    assert "provider hold expires" in spec
    assert "| PR4.5 | Managed Postgres HA and PITR drill | In progress |" in board
