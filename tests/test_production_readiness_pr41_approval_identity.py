"""PR4.1 verified approval identity and role authorization tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
import jwt
import pytest

from apps.api import approval_auth


ISSUER = "https://issuer.example.test"
AUDIENCE = "spaceops-approval-api"
ROLE = "spaceops.approver"
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def oidc_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, other_private_key


@pytest.fixture
def oidc_settings(monkeypatch, oidc_keys):
    private_key, _ = oidc_keys
    monkeypatch.setattr("config.settings.approval_auth_mode", "oidc")
    monkeypatch.setattr("config.settings.approval_oidc_issuer", ISSUER)
    monkeypatch.setattr("config.settings.approval_oidc_audience", AUDIENCE)
    monkeypatch.setattr(
        "config.settings.approval_oidc_jwks_url",
        f"{ISSUER}/.well-known/jwks.json",
    )
    monkeypatch.setattr("config.settings.approval_oidc_algorithms", "RS256")
    monkeypatch.setattr("config.settings.approval_oidc_role_claim", "roles")
    monkeypatch.setattr("config.settings.approval_oidc_required_role", ROLE)
    monkeypatch.setattr(
        approval_auth,
        "_jwk_client",
        lambda _url: SimpleNamespace(
            get_signing_key_from_jwt=lambda _token: SimpleNamespace(
                key=private_key.public_key()
            )
        ),
    )


def _token(private_key, **overrides) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "operator-123",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "roles": [ROLE],
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test"})


def test_valid_oidc_principal_is_derived_from_signed_token(
    oidc_settings, oidc_keys
) -> None:
    private_key, _ = oidc_keys
    principal = approval_auth.authenticate_approval(
        authorization=f"Bearer {_token(private_key)}",
        api_key=None,
    )
    assert principal.subject == "operator-123"
    assert principal.audit_id == "oidc:operator-123"
    assert principal.roles == frozenset({ROLE})


@pytest.mark.parametrize(
    ("overrides", "status_code"),
    [
        ({"iss": "https://forged.example.test"}, 401),
        ({"aud": "another-api"}, 401),
        ({"exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, 401),
        ({"roles": ["spaceops.viewer"]}, 403),
        ({"sub": ""}, 401),
    ],
)
def test_oidc_claim_failures_are_closed(
    oidc_settings, oidc_keys, overrides, status_code
) -> None:
    private_key, _ = oidc_keys
    with pytest.raises(HTTPException) as exc_info:
        approval_auth.authenticate_approval(
            authorization=f"Bearer {_token(private_key, **overrides)}",
            api_key=None,
        )
    assert getattr(exc_info.value, "status_code", None) == status_code


def test_invalid_signature_and_malformed_token_fail_closed(
    oidc_settings, oidc_keys
) -> None:
    _, other_private_key = oidc_keys
    for token in (_token(other_private_key), "not-a-jwt"):
        with pytest.raises(HTTPException) as exc_info:
            approval_auth.authenticate_approval(
                authorization=f"Bearer {token}",
                api_key=None,
            )
        assert getattr(exc_info.value, "status_code", None) == 401


def test_oidc_mode_rejects_api_key_and_missing_bearer(oidc_settings) -> None:
    for authorization, api_key in ((None, None), (None, "legacy"), ("Basic abc", None)):
        with pytest.raises(HTTPException) as exc_info:
            approval_auth.authenticate_approval(
                authorization=authorization,
                api_key=api_key,
            )
        assert getattr(exc_info.value, "status_code", None) == 401


def test_api_ignores_forged_identity_header(
    api_client, tmp_path, monkeypatch, oidc_settings, oidc_keys
) -> None:
    from apps.agent.approval_store import create as create_approval

    private_key, _ = oidc_keys
    monkeypatch.setattr(
        "config.settings.approval_store_path", str(tmp_path / "approvals")
    )
    monkeypatch.setattr(
        "config.settings.audit_log_path", str(tmp_path / "audit.ndjson")
    )
    monkeypatch.setattr(
        "apps.agent.approval_executor.execute_approved_action",
        lambda _approval_id, _record: {"outcome": "success", "result": {}},
    )
    approval_id = create_approval(
        incident_id="inc-pr41",
        step_index=0,
        step={"action": "Change config", "action_type": "change_config"},
    )

    response = api_client.post(
        f"/approvals/{approval_id}/approve",
        headers={
            "Authorization": f"Bearer {_token(private_key)}",
            "X-Approval-By": "forged-admin",
        },
    )
    assert response.status_code == 200
    assert response.json()["approval"]["decided_by"] == "oidc:operator-123"


def test_production_helm_forces_oidc_and_evidence_passed() -> None:
    values = (ROOT / "deploy" / "helm" / "spaceops" / "values.yaml").read_text(
        encoding="utf-8"
    )
    prod = (ROOT / "deploy" / "helm" / "spaceops" / "values-prod.yaml").read_text(
        encoding="utf-8"
    )
    template = (
        ROOT / "deploy" / "helm" / "spaceops" / "templates" / "_api-env.tpl"
    ).read_text(encoding="utf-8")
    assert "approvalAuth:" in values
    assert "mode: oidc" in prod
    for variable in (
        "APPROVAL_AUTH_MODE",
        "APPROVAL_OIDC_ISSUER",
        "APPROVAL_OIDC_AUDIENCE",
        "APPROVAL_OIDC_JWKS_URL",
        "APPROVAL_OIDC_REQUIRED_ROLE",
    ):
        assert variable in template

    evidence = json.loads(
        (
            ROOT
            / "roadmap"
            / "02.5-production-readiness"
            / "sprint-4"
            / "evidence"
            / "PR4.1-oidc-drill-2026-11-23.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["result"] == "pass"
    assert len(evidence["vectors"]) == 7
    assert all(item["expected"] == item["actual"] for item in evidence["vectors"])


def test_ui_has_no_production_shared_key_or_forged_identity_header() -> None:
    page = (ROOT / "apps" / "ui" / "app" / "approvals" / "page.tsx").read_text(
        encoding="utf-8"
    )
    config = (ROOT / "apps" / "ui" / "lib" / "config.ts").read_text(
        encoding="utf-8"
    )
    dockerfile = (ROOT / "apps" / "ui" / "Dockerfile").read_text(encoding="utf-8")
    combined = "\n".join((page, config, dockerfile))
    assert "X-Approval-By" not in combined
    assert "NEXT_PUBLIC_APPROVAL_API_KEY" not in combined
    assert "NEXT_PUBLIC_LOCAL_APPROVAL_API_KEY" in combined
    assert "Production approval clients must use OIDC" in config
