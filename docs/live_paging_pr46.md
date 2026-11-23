# PR4.6 live paging drill

The 2026-11-23 drill used a temporary PagerDuty trial service and the Events API v2. The
production-admission decision stays **No-go**. PR4.6 stays **In progress** because the live page
was not emitted by Alertmanager and the trial account has only one escalation level.

## Secret path

Paging is off unless `observability.paging.enabled` is true. The chart then refuses to render
without an existing secret name and key. Alertmanager reads that key from a mounted file
(`routing_key_file`); the chart does not accept the key as a Helm value and does not render it
into a ConfigMap. Stage and prod should supply the key through the existing External Secrets path
under `observability.paging.externalSecretRemoteKey`.

Only alerts labeled `severity="page"` use the paging receiver. Every other alert stays on the local
`unpaged` receiver. A missing secret keeps the Alertmanager pod from starting, so the route fails
closed instead of sending with an empty key.

## Live drill

| Step | Result |
|------|--------|
| Synthetic trigger | Events API v2 returned HTTP 202 |
| Human acknowledgement | Incident UI recorded acknowledgement two minutes after creation; a later Events API acknowledge also returned HTTP 202 |
| Resolution | Incident status `Resolved`, two minutes after creation; Events API resolve returned HTTP 202 |
| Invalid routing key | HTTP 400, and the response body did not echo the submitted key |
| Escalation | The policy has one level and one on-call user. A second responder was not available |
| Teardown | The temporary service was deleted. Its direct URL then returned not found |

A follow-up enqueue sent after that deletion still returned HTTP 202 and did not echo the key. That
follow-up was acknowledged and resolved immediately. HTTP 202 after deletion does not prove that
the provider revoked the key, so key revocation remains unproven.

No routing key, account name, contact, subdomain, or screenshot is stored in this repository.
Provider incident history remains on the trial account.

## Remaining gate

BL-006 stays open. Closing it needs a page emitted by the secret-backed Alertmanager path, a second
escalation target or an explicit expiring exception, and proof that a removed integration key is
rejected.
