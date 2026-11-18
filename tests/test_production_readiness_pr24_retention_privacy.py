"""PR2.4 retention, privacy, and baseline log-redaction tests."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from apps.telemetry import JsonTraceFormatter, redact_sensitive_text

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY = REPO_ROOT / "docs" / "data_retention_privacy_pr24.md"
SPEC = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "PR2.4-retention-privacy.md"
)
EVIDENCE = (
    REPO_ROOT
    / "roadmap"
    / "02.5-production-readiness"
    / "sprint-2"
    / "evidence"
    / "PR2.4-retention-privacy-2026-09-26.json"
)


def test_pr24_policy_covers_required_data_sets_and_environments() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for data_set in (
        "Application/container logs",
        "Distributed traces",
        "Prometheus metrics",
        "Audit records",
        "Approval records",
        "Eval inputs and reports",
        "Generated incident reports",
    ):
        assert data_set in text
    for environment in ("Local/dev", "Stage", "Production pilot"):
        assert environment in text
    for classification in ("Public", "Internal", "Confidential", "Restricted"):
        assert classification in text


def test_pr24_policy_records_backend_deletion_export_and_ng3_gates() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for required in (
        "Google Cloud Trace",
        "Google Cloud Logging",
        "Operator export and deletion procedure",
        "External export rules",
        "NG3.3",
        "production-pilot `Go`",
    ):
        assert required in text
    assert "Jaeger has no persistent volume or retention control" in text
    assert EVIDENCE.is_file()


def test_pr24_redacts_known_secret_shapes() -> None:
    raw_values = (
        "actual-bearer-token",
        "sk-1234567890abcdef",
        "ghp_1234567890abcdef",
        "approval-secret",
        "database-secret",
    )
    message = (
        "Authorization: Bearer actual-bearer-token "
        "OPENAI_API_KEY=sk-1234567890abcdef "
        "github_token=ghp_1234567890abcdef "
        "approval_api_key='approval-secret' "
        "dsn=postgresql://spaceops:database-secret@postgres:5432/spaceops"
    )
    redacted = redact_sensitive_text(message)
    for value in raw_values:
        assert value not in redacted
    assert redacted.count("<redacted>") >= 5


def test_pr24_json_formatter_redacts_message_and_exception() -> None:
    formatter = JsonTraceFormatter()
    try:
        raise RuntimeError(
            "password=exception-secret " "Authorization: Bearer exception-bearer-token"
        )
    except RuntimeError:
        record = logging.LogRecord(
            name="test.privacy",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="api_key=%s",
            args=("message-secret",),
            exc_info=__import__("sys").exc_info(),
        )

    payload = json.loads(formatter.format(record))
    rendered = json.dumps(payload)
    for value in (
        "exception-secret",
        "exception-bearer-token",
        "message-secret",
    ):
        assert value not in rendered
    assert payload["message"] == "api_key=<redacted>"
    assert "<redacted>" in payload["exception"]


def test_pr24_traces_do_not_attach_prompt_or_payload_bodies() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8") for path in (REPO_ROOT / "apps").rglob("*.py")
    )
    forbidden_attributes = (
        'set_attribute("prompt"',
        'set_attribute("payload"',
        'set_attribute("request.body"',
        'set_attribute("response.body"',
        'set_attribute("authorization"',
        'set_attribute("cookie"',
    )
    for attribute in forbidden_attributes:
        assert attribute not in sources


def test_pr24_current_jaeger_is_explicitly_ephemeral() -> None:
    template = (
        REPO_ROOT / "deploy" / "helm" / "spaceops" / "templates" / "observability.yaml"
    ).read_text(encoding="utf-8")
    jaeger_section = template.split(
        "{{- if .Values.observability.otelCollector.enabled }}", maxsplit=1
    )[0]
    assert "kind: Deployment" in jaeger_section
    assert "persistentVolumeClaim" not in jaeger_section
    assert "volumeClaimTemplates" not in jaeger_section


def test_pr24_spec_is_done_without_claiming_managed_backend_deployed() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "| **Status** | Done |" in text
    assert "does not claim that the managed production backend is deployed" in text
    assert "PR3.4" in text
