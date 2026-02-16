# ADR 0001: Python GUI Prototype and Pivot to Web Client

- Status: Proposed (documents existing project history)
- Date: 2026-02-16

## Context

The repository started with a Python GUI (Kivy) client and later introduced a full Vue web client.

Evidence:

- Python app introduction: commit `31f78df "mobile app starts"`
- Kivy prototype notes: `app/README.md:1`, `app/README.md:19`
- Python client auth/session work: commit `7cf9c9b "add mobile auth flow with session restore and crash reporting"`
- Python client map CRUD improvements: commit `c382497 "improve mobile spot CRUD and map interactions with better error feedback"`
- Full Vue client introduction: commit `253bb95 "add Vue web client with auth, map, social, profile, and support flows"`
- Ongoing activity concentrated in webapp commits after pivot (`a3671b8`, `49b5316`, `f128b45`, `ca07f5e`, `73610a4`).

## Decision

Treat `webapp/` as the active delivery client and `app/` as historical prototype context.

- New feature and rubric-hardening work targets `webapp/` + backend.
- `app/` remains in repository to preserve project evolution traceability.

## Alternatives Considered

1. Keep Python GUI as primary client and stop web development.
2. Maintain Python GUI and webapp equally in parallel.
3. Remove `app/` from repository entirely.

## Consequences

### Positive

- Easier onboarding and validation in browser runtime.
- Faster UI iteration cycle in active client.
- Clearer deployment path for reviewers.

### Negative

- Historical code remains and can create ambiguity if not documented.
- Dual-client history requires explicit scope statements in docs.
