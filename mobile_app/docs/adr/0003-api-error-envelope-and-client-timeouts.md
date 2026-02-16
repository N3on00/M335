# ADR 0003: Standardize API Error Envelope and Add Client Timeout/Retry Policy

- Status: Proposed
- Date: 2026-02-16

## Context

Error responses are currently inconsistent across backend paths, and the frontend transport has no explicit timeout/retry behavior.

Evidence:

- Generic CRUD router returns traceback-rich payload:
  - `backend/routing/router.py:62`
- Auth/social endpoints mainly return plain detail strings:
  - `backend/routing/auth_routes.py:450`
- Frontend parser handles mixed payload structures:
  - `webapp/src/services/apiErrors.js:49`
  - `webapp/src/services/apiErrors.js:155`
- ApiClient uses bare `fetch` without timeout/retry:
  - `webapp/src/services/apiClient.js:39`

## Decision

1. Introduce one backend error envelope:
   - `error.code`
   - `error.message`
   - `error.details[]`
   - `error.request_id`
   - `error.timestamp_utc`
2. Remove traceback data from client-visible payloads in production.
3. Add frontend transport policy:
   - timeout via `AbortController`
   - retry only idempotent GET on network/5xx
   - no automatic retry for mutating operations

## Alternatives Considered

1. Keep current mixed format and rely on frontend heuristics.
2. Add timeout only, keep mixed backend errors.
3. Move immediately to generated OpenAPI client without transitional hardening.

## Consequences

### Positive

- Stable API contract and simpler frontend handling.
- Better resilience under transient network/server failures.
- Better security posture by avoiding traceback leakage.

### Negative

- Requires coordinated backend + frontend changes.
- Temporary compatibility layer needed during migration.
