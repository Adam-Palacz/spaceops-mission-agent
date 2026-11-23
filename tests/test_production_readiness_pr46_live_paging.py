"""PR4.6 live paging configuration and evidence tests."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "deploy" / "helm" / "spaceops"
SPRINT = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-4"
EVIDENCE = SPRINT / "evidence" / "PR4.6-live-paging-2026-11-23.json"
PAGING = CHART / "templates" / "paging.yaml"


def test_paging_chart_reads_a_mounted_secret_and_fails_closed() -> None:
    template = PAGING.read_text(encoding="utf-8")
    values = (CHART / "values.yaml").read_text(encoding="utf-8")
    assert "routing_key_file: /etc/alertmanager/secrets/routing-key" in template
    assert "observability.paging.secret.name is required" in template
    assert "routing_key:" not in template
    assert "enabled: false" in values
    assert "pagerduty-routing-key" in values


def test_enabled_paging_template_has_no_routing_key_literal() -> None:
    helm = shutil.which("helm")
    if helm is None:
        return
    proc = subprocess.run(
        [
            helm,
            "template",
            "spaceops",
            str(CHART),
            "--set",
            "observability.paging.enabled=true",
            "--set",
            "observability.paging.secret.name=spaceops-paging",
            "--set",
            "observability.prometheus.enabled=true",
            "--set",
            "externalSecrets.enabled=true",
            "--set",
            "secrets.create=true",
            "--set",
            "secrets.postgresPassword=ci-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    rendered = proc.stdout
    assert "routing_key_file: /etc/alertmanager/secrets/routing-key" in rendered
    assert "secretName: spaceops-paging" in rendered
    assert "severity=\"page\"" in rendered
    assert "spaceops-stage-pagerduty-routing-key" in rendered
    assert not re.search(r"routing_key:\s*[A-Za-z0-9]", rendered)


def test_live_page_was_acknowledged_and_resolved() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    delivery = evidence["delivery"]
    assert evidence["result"] == "pass_with_escalation_and_sender_gaps"
    assert delivery["trigger_http_status"] == 202
    assert delivery["human_acknowledgement"] is True
    assert delivery["acknowledge_http_status"] == 202
    assert delivery["resolve_http_status"] == 202
    assert delivery["duration_minutes"] == 2
    assert delivery["alertmanager_emitted_page"] is False
    assert evidence["failed_delivery"]["invalid_routing_key_http_status"] == 400
    assert evidence["failed_delivery"]["response_echoed_routing_key"] is False


def test_escalation_and_key_revocation_keep_the_gate_blocked() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["escalation"]["policy_levels"] == 1
    assert evidence["escalation"]["distinct_person_escalation_verified"] is False
    assert evidence["teardown"]["temporary_service_deleted"] is True
    assert evidence["teardown"]["post_delete_enqueue_http_status"] == 202
    assert evidence["teardown"]["post_delete_key_revocation_proven"] is False
    assert evidence["done_gate"]["status"] == "blocked"


def test_pr46_evidence_contains_no_identifying_or_secret_material() -> None:
    text = EVIDENCE.read_text(encoding="utf-8")
    lower = text.lower()
    assert "palacz" not in lower
    assert "pagerduty.com" not in lower
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    assert not re.search(r"\b[A-Z0-9]{32}\b", text)
    assert '"routing_key_included": false' in text
    assert '"credentials_included": false' in text


def test_pr46_stays_in_progress_until_the_remaining_gates_close() -> None:
    spec = (SPRINT / "PR4.6-live-paging-drill.md").read_text(encoding="utf-8")
    board = (SPRINT / "BOARD.md").read_text(encoding="utf-8")
    assert "| **Status** | In progress |" in spec
    assert "real paging destination" in spec
    assert "| PR4.6 | Live paging integration drill | In progress |" in board
