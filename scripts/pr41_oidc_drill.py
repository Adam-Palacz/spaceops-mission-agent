#!/usr/bin/env python3
"""Run a production-equivalent approval OIDC/JWKS verification drill."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
from typing import Any, Iterator

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
import jwt
from jwt.algorithms import RSAAlgorithm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api import approval_auth  # noqa: E402
from config import settings  # noqa: E402


AUDIENCE = "spaceops-approval-api"
REQUIRED_ROLE = "spaceops.approver"


class _JwksHandler(BaseHTTPRequestHandler):
    jwks: dict[str, Any] = {}

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self.path != "/.well-known/jwks.json":
            self.send_error(404)
            return
        payload = json.dumps(self.jwks).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: Any) -> None:
        return


@contextmanager
def _jwks_server(public_key: Any) -> Iterator[tuple[str, str]]:
    jwk = RSAAlgorithm.to_jwk(public_key, as_dict=True)
    jwk.update({"kid": "pr41-drill", "use": "sig", "alg": "RS256"})
    _JwksHandler.jwks = {"keys": [jwk]}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _JwksHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    issuer = f"http://127.0.0.1:{server.server_port}"
    try:
        yield issuer, f"{issuer}/.well-known/jwks.json"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _mint(private_key: Any, issuer: str, **overrides: Any) -> str:
    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "iss": issuer,
        "aud": AUDIENCE,
        "sub": "synthetic-operator",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "roles": [REQUIRED_ROLE],
    }
    claims.update(overrides)
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "pr41-drill"},
    )


def _configure(issuer: str, jwks_url: str) -> None:
    settings.approval_auth_mode = "oidc"
    settings.approval_oidc_issuer = issuer
    settings.approval_oidc_audience = AUDIENCE
    settings.approval_oidc_jwks_url = jwks_url
    settings.approval_oidc_algorithms = "RS256"
    settings.approval_oidc_role_claim = "roles"
    settings.approval_oidc_required_role = REQUIRED_ROLE
    approval_auth._jwk_client.cache_clear()


def run_drill() -> dict[str, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    vectors: list[dict[str, str]] = []

    with _jwks_server(private_key.public_key()) as (issuer, jwks_url):
        _configure(issuer, jwks_url)
        valid = approval_auth.authenticate_approval(
            authorization=f"Bearer {_mint(private_key, issuer)}",
            api_key=None,
        )
        vectors.append(
            {
                "id": "valid_approver",
                "expected": "allow",
                "actual": "allow",
                "subject": valid.audit_id,
            }
        )

        negative_tokens = {
            "wrong_issuer": _mint(private_key, "https://wrong-issuer.invalid"),
            "wrong_audience": _mint(private_key, issuer, aud="wrong-approval-audience"),
            "expired": _mint(
                private_key,
                issuer,
                exp=datetime.now(timezone.utc) - timedelta(seconds=1),
            ),
            "missing_role": _mint(private_key, issuer, roles=["spaceops.viewer"]),
            "invalid_signature": _mint(other_key, issuer),
            "malformed": "not-a-jwt",
        }
        for vector_id, token in negative_tokens.items():
            try:
                approval_auth.authenticate_approval(
                    authorization=f"Bearer {token}",
                    api_key=None,
                )
                actual = "allow"
            except HTTPException:
                actual = "deny"
            vectors.append({"id": vector_id, "expected": "deny", "actual": actual})

    passed = all(item["expected"] == item["actual"] for item in vectors)
    return {
        "schema_version": "pr41.oidc-verification-drill.v1",
        "result": "pass" if passed else "fail",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verification": {
            "signature_algorithm": "RS256",
            "jwks_transport": "ephemeral HTTP",
            "issuer_and_audience_enforced": True,
            "role_enforced": True,
            "caller_identity_header_used": False,
            "private_key_persisted": False,
        },
        "vectors": vectors,
        "limitations": [
            "The selected external pilot IdP still requires deployment-specific configuration.",
            "Security and production-pilot owner sign-off is not automated by this drill.",
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
