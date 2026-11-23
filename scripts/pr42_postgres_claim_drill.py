#!/usr/bin/env python3
"""Exercise concurrent Postgres approval claims and downstream idempotency."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.agent import approval_store  # noqa: E402
from config import settings  # noqa: E402


def _record_side_effect(dsn: str, idempotency_key: str) -> bool:
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS pr42_drill_side_effects (
                    idempotency_key TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                INSERT INTO pr42_drill_side_effects (idempotency_key)
                VALUES (%s)
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (idempotency_key,),
            )
            inserted = cur.rowcount == 1
        conn.commit()
    return inserted


def run_drill(dsn: str, contenders: int) -> dict[str, Any]:
    settings.database_url = dsn
    settings.approval_store_backend = "postgres"
    request_id = approval_store.create(
        incident_id="inc-pr42-drill",
        step_index=0,
        step={
            "action": "Synthetic idempotent side effect",
            "action_type": "change_config",
        },
        reason="pr42-concurrency-drill",
    )

    def contend(number: int):
        return approval_store.approve_and_claim(
            request_id,
            decided_by="oidc:synthetic-approver",
            worker_id=f"contender-{number}",
            lease_seconds=120,
        )

    with ThreadPoolExecutor(max_workers=contenders) as executor:
        outcomes = list(executor.map(contend, range(contenders)))
    winners = [(record, claim) for record, claim in outcomes if claim is not None]
    side_effect_count = 0
    completion_recorded = False
    if len(winners) == 1:
        _record, claim = winners[0]
        assert claim is not None
        if _record_side_effect(dsn, claim.idempotency_key):
            side_effect_count += 1
        completion_recorded = approval_store.complete_execution(
            request_id,
            claim=claim,
            result={"outcome": "success", "result": {"synthetic": True}},
        )
        if _record_side_effect(dsn, claim.idempotency_key):
            side_effect_count += 1

    final_record = approval_store.get_request(request_id) or {}
    _repeat_record, repeat_claim = approval_store.approve_and_claim(
        request_id,
        decided_by="oidc:synthetic-approver",
        worker_id="repeat",
        lease_seconds=120,
    )
    passed = (
        len(winners) == 1
        and side_effect_count == 1
        and completion_recorded
        and repeat_claim is None
        and final_record.get("execution_status") == "succeeded"
        and final_record.get("execution_attempts") == 1
    )
    return {
        "schema_version": "pr42.postgres-claim-drill.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result": "pass" if passed else "fail",
        "request_id": request_id,
        "contenders": contenders,
        "winning_claims": len(winners),
        "externally_visible_side_effects": side_effect_count,
        "completion_recorded": completion_recorded,
        "repeat_claimed": repeat_claim is not None,
        "final_execution_status": final_record.get("execution_status"),
        "execution_attempts": final_record.get("execution_attempts"),
        "database": "temporary local Postgres; no cloud resource",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--contenders", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_drill(args.dsn, max(2, args.contenders))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
