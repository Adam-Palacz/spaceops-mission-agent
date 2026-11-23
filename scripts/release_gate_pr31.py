#!/usr/bin/env python3
"""PR3.1 blocking release gate with machine-readable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVIDENCE = REPO_ROOT / "artifacts" / "release-gates" / "latest.json"
NAMESPACE = "spaceops-stage"
RELEASE = "spaceops"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def static_steps() -> list[dict[str, Any]]:
    py = sys.executable
    chart = "deploy/helm/spaceops"
    safety_tests = [
        "tests/test_act_opa_policy.py",
        "tests/test_opa_client.py",
        "tests/test_guardrails_ps17.py",
        "tests/test_api.py",
    ]
    return [
        {"id": "lint", "command": ["ruff", "check", "."]},
        {
            "id": "typecheck",
            "command": [
                py,
                "-m",
                "mypy",
                "-m",
                "apps.agent",
                "-m",
                "apps.api",
                "-m",
                "config",
                "-m",
                "evals",
                "--ignore-missing-imports",
            ],
        },
        {"id": "tests", "command": [py, "-m", "pytest", "tests/", "-q"]},
        {
            "id": "approval_opa_fail_closed",
            "command": [py, "-m", "pytest", *safety_tests, "-q"],
        },
        {
            "id": "helm_lint_stage",
            "command": [
                "helm",
                "lint",
                chart,
                "-f",
                f"{chart}/values-stage.yaml",
            ],
        },
        {
            "id": "helm_lint_prod",
            "command": [
                "helm",
                "lint",
                chart,
                "-f",
                f"{chart}/values-prod.yaml",
            ],
        },
        {
            "id": "helm_template_stage",
            "command": [
                "helm",
                "template",
                RELEASE,
                chart,
                "-f",
                f"{chart}/values-stage.yaml",
                "--set",
                "secrets.postgresPassword=release-gate-placeholder",
            ],
        },
        {
            "id": "migration_offline_sql",
            "command": [py, "-m", "alembic", "upgrade", "head", "--sql"],
            "env": {
                "DATABASE_URL": "postgresql://release_gate:placeholder@localhost/spaceops"
            },
        },
    ]


def stage_steps(api_url: str, namespace: str) -> list[dict[str, Any]]:
    py = sys.executable
    return [
        {
            "id": "stage_health",
            "command": [
                py,
                "scripts/gcp_stage.py",
                "smoke",
                "--api-url",
                api_url,
                "--skip-kube-refresh",
            ],
        },
        {
            "id": "stage_scenarios_a_b",
            "command": [
                py,
                "scripts/gcp_stage.py",
                "demo",
                "--api-url",
                api_url,
                "--scenario",
                "both",
                "--skip-kube-refresh",
            ],
        },
        {
            "id": "queue_stream_status",
            "command": [
                "kubectl",
                "wait",
                "--for=condition=Ready",
                "pod",
                "-n",
                namespace,
                "-l",
                "app.kubernetes.io/component=telemetry-persister",
                "--timeout=2m",
            ],
        },
        {
            "id": "rollback_helm_snapshot",
            "command": ["helm", "get", "values", RELEASE, "-n", namespace, "-a"],
        },
        {
            "id": "rollback_image_snapshot",
            "command": [
                "kubectl",
                "get",
                "deployment",
                f"{RELEASE}-api",
                "-n",
                namespace,
                "-o",
                "jsonpath={.spec.template.spec.containers[*].image}",
            ],
        },
    ]


def _safe_output(text: str, limit: int = 4000) -> str:
    return text[-limit:]


def execute_step(step: dict[str, Any]) -> dict[str, Any]:
    started = _now()
    env = os.environ.copy()
    env.update(step.get("env", {}))
    try:
        proc = subprocess.run(
            step["command"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return {
            "id": step["id"],
            "status": "pass" if proc.returncode == 0 else "fail",
            "returncode": proc.returncode,
            "started_at": started,
            "finished_at": _now(),
            "command": step["command"],
            "output_tail": _safe_output(output),
            "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        }
    except OSError as exc:
        return {
            "id": step["id"],
            "status": "fail",
            "returncode": None,
            "started_at": started,
            "finished_at": _now(),
            "command": step["command"],
            "output_tail": str(exc),
            "output_sha256": hashlib.sha256(str(exc).encode()).hexdigest(),
        }


def check_dlq(api_url: str, max_rows: int) -> dict[str, Any]:
    url = f"{api_url.rstrip('/')}/dlq/telemetry?limit={max_rows + 1}"
    started = _now()
    try:
        with request.urlopen(url, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        if isinstance(body, list):
            count = len(body)
        elif isinstance(body, dict) and "dlq_events" in body and "count" in body:
            count = int(body["count"])
        else:
            raise ValueError("Unexpected DLQ response schema")
        status = "pass" if count <= max_rows else "fail"
        detail = f"{count} DLQ row(s), allowed maximum {max_rows}"
    except (error.URLError, ValueError, TypeError, AttributeError) as exc:
        status, count, detail = "fail", None, str(exc)
    return {
        "id": "dlq_threshold",
        "status": status,
        "started_at": started,
        "finished_at": _now(),
        "url": url,
        "observed_rows": count,
        "maximum_rows": max_rows,
        "output_tail": detail,
    }


def planned_step(step: dict[str, Any]) -> dict[str, Any]:
    return {"id": step["id"], "status": "planned", "command": step["command"]}


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry-run", "ci", "stage"), default="dry-run")
    parser.add_argument("--api-url", default=os.getenv("GCP_API_URL", ""))
    parser.add_argument("--namespace", default=NAMESPACE)
    parser.add_argument("--max-dlq-rows", type=int, default=0)
    parser.add_argument("--release-id", default=os.getenv("GITHUB_SHA", "local"))
    parser.add_argument("--operator", default=os.getenv("GITHUB_ACTOR", ""))
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.mode == "stage" and not args.api_url:
        raise SystemExit("--api-url or GCP_API_URL is required for stage mode")

    steps = static_steps()
    if args.mode == "stage":
        steps += stage_steps(args.api_url, args.namespace)

    report: dict[str, Any] = {
        "schema_version": "pr31.release-gate.v1",
        "release_id": args.release_id,
        "operator": args.operator,
        "mode": args.mode,
        "generated_at": _now(),
        "environment": args.namespace if args.mode == "stage" else "ci",
        "blocking": True,
        "steps": [],
    }

    if args.mode == "dry-run":
        report["steps"] = [planned_step(step) for step in steps]
        report["result"] = "planned"
    else:
        for step in steps:
            result = execute_step(step)
            report["steps"].append(result)
            if result["status"] == "fail":
                break
        if args.mode == "stage" and all(
            item["status"] == "pass" for item in report["steps"]
        ):
            report["steps"].append(check_dlq(args.api_url, args.max_dlq_rows))
        report["result"] = (
            "pass"
            if len(report["steps"]) == len(steps) + (1 if args.mode == "stage" else 0)
            and all(item["status"] == "pass" for item in report["steps"])
            else "fail"
        )

    report["finished_at"] = _now()
    write_report(report, args.evidence)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result"] in {"planned", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
