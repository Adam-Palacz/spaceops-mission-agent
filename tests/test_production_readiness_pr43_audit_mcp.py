"""PR4.3 audit integrity and MCP workload-identity tests."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "deploy" / "helm" / "spaceops"
SPRINT = ROOT / "roadmap" / "02.5-production-readiness" / "sprint-4"


def test_mcp_policy_requires_strict_mtls_and_named_principals() -> None:
    policy = (CHART / "templates" / "mcp-workload-identity.yaml").read_text(
        encoding="utf-8"
    )
    assert "kind: PeerAuthentication" in policy
    assert "mode: STRICT" in policy
    assert "kind: AuthorizationPolicy" in policy
    assert "principals:" in policy
    assert '"api"' in policy
    assert '"agent-worker"' in policy
    assert "namespaces:" not in policy
    assert "notPrincipals:" not in policy


def test_mcp_and_callers_request_istio_sidecars() -> None:
    for template in (
        "api.yaml",
        "agent-worker.yaml",
        "telemetry-mcp.yaml",
        "mcp-optional.yaml",
    ):
        text = (CHART / "templates" / template).read_text(encoding="utf-8")
        assert "sidecar.istio.io/inject" in text
        assert "mcpWorkloadIdentity.enabled" in text


def test_audit_signing_key_uses_external_secret_path() -> None:
    values = (CHART / "values.yaml").read_text(encoding="utf-8")
    external_secret = (CHART / "templates" / "external-secret.yaml").read_text(
        encoding="utf-8"
    )
    api = (CHART / "templates" / "api.yaml").read_text(encoding="utf-8")
    assert "auditSigningKey:" in values
    assert "AUDIT_SIGNING_KEY" in external_secret
    assert "AUDIT_SIGNING_KEY" in api


def test_pr43_boundary_evidence_passed_with_explicit_limitations() -> None:
    evidence = json.loads(
        (
            SPRINT / "evidence" / "PR4.3-security-boundary-drill-2026-11-23.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["result"] == "pass"
    assert evidence["audit"]["tamper_detected"] is True
    assert all(evidence["mcp_policy_static_checks"].values())
    assert evidence["platform_ops_write_actions"] == "disabled"
    assert any("live mesh" in limitation for limitation in evidence["limitations"])
