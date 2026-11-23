"""
SpaceOps Agent — append-only audit log (S1.9, goals.md §4.6).
Schema: timestamp, trace_id, incident_id, actor, tool, args_hash, decision, policy_result, outcome, [error_message].
Storage: single NDJSON file; process only appends, no update/delete.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_AUDIT_PATH = REPO_ROOT / "data" / "audit.ndjson"
GENESIS_HASH = "0" * 64
_AUDIT_LOCK = Lock()


def _args_hash(args: dict) -> str:
    """Canonical hash of args for same args => same hash."""
    canonical = json.dumps(args, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_audit_path() -> Path:
    """Path to the audit NDJSON file (append-only)."""
    from config import settings

    path = (getattr(settings, "audit_log_path", None) or "").strip()
    if path:
        return Path(path)
    return DEFAULT_AUDIT_PATH


def _last_chain_state(path: Path) -> tuple[int, str]:
    if not path.exists():
        return 0, GENESIS_HASH
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
        if not lines:
            return 0, GENESIS_HASH
        last = json.loads(lines[-1])
        sequence = int(last.get("sequence") or 0)
        entry_hash = str(last.get("entry_hash") or "")
        if len(entry_hash) != 64:
            return 0, GENESIS_HASH
        return sequence, entry_hash
    except (OSError, ValueError, json.JSONDecodeError):
        return 0, GENESIS_HASH


def _entry_hash(entry: dict[str, Any]) -> str:
    content = {
        key: value
        for key, value in entry.items()
        if key not in {"entry_hash", "signature"}
    }
    canonical = json.dumps(
        content,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_chain(
    path: Path | None = None, *, signing_key: str | None = None
) -> dict[str, Any]:
    """Verify sequence, previous hashes, entry hashes, and optional HMAC signatures."""

    target = path or get_audit_path()
    previous = GENESIS_HASH
    checked = 0
    try:
        lines = [
            line for line in target.read_text(encoding="utf-8").splitlines() if line
        ]
    except FileNotFoundError:
        lines = []
    for expected_sequence, line in enumerate(lines, start=1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            return {"valid": False, "checked": checked, "reason": "invalid_json"}
        if entry.get("sequence") != expected_sequence:
            return {"valid": False, "checked": checked, "reason": "sequence_mismatch"}
        if entry.get("previous_hash") != previous:
            return {
                "valid": False,
                "checked": checked,
                "reason": "previous_hash_mismatch",
            }
        actual_hash = _entry_hash(entry)
        if not hmac.compare_digest(str(entry.get("entry_hash") or ""), actual_hash):
            return {"valid": False, "checked": checked, "reason": "entry_hash_mismatch"}
        signature = entry.get("signature")
        if signature is not None:
            if not signing_key:
                return {
                    "valid": False,
                    "checked": checked,
                    "reason": "signing_key_required",
                }
            expected_signature = hmac.new(
                signing_key.encode("utf-8"),
                actual_hash.encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(str(signature), expected_signature):
                return {
                    "valid": False,
                    "checked": checked,
                    "reason": "signature_mismatch",
                }
        previous = actual_hash
        checked += 1
    return {"valid": True, "checked": checked, "root_hash": previous}


def append_entry(
    *,
    trace_id: str,
    incident_id: str,
    actor: str,
    tool: str,
    args: dict,
    decision: str = "allow",
    policy_result: str = "allow",
    outcome: str = "success",
    error_message: str | None = None,
) -> None:
    """
    Append one audit log entry. Append-only; no update/delete.
    actor: "agent" | "human"
    decision: e.g. allow, deny, escalate
    policy_result: OPA result — allow, deny, error (or "n/a" if no OPA yet)
    outcome: success, empty, failure, skipped
    error_message: optional short, safe description when outcome=failure
    """
    path = get_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_LOCK:
        previous_sequence, previous_hash = _last_chain_state(path)
        entry = {
            "sequence": previous_sequence + 1,
            "previous_hash": previous_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "incident_id": incident_id,
            "actor": actor,
            "tool": tool,
            "args_hash": _args_hash(args),
            "decision": decision,
            "policy_result": policy_result,
            "outcome": outcome,
        }
        if error_message:
            entry["error_message"] = error_message[:200].replace("\n", " ")
        entry["entry_hash"] = _entry_hash(entry)
        from config import settings

        signing_key = str(getattr(settings, "audit_signing_key", "") or "")
        if signing_key:
            entry["signature"] = hmac.new(
                signing_key.encode("utf-8"),
                entry["entry_hash"].encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if bool(getattr(settings, "audit_stdout_export", False)):
            managed_entry = {"spaceops_audit": True, **entry}
            print(
                json.dumps(managed_entry, ensure_ascii=False, separators=(",", ":")),
                flush=True,
            )
