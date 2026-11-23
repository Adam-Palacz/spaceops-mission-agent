"""Authentication and role authorization for approval endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hmac
from typing import Any

import jwt
from fastapi import HTTPException
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from config import settings


@dataclass(frozen=True)
class ApprovalPrincipal:
    """Verified identity used for authorization and audit attribution."""

    subject: str
    issuer: str
    roles: frozenset[str]
    auth_mode: str

    @property
    def audit_id(self) -> str:
        return f"{self.auth_mode}:{self.subject}"


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _setting(name: str) -> str:
    return str(getattr(settings, name, "") or "").strip()


def _roles_from_claim(claim: Any) -> frozenset[str]:
    if isinstance(claim, str):
        return frozenset(part for part in claim.replace(",", " ").split() if part)
    if isinstance(claim, list) and all(isinstance(item, str) for item in claim):
        return frozenset(item for item in claim if item)
    return frozenset()


@lru_cache(maxsize=8)
def _jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def _verify_oidc_token(token: str) -> ApprovalPrincipal:
    issuer = _setting("approval_oidc_issuer")
    audience = _setting("approval_oidc_audience")
    jwks_url = _setting("approval_oidc_jwks_url")
    role_claim = _setting("approval_oidc_role_claim") or "roles"
    required_role = _setting("approval_oidc_required_role") or "spaceops.approver"
    algorithms = [
        value.strip()
        for value in (_setting("approval_oidc_algorithms") or "RS256").split(",")
        if value.strip()
    ]

    if not issuer or not audience or not jwks_url:
        raise HTTPException(
            status_code=503,
            detail="Approval OIDC authentication is not fully configured",
        )

    try:
        signing_key = _jwk_client(jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except PyJWTError as exc:
        raise _unauthorized("Invalid approval bearer token") from exc
    except Exception as exc:
        raise _unauthorized("Unable to verify approval bearer token") from exc

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise _unauthorized("Approval token has no valid subject")
    roles = _roles_from_claim(claims.get(role_claim))
    if required_role not in roles:
        raise HTTPException(status_code=403, detail="Approver role is required")
    return ApprovalPrincipal(
        subject=subject.strip(),
        issuer=issuer,
        roles=roles,
        auth_mode="oidc",
    )


def authenticate_approval(
    *,
    authorization: str | None,
    api_key: str | None,
) -> ApprovalPrincipal:
    """Authenticate an approval caller without trusting caller identity headers."""

    mode = (_setting("approval_auth_mode") or "api_key").lower()
    if mode == "oidc":
        if not authorization or not authorization.lower().startswith("bearer "):
            raise _unauthorized("Approval bearer token is required")
        token = authorization[7:].strip()
        if not token:
            raise _unauthorized("Approval bearer token is required")
        return _verify_oidc_token(token)

    if mode == "api_key":
        expected = _setting("approval_api_key")
        if not expected:
            raise HTTPException(
                status_code=501,
                detail="Approval API key not configured (set APPROVAL_API_KEY)",
            )
        candidate = (api_key or "").strip()
        if (
            not candidate
            and authorization
            and authorization.lower().startswith("bearer ")
        ):
            candidate = authorization[7:].strip()
        if not candidate or not hmac.compare_digest(candidate, expected):
            raise _unauthorized("Invalid or missing approval credential")
        return ApprovalPrincipal(
            subject="legacy-api-key",
            issuer="local",
            roles=frozenset({"spaceops.approver"}),
            auth_mode="api_key",
        )

    raise HTTPException(
        status_code=503, detail="Unsupported approval authentication mode"
    )
