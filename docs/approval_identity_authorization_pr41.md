# Approval identity and authorization (PR4.1)

## Decision

The production-pilot identity provider is **Google Cloud Identity Platform / Firebase
Authentication**, matching the existing GCP platform. The API uses standard OIDC verification and
is not coupled to a provider SDK:

- issuer: `https://securetoken.google.com/<project-id>`
- audience: the deployment's Identity Platform project ID
- JWKS: Google's Secure Token public-key endpoint
- algorithm allowlist: `RS256`
- role claim: `roles`
- required role: `spaceops.approver`

The project identifier is deployment configuration and must not be committed to public evidence.
An authorized private administration path assigns the custom role claim; callers cannot request or
override it through the SpaceOps API.

## Threat model

| Threat | Control |
|---|---|
| Forged caller identity header | `X-Approval-By` is ignored; audit identity comes from verified `sub`. |
| Stolen/expired token | Short-lived token expiry is mandatory; TLS and provider controls protect delivery. |
| Token minted for another API | Exact `aud` match is mandatory. |
| Token from another issuer | Exact `iss` match plus JWKS signature verification is mandatory. |
| Algorithm confusion | Configured asymmetric algorithm allowlist; pilot uses only `RS256`. |
| Authenticated non-approver | Required role is checked after cryptographic verification. |
| JWKS outage or malformed response | Verification fails closed; no API-key fallback in OIDC mode. |
| Static-key bypass | Production Helm values force `oidc`; `api_key` remains local compatibility only. |
| Sensitive identity disclosure | Audit stores the stable opaque `oidc:<sub>` reference, not bearer tokens. |

## Implementation

`apps/api/approval_auth.py` validates signature, issuer, audience, expiry, issued-at, subject, and
role before returning an immutable principal. Approval list/approve/reject endpoints use this
principal for authorization and audit attribution. Caller-supplied identity headers no longer
affect `decided_by`.

Configuration:

```text
APPROVAL_AUTH_MODE=oidc
APPROVAL_OIDC_ISSUER=https://securetoken.google.com/<project-id>
APPROVAL_OIDC_AUDIENCE=<project-id>
APPROVAL_OIDC_JWKS_URL=<google-secure-token-jwks-url>
APPROVAL_OIDC_ALGORITHMS=RS256
APPROVAL_OIDC_ROLE_CLAIM=roles
APPROVAL_OIDC_REQUIRED_ROLE=spaceops.approver
```

The Helm production overlay enables OIDC mode and intentionally leaves deployment-specific values
empty. Missing values return `503` on approval access rather than silently falling back.

The MVP web UI no longer defines a production-looking shared-key variable or sends
`X-Approval-By`. Its renamed `NEXT_PUBLIC_LOCAL_APPROVAL_API_KEY` path is explicitly local-only;
production controls remain disabled until an OIDC-aware UI client is implemented.

## Verification

The deterministic test suite covers valid tokens, wrong issuer, wrong audience, expiry, missing
role, invalid signature, malformed token, missing bearer token, API-key rejection in OIDC mode, and
forged `X-Approval-By`.

The production-equivalent drill starts an ephemeral HTTP JWKS endpoint, signs an RS256 token with an
in-memory key, executes one allow and six deny vectors through the real verifier, and destroys the
key without persisting it. See
[PR4.1 evidence](../roadmap/02.5-production-readiness/sprint-4/evidence/PR4.1-oidc-drill-2026-11-23.json).

## Remaining admission work

- Configure Identity Platform and private role administration in the selected pilot project.
- Execute one external-provider token verification on stage.
- Record named Security and production-pilot owner acceptance.

Until those items are complete, PR4.1 remains **In progress** and PR23-002 remains open.
