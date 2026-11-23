"""Postgres approval store with transactional execution claims."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Any
import uuid

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from config import settings


APPROVAL_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    incident_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    step JSONB NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMPTZ,
    decided_by TEXT,
    execution_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (execution_status IN ('pending', 'claimed', 'succeeded', 'failed')),
    execution_claim_token UUID,
    execution_worker_id TEXT,
    execution_claimed_at TIMESTAMPTZ,
    execution_lease_until TIMESTAMPTZ,
    execution_attempts INTEGER NOT NULL DEFAULT 0,
    execution_completed_at TIMESTAMPTZ,
    execution_result JSONB,
    execution_error TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_approval_requests_status_created
    ON approval_requests(status, created_at);
CREATE INDEX IF NOT EXISTS ix_approval_requests_execution_lease
    ON approval_requests(execution_lease_until)
    WHERE execution_status = 'claimed';
"""


@dataclass(frozen=True)
class ApprovalClaim:
    token: str
    worker_id: str
    idempotency_key: str


def _conn():
    return psycopg2.connect(settings.postgres_dsn)


def ensure_table() -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(APPROVAL_TABLE_SQL)
        conn.commit()


def _record(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in ("id", "execution_claim_token"):
        if result.get(key) is not None:
            result[key] = str(result[key])
    for key in (
        "created_at",
        "decided_at",
        "execution_claimed_at",
        "execution_lease_until",
        "execution_completed_at",
        "updated_at",
    ):
        value = result.get(key)
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    for key in ("step", "execution_result"):
        value = result.get(key)
        if isinstance(value, str):
            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:
                pass
    return result


def create(
    *,
    incident_id: str,
    step_index: int,
    step: dict[str, Any],
    reason: str = "restricted",
) -> str:
    ensure_table()
    request_id = str(uuid.uuid4())
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO approval_requests
                    (id, idempotency_key, incident_id, step_index, step, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    f"approval:{request_id}",
                    incident_id,
                    step_index,
                    Json(step),
                    reason,
                ),
            )
        conn.commit()
    return request_id


def list_requests(status: str | None = None) -> list[dict[str, Any]]:
    ensure_table()
    query = "SELECT * FROM approval_requests"
    params: tuple[Any, ...] = ()
    if status is not None:
        query += " WHERE status = %s"
        params = (status,)
    query += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [_record(row) or {} for row in rows]


def get_request(request_id: str) -> dict[str, Any] | None:
    ensure_table()
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM approval_requests WHERE id = %s", (request_id,))
            row = cur.fetchone()
    return _record(row)


def reject(request_id: str, decided_by: str) -> dict[str, Any] | None:
    ensure_table()
    now = datetime.now(timezone.utc)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE approval_requests
                SET status = 'rejected', decided_at = %s, decided_by = %s, updated_at = %s
                WHERE id = %s AND status = 'pending'
                RETURNING *
                """,
                (now, decided_by, now, request_id),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT * FROM approval_requests WHERE id = %s", (request_id,)
                )
                row = cur.fetchone()
        conn.commit()
    return _record(row)


def approve_and_claim(
    request_id: str,
    *,
    decided_by: str,
    worker_id: str,
    lease_seconds: int,
) -> tuple[dict[str, Any] | None, ApprovalClaim | None]:
    """Approve and exclusively claim execution in one transaction."""

    ensure_table()
    now = datetime.now(timezone.utc)
    lease_until = now + timedelta(seconds=max(30, lease_seconds))
    claim_token = str(uuid.uuid4())
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM approval_requests WHERE id = %s FOR UPDATE",
                (request_id,),
            )
            current = cur.fetchone()
            if current is None:
                return None, None
            if current["status"] == "pending":
                cur.execute(
                    """
                    UPDATE approval_requests
                    SET status = 'approved', decided_at = %s, decided_by = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (now, decided_by, now, request_id),
                )
            elif current["status"] != "approved":
                return _record(current), None

            cur.execute(
                """
                UPDATE approval_requests
                SET execution_status = 'claimed',
                    execution_claim_token = %s,
                    execution_worker_id = %s,
                    execution_claimed_at = %s,
                    execution_lease_until = %s,
                    execution_attempts = execution_attempts + 1,
                    updated_at = %s
                WHERE id = %s
                  AND status = 'approved'
                  AND (
                    execution_status = 'pending'
                    OR (
                      execution_status = 'claimed'
                      AND execution_lease_until IS NOT NULL
                      AND execution_lease_until < %s
                    )
                  )
                RETURNING *
                """,
                (
                    claim_token,
                    worker_id,
                    now,
                    lease_until,
                    now,
                    request_id,
                    now,
                ),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT * FROM approval_requests WHERE id = %s", (request_id,)
                )
                row = cur.fetchone()
        conn.commit()

    record = _record(row)
    if record and record.get("execution_claim_token") == claim_token:
        return record, ApprovalClaim(
            token=claim_token,
            worker_id=worker_id,
            idempotency_key=str(record["idempotency_key"]),
        )
    return record, None


def complete_execution(
    request_id: str,
    *,
    claim: ApprovalClaim,
    result: dict[str, Any],
) -> bool:
    now = datetime.now(timezone.utc)
    outcome = str(result.get("outcome") or "failure")
    status = "succeeded" if outcome == "success" else "failed"
    error = str(result.get("error_message") or "")[:2000] or None
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE approval_requests
                SET execution_status = %s,
                    execution_completed_at = %s,
                    execution_lease_until = NULL,
                    execution_result = %s,
                    execution_error = %s,
                    updated_at = %s
                WHERE id = %s
                  AND execution_status = 'claimed'
                  AND execution_claim_token = %s
                  AND execution_worker_id = %s
                """,
                (
                    status,
                    now,
                    Json(result),
                    error,
                    now,
                    request_id,
                    claim.token,
                    claim.worker_id,
                ),
            )
            updated = cur.rowcount
        conn.commit()
    return updated == 1


def count_stale_claims() -> int:
    """Return claimed executions whose lease expired and can be reclaimed."""

    ensure_table()
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM approval_requests
                WHERE execution_status = 'claimed'
                  AND execution_lease_until IS NOT NULL
                  AND execution_lease_until < NOW()
                """
            )
            row = cur.fetchone()
    return int(row[0] if row else 0)


def requeue_failed_execution(request_id: str) -> bool:
    """Operator reconciliation: return one failed approved execution to pending."""

    now = datetime.now(timezone.utc)
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE approval_requests
                SET execution_status = 'pending',
                    execution_claim_token = NULL,
                    execution_worker_id = NULL,
                    execution_claimed_at = NULL,
                    execution_lease_until = NULL,
                    execution_completed_at = NULL,
                    execution_result = NULL,
                    execution_error = NULL,
                    updated_at = %s
                WHERE id = %s
                  AND status = 'approved'
                  AND execution_status = 'failed'
                """,
                (now, request_id),
            )
            updated = cur.rowcount
        conn.commit()
    return updated == 1
