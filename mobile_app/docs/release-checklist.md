# Release Checklist

## 1) Build and Runtime Verification

- [x] Backend starts without errors (`python main.py` or Docker compose)
- [x] `npm run build` succeeds in `webapp/`
- [x] `npm run build:mobile:web` succeeds in `webapp/`
- [ ] Android native release build succeeds (`webapp/android` Gradle release lane)
- [ ] iOS archive/TestFlight lane succeeds on macOS (`webapp/ios` Xcode lane)
- [x] Frontend authentication works against backend
- [x] Protected routes load (`/home`, `/map`, `/social`, `/profile`, `/settings`, `/support`)
- [x] Critical smoke flows completed (auth, spot create/edit/delete, social follow, support ticket)

## 2) Configuration and Secrets

- [x] No production secret values hardcoded
- [x] `JWT_SECRET` explicitly configured in deployment
- [x] `MONGO_URL` configured per environment
- [x] `VITE_API_BASE_URL` points to correct backend
- [x] `.env` files are not committed; examples are documented

## 3) Error Handling and Logging

- [x] Backend returns sanitized error payloads (no traceback leakage)
- [x] Frontend notifications provide meaningful user messages
- [x] Unauthorized session transition works (single notice + auth redirect)
- [x] Operational logs exist for request failures and persistence failures

## 4) Security Baseline

- [x] CORS restricted for production origins
- [x] Auth checks verified on protected endpoints
- [x] Input validation verified for auth/profile/spot/support payloads
- [x] Password-change policy validated (current password + complexity)
- [x] Social block/follow constraints validated
- [x] Rate-limiting strategy documented (implemented or planned)

## 5) Persistence Baseline

- [x] Required indexes exist and are validated
- [x] Timestamps are consistently UTC
- [x] API ID serialization is consistent (`id` as string)
- [x] Repository policy enforced for generic/auth layers; social-layer repository split tracked in architecture backlog

## 6) Documentation and QA Artifacts

- [x] `ARCHITECTURE.md` updated
- [x] `API_SPEC.md` updated
- [x] `PERSISTENCE.md` updated
- [x] Mobile integration docs updated (`README`, `webapp/README`, Capacitor config)
- [x] ADR records updated for major decisions
- [x] `docs/test-protocol.md` completed for release commit
- [x] `docs/backend-architecture.drawio` and `docs/frontend-architecture.drawio` updated
- [x] `docs/uml-specifications.md` updated with diagram mapping

## 7) Known Limitations and Follow-Up

- [x] Remaining architecture gaps documented
- [x] API versioning migration status documented
- [x] Automated test coverage status documented
