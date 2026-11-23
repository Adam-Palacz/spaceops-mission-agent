"""
S2.5 — Approval requests store (file-based).

Persistent storage for approval_requests: create, list, get, approve, reject.
Idempotent: approve/reject on already-decided id returns success without re-execution.

When are files created? Only when the Act node runs a restricted step that OPA allows:
- Plan must contain a step with safe=false and action_type in {change_config, restart_service}.
- OPA must be running and return allow (policy allows that step; no "restart all" in action).
If OPA is down or denies → no create(), only escalation. See S2.4 / infra/opa/README.md.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from apps.agent.approval_store_postgres import ApprovalClaim

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORE_DIR = REPO_ROOT / "data" / "approvals"
_FILE_LOCK = Lock()


def _use_postgres() -> bool:
    from config import settings

    return (
        str(getattr(settings, "approval_store_backend", "file") or "file").lower()
        == "postgres"
    )


def _store_dir() -> Path:
    from config import settings

    path = getattr(settings, "approval_store_path", None) or ""
    if path:
        return Path(path)
    return DEFAULT_STORE_DIR


def _path_for_id(request_id: str) -> Path:
    return _store_dir() / f"{request_id}.json"


def create(
    *,
    incident_id: str,
    step_index: int,
    step: dict[str, Any],
    reason: str = "restricted",
) -> str:
    """
    Persist a new approval request; return its id.
    """
    if _use_postgres():
        from apps.agent.approval_store_postgres import create as postgres_create

        return postgres_create(
            incident_id=incident_id,
            step_index=step_index,
            step=step,
            reason=reason,
        )
    request_id = str(uuid.uuid4())
    store_dir = _store_dir()
    store_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "id": request_id,
        "incident_id": incident_id,
        "step_index": step_index,
        "step": step,
        "reason": reason,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decided_at": None,
        "decided_by": None,
    }
    with open(_path_for_id(request_id), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return request_id


def list_requests(status: str | None = None) -> list[dict[str, Any]]:
    """Return all approval requests, optionally filtered by status (pending, approved, rejected)."""
    if _use_postgres():
        from apps.agent.approval_store_postgres import (
            list_requests as postgres_list_requests,
        )

        return postgres_list_requests(status)
    store_dir = _store_dir()
    if not store_dir.exists():
        return []
    out = []
    for p in store_dir.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                rec = json.load(f)
            if status is None or (rec.get("status") == status):
                out.append(rec)
        except (json.JSONDecodeError, OSError):
            continue
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out


def get_request(request_id: str) -> dict[str, Any] | None:
    """Return one approval request by id, or None if not found."""
    if _use_postgres():
        from apps.agent.approval_store_postgres import (
            get_request as postgres_get_request,
        )

        return postgres_get_request(request_id)
    path = _path_for_id(request_id)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _update_status(
    request_id: str,
    new_status: str,
    decided_by: str,
) -> dict[str, Any] | None:
    rec = get_request(request_id)
    if rec is None:
        return None
    if rec.get("status") != "pending":
        return rec  # idempotent: already decided
    rec["status"] = new_status
    rec["decided_at"] = datetime.now(timezone.utc).isoformat()
    rec["decided_by"] = decided_by
    with open(_path_for_id(request_id), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    return rec


def approve(request_id: str, decided_by: str) -> dict[str, Any] | None:
    """Set status to approved; return updated record or None. Idempotent if already approved/rejected."""
    if _use_postgres():
        record, _claim = approve_and_claim(
            request_id,
            decided_by=decided_by,
            worker_id="legacy-approve",
            lease_seconds=300,
        )
        return record
    return _update_status(request_id, "approved", decided_by)


def reject(request_id: str, decided_by: str) -> dict[str, Any] | None:
    """Set status to rejected; return updated record or None. Idempotent if already approved/rejected."""
    if _use_postgres():
        from apps.agent.approval_store_postgres import reject as postgres_reject

        return postgres_reject(request_id, decided_by)
    return _update_status(request_id, "rejected", decided_by)


def approve_and_claim(
    request_id: str,
    *,
    decided_by: str,
    worker_id: str,
    lease_seconds: int,
) -> tuple[dict[str, Any] | None, ApprovalClaim | None]:
    """Approve and return the one execution claim won by this caller."""

    if _use_postgres():
        from apps.agent.approval_store_postgres import (
            approve_and_claim as postgres_approve_and_claim,
        )

        return postgres_approve_and_claim(
            request_id,
            decided_by=decided_by,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

    with _FILE_LOCK:
        rec = get_request(request_id)
        if rec is None:
            return None, None
        if rec.get("status") == "rejected":
            return rec, None
        if rec.get("status") == "approved" or rec.get("execution_status") in {
            "claimed",
            "succeeded",
            "failed",
        }:
            return rec, None
        now = datetime.now(timezone.utc).isoformat()
        token = str(uuid.uuid4())
        rec.update(
            {
                "status": "approved",
                "decided_at": now,
                "decided_by": decided_by,
                "idempotency_key": f"approval:{request_id}",
                "execution_status": "claimed",
                "execution_claim_token": token,
                "execution_worker_id": worker_id,
                "execution_claimed_at": now,
                "execution_attempts": 1,
            }
        )
        with open(_path_for_id(request_id), "w", encoding="utf-8") as file:
            json.dump(rec, file, indent=2, ensure_ascii=False)
        return rec, ApprovalClaim(
            token=token,
            worker_id=worker_id,
            idempotency_key=f"approval:{request_id}",
        )


def complete_execution(
    request_id: str,
    *,
    claim: ApprovalClaim,
    result: dict[str, Any],
) -> bool:
    """Complete only the execution claim owned by the supplied token and worker."""

    if _use_postgres():
        from apps.agent.approval_store_postgres import (
            complete_execution as postgres_complete_execution,
        )

        return postgres_complete_execution(request_id, claim=claim, result=result)

    with _FILE_LOCK:
        rec = get_request(request_id)
        if (
            rec is None
            or rec.get("execution_status") != "claimed"
            or rec.get("execution_claim_token") != claim.token
            or rec.get("execution_worker_id") != claim.worker_id
        ):
            return False
        rec["execution_status"] = (
            "succeeded" if result.get("outcome") == "success" else "failed"
        )
        rec["execution_result"] = result
        rec["execution_completed_at"] = datetime.now(timezone.utc).isoformat()
        rec["execution_claim_token"] = None
        with open(_path_for_id(request_id), "w", encoding="utf-8") as file:
            json.dump(rec, file, indent=2, ensure_ascii=False)
    return True
