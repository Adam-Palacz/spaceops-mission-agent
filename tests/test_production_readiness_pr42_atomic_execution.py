"""PR4.2 durable approval and atomic execution-claim tests."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Thread

from apps.agent import approval_store


ROOT = Path(__file__).resolve().parents[1]
SPRINT = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-4"


def test_file_compatibility_claim_is_process_atomic(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("config.settings.approval_store_backend", "file")
    monkeypatch.setattr(
        "config.settings.approval_store_path", str(tmp_path / "approvals")
    )
    approval_id = approval_store.create(
        incident_id="inc-file-race",
        step_index=0,
        step={"action": "Synthetic", "action_type": "restart_service"},
    )
    outcomes = []

    def contend(index: int) -> None:
        outcomes.append(
            approval_store.approve_and_claim(
                approval_id,
                decided_by="oidc:approver",
                worker_id=f"thread-{index}",
                lease_seconds=60,
            )
        )

    threads = [Thread(target=contend, args=(index,)) for index in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    claims = [claim for _record, claim in outcomes if claim is not None]
    assert len(claims) == 1

    assert approval_store.complete_execution(
        approval_id,
        claim=claims[0],
        result={"outcome": "success", "result": {"synthetic": True}},
    )
    _record, duplicate = approval_store.approve_and_claim(
        approval_id,
        decided_by="oidc:approver",
        worker_id="duplicate",
        lease_seconds=60,
    )
    assert duplicate is None


def test_postgres_schema_has_transactional_claim_guards() -> None:
    source = (ROOT / "apps" / "agent" / "approval_store_postgres.py").read_text(
        encoding="utf-8"
    )
    migration = (
        ROOT / "alembic" / "versions" / "20261123_0004_pr42_approval_claims.py"
    ).read_text(encoding="utf-8")
    assert "FOR UPDATE" in source
    for required in (
        "execution_claim_token",
        "execution_lease_until",
        "execution_attempts",
        "idempotency_key",
    ):
        assert required in source
        assert required in migration


def test_live_local_postgres_drill_proves_one_claim_and_side_effect() -> None:
    evidence = json.loads(
        (SPRINT / "evidence" / "PR4.2-postgres-claim-drill-2026-11-23.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["result"] == "pass"
    assert evidence["contenders"] >= 2
    assert evidence["winning_claims"] == 1
    assert evidence["externally_visible_side_effects"] == 1
    assert evidence["repeat_claimed"] is False
    assert evidence["final_execution_status"] == "succeeded"
    assert evidence["database"] == "temporary local Postgres; no cloud resource"


def test_production_uses_postgres_approval_store() -> None:
    prod = (ROOT / "deploy" / "helm" / "spaceops" / "values-prod.yaml").read_text(
        encoding="utf-8"
    )
    template = (
        ROOT / "deploy" / "helm" / "spaceops" / "templates" / "_api-env.tpl"
    ).read_text(encoding="utf-8")
    assert "storeBackend: postgres" in prod
    assert "APPROVAL_STORE_BACKEND" in template
    assert "APPROVAL_EXECUTION_LEASE_SECONDS" in template
