# Release Checklist

## 1) Build and Runtime Verification

- [ ] Backend starts without errors (`python main.py` or Docker compose)
- [ ] `npm run build` succeeds in `webapp/`
- [ ] Frontend authentication works against backend
- [ ] Protected routes load (`/home`, `/map`, `/social`, `/profile`, `/settings`, `/support`)
- [ ] Critical smoke flows completed (auth, spot create/edit/delete, social follow, support ticket)

## 2) Configuration and Secrets

- [ ] No production secret values hardcoded
- [ ] `JWT_SECRET` explicitly configured in deployment
- [ ] `MONGO_URL` configured per environment
- [ ] `VITE_API_BASE_URL` points to correct backend
- [ ] `.env` files are not committed; examples are documented

## 3) Error Handling and Logging

- [ ] Backend returns sanitized error payloads (no traceback leakage)
- [ ] Frontend notifications provide meaningful user messages
- [ ] Unauthorized session transition works (single notice + auth redirect)
- [ ] Operational logs exist for request failures and persistence failures

## 4) Security Baseline

- [ ] CORS restricted for production origins
- [ ] Auth checks verified on protected endpoints
- [ ] Input validation verified for auth/profile/spot/support payloads
- [ ] Password-change policy validated (current password + complexity)
- [ ] Social block/follow constraints validated
- [ ] Rate-limiting strategy documented (implemented or planned)

## 5) Persistence Baseline

- [ ] Required indexes exist and are validated
- [ ] Timestamps are consistently UTC
- [ ] API ID serialization is consistent (`id` as string)
- [ ] Repository-only DB access policy enforced (after refactor)

## 6) Documentation and QA Artifacts

- [ ] `ARCHITECTURE.md` updated
- [ ] `API_SPEC.md` updated
- [ ] `PERSISTENCE.md` updated
- [ ] ADR records updated for major decisions
- [ ] `docs/test-protocol.md` completed for release commit

## 7) Known Limitations and Follow-Up

- [ ] Remaining architecture gaps documented
- [ ] API versioning migration status documented
- [ ] Automated test coverage status documented
