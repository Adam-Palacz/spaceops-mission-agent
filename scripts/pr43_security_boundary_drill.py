#!/usr/bin/env python3
"""Exercise PR4.3 audit integrity and inspect MCP workload-identity policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.agent import audit_log  # noqa: E402
from config import settings  # noqa: E402


def run_drill() -> dict:
    with tempfile.TemporaryDirectory(prefix="spaceops-pr43-") as directory:
        path = Path(directory) / "audit.ndjson"
        settings.audit_log_path = str(path)
        settings.audit_signing_key = "synthetic-pr43-signing-key"
        for index in range(3):
            audit_log.append_entry(
                trace_id=f"pr43-{index}",
                incident_id="inc-pr43",
                actor="agent",
                tool="security_boundary_drill",
                args={"index": index},
            )
        valid_before = audit_log.verify_chain(
            path, signing_key="synthetic-pr43-signing-key"
        )
        lines = path.read_text(encoding="utf-8").splitlines()
        changed = json.loads(lines[1])
        changed["decision"] = "tampered"
        lines[1] = json.dumps(changed)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tamper_result = audit_log.verify_chain(
            path, signing_key="synthetic-pr43-signing-key"
        )

    policy = (
        ROOT
        / "deploy"
        / "helm"
        / "spaceops"
        / "templates"
        / "mcp-workload-identity.yaml"
    ).read_text(encoding="utf-8")
    prod = (ROOT / "deploy" / "helm" / "spaceops" / "values-prod.yaml").read_text(
        encoding="utf-8"
    )
    policy_checks = {
        "strict_mtls": "mode: STRICT" in policy,
        "workload_principals": "principals:" in policy,
        "api_service_account": '"api"' in policy,
        "worker_service_account": '"agent-worker"' in policy,
        "production_enabled": "mcpWorkloadIdentity:\n  enabled: true" in prod,
    }
    passed = (
        valid_before.get("valid") is True
        and tamper_result.get("valid") is False
        and all(policy_checks.values())
    )
    return {
        "schema_version": "pr43.security-boundary-drill.v1",
        "result": "pass" if passed else "fail",
        "audit": {
            "valid_chain_entries": valid_before.get("checked"),
            "root_hash_recorded": bool(valid_before.get("root_hash")),
            "tamper_detected": tamper_result.get("valid") is False,
            "tamper_reason": tamper_result.get("reason"),
            "signing_key_persisted": False,
        },
        "mcp_policy_static_checks": policy_checks,
        "platform_ops_write_actions": "disabled",
        "limitations": [
            "Istio mTLS authorization requires a live mesh allow/deny drill.",
            "Durable managed audit export is completed together with PR4.4.",
            "Named Security and pilot-owner disposition is still required.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_drill()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
