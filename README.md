# sql-agents-# sql-agents-ia

## Internal authentication and trust boundary

The AI API expects calls from trusted server-side services.

Before forwarding a user-scoped request, the calling service must validate
the user's Bearer token with the authentication backend and derive the user
ID from that authenticated response.

The caller supplies:
- `X-Signature`: the internal shared secret.
- `X-User-Id`: the authenticated user's positive integer ID.

The API validates the internal secret. Protected dataset operations also
check ownership before returning data or performing side effects.

### Deployment requirements

- Restrict access to the AI API to authorized server-side services.
- Do not publish its application port to untrusted networks.
- Do not expose it through an unrestricted reverse proxy or rewrite.
- Keep the shared secret exclusively in authorized server environments.
  Never include it in browser code, public environment variables or Git.
- Browser requests must use authenticated application proxies that derive
  identity from the authentication backend and generate internal headers
  themselves, ignoring caller-supplied identity headers.
- Apply these requirements in every environment. A developer's local
  Docker Compose configuration does not enforce them elsewhere.

### Limitations

`X-Signature` is a static shared secret, not a cryptographic signature
binding the user ID to the request. A caller that possesses the secret and
can reach the API can supply another user's ID.

This authentication mechanism therefore relies on the internal trust
boundary described above. If that boundary cannot be enforced, use an
independently verifiable identity mechanism, such as a signed, short-lived
identity assertion, before exposing the API.