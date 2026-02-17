# M335 Max-Points Assessment and Hardening Plan

## Scope and Evidence Rules

- Scope: this assessment targets the active stack (`webapp/` + backend API) and treats `app/` as historical prototype context.
- Evidence format used in this report:
  - Code evidence: `path:line`
  - Git evidence: `commitHash "message"`
- If rationale is not explicitly documented in repository artifacts, it is marked as **Assumption**.

## Status Update (2026-02-17)

- Backend smoke tests implemented: `backend/tests/test_api_routes_smoke.py`
- Frontend contract/resilience tests implemented: `webapp/src/tests/`
- CI pipeline implemented: `.github/workflows/ci.yml`
- Executed test protocol completed: `docs/test-protocol.md`
- Two UML diagrams available: `docs/backend-architecture.drawio`, `docs/frontend-architecture.drawio`

---

## 1) Executive Overview

### Project Purpose and Target Users

- SpotOnSight is a map-based platform to discover, save, and share spots, including social interactions around those spots.
  - Evidence: `README.md:1`, `README.md:3`, `webapp/README.md:1`, `webapp/src/router/index.js:17`
- Target users are authenticated end users who manage personal spots, social relations, and support tickets.
  - Evidence: `webapp/src/router/index.js:16`, `webapp/src/router/index.js:22`, `backend/routing/auth_routes.py:973`

### Current Architecture at a Glance

- Frontend: Vue 3 + Vite SPA with registry-driven screen composition.
  - Evidence: `webapp/package.json:17`, `webapp/src/core/registry.js:8`, `webapp/src/components/layouts/SlotScreenLayout.vue:13`
- Frontend layering: View -> Registration -> Controller -> Service -> ApiClient.
  - Evidence: `webapp/src/views/HomeView.vue:13`, `webapp/src/registrations/homeUi.js:1`, `webapp/src/controllers/spotsController.js:3`, `webapp/src/services/spotsService.js:4`, `webapp/src/services/apiClient.js:3`
- Backend: FastAPI app builder + auth/social router + decorator-generated CRUD routers + MongoDB.
  - Evidence: `backend/routing/routing.py:18`, `backend/routing/routing.py:29`, `backend/routing/registry.py:31`, `backend/data/mongo_repository.py:9`
- Integrations: location search via Nominatim with Photon fallback.
  - Evidence: `webapp/src/services/locationSearchService.js:80`, `webapp/src/services/locationSearchService.js:112`

### Max-Points Status (Current)

| Rubric Area | Current Status | Main Blocker(s) |
|---|---|---|
| Clean Code / DRY / KISS | Partial | Repeated owner-profile and file-base64 logic in multiple components |
| Architecture / Layering | Partial | Backend auth/social routes mix routing, business logic, and persistence |
| Frontend ↔ Backend contract | Partial | Error format inconsistency; no timeout/retry policy |
| Data persistence | Partial | Repository bypass and timestamp timezone inconsistency |
| Version control | Good | Conventional commit format not consistently enforced |
| Tests | Missing | No automated tests + no executed protocol artifact |
| Deliverable readiness | Partial | Setup docs exist; release checklist/test protocol missing in baseline |
| Bonus (docs/observability) | Partial | No ADR pack and no explicit logging strategy |

### Minimal Hardening Roadmap (Prioritized)

1. Add documentation pack (architecture/API/persistence/ADR/test/release checklist).
2. Remove frontend duplication (owner loading + file conversion helpers).
3. Enforce backend layering (Router -> Service -> Repository -> DB).
4. Standardize API error envelope and add client timeout/retry.
5. Add backend/frontend smoke tests and protocol evidence.

---

## 2) Project Evolution and Decision History

## Phase A - Python GUI Prototype

### What was built

- Kivy-based client scaffold with MVC-ish structure and map placeholder.
  - Evidence: `app/README.md:1`, `app/README.md:19`, commit `31f78df "mobile app starts"`
- Extended Python client functionality for auth/session/crash reporting and map CRUD interaction.
  - Evidence: commit `7cf9c9b "add mobile auth flow with session restore and crash reporting"`, commit `c382497 "improve mobile spot CRUD and map interactions with better error feedback"`

### Problems found

- The Python GUI path enabled the first cross-platform prototype but became less suitable for long-term feature velocity and maintainability.
- Supporting evidence:
  - rapid introduction of complete Vue web client (`253bb95`)
  - no new `app/` changes after `c382497`
  - current mobile packaging now handled through Capacitor in `webapp/`

## Phase B - Pivot Decision

### Decision and rationale

- The project pivoted to a Vue web client as the active solution.
  - Evidence: commit `253bb95 "add Vue web client with auth, map, social, profile, and support flows"`
- Rationale is now explicitly documented:
  - initial implementation used Python GUI as the first known cross-platform route
  - active delivery shifted to Vue + Capacitor to ship one frontend to browser/Android/iOS
  - Evidence: `README.md`, `docs/mobile-cross-platform-plan.md`

### Structural impact

- Added full `webapp/` application architecture and route-level feature parity.
  - Evidence: commit `253bb95` file list (webapp root and full src tree)
- Continued backend auth/social API expansion to support new client.
  - Evidence: commit `47aafe5 "add JWT auth/social API routes and backend dependencies"`

## Phase C - Current Architecture Iteration

- Ongoing development is concentrated on webapp UX, mobile navigation, notifications, and session handling.
  - Evidence: commits `a3671b8`, `49b5316`, `2129e8b`, `f128b45`, `ca07f5e`, `73610a4`
- Python GUI remains in repository as historical artifact.
  - Evidence: latest `app/` commit `c382497`; latest `webapp/` commit `73610a4`

---

## 3) Rubric Mapping With Evidence

## A) Clean Code / DRY / KISS

### Target state

- Single-purpose modules and reusable shared logic.
- No duplicate business helpers across components.

### Current state

- Shared action/error helpers exist in `uiShared`.
  - Evidence: `webapp/src/registrations/uiShared.js:204`, `webapp/src/registrations/uiShared.js:250`
- Duplicate owner-profile loading logic appears in three components.
  - Evidence: `webapp/src/components/map/MapWorkspace.vue:272`, `webapp/src/components/home/HomeDiscover.vue:73`, `webapp/src/components/profile/ProfileSummary.vue:99`
- Duplicate file-to-base64 helper appears in two components.
  - Evidence: `webapp/src/components/map/SpotEditorModal.vue:63`, `webapp/src/components/settings/SettingsForm.vue:104`

### Gaps and required code changes

1. Extract `useOwnerProfiles` composable and reuse in map/home/profile components.
2. Extract `readFileAsBase64` utility into `webapp/src/utils/fileBase64.js`.
3. Split large `MapWorkspace.vue` orchestration into composables (`useMapFilters`, `useMapSubscriptions`, `useMapSelection`).

## B) Architecture / Structure

### Target state

- Strict backend layering: Router -> Service -> Repository -> DB.
- Frontend UI components orchestrate via props/actions, not domain-heavy logic.

### Current state

- Frontend layering is mostly consistent.
  - Evidence: `webapp/src/bootstrap/appBootstrap.js:64`, `webapp/src/controllers/baseController.js:1`, `webapp/src/services/baseService.js:17`
- Backend has repository abstraction but auth/social routes bypass it.
  - Evidence: `backend/data/mongo_repository.py:9`, `backend/routing/auth_routes.py:465`, `backend/routing/auth_routes.py:612`, `backend/routing/auth_routes.py:997`

### Gaps and required code changes

1. Create backend service modules (`auth_service.py`, `social_service.py`).
2. Create domain repositories (`users_repository.py`, `spots_repository.py`, `social_repository.py`, `support_repository.py`).
3. Refactor `auth_routes.py` to route boundary only.

## C) Frontend ↔ Backend Communication

### Target state

- Unified error envelope.
- Consistent status code semantics.
- Timeout/abort and selective retry policy.

### Current state

- Frontend has centralized `ApiClient` and error parser.
  - Evidence: `webapp/src/services/apiClient.js:3`, `webapp/src/services/apiErrors.js:103`
- Backend error responses are inconsistent:
  - traceback object in generic CRUD router
  - string detail in auth/social endpoints
  - Evidence: `backend/routing/router.py:62`, `backend/routing/auth_routes.py:450`
- Client has no timeout/retry control.
  - Evidence: `webapp/src/services/apiClient.js:39`

### Gaps and required code changes

1. Add global error handlers returning one error schema.
2. Remove traceback payload exposure from API responses.
3. Add timeout + retry for idempotent GET calls in ApiClient.

## D) Data Persistence

### Target state

- Repository-only DB access.
- Explicit index policy and UTC timestamp consistency.

### Current state

- Index creation is implemented and explicit.
  - Evidence: `backend/routing/auth_routes.py:53`, `backend/routing/auth_routes.py:67`
- Timestamp handling is inconsistent between modules.
  - naive `datetime.now()` in DTO layer
  - UTC-aware timestamps in auth/social routes
  - Evidence: `backend/data/dto.py:28`, `backend/routing/auth_routes.py:370`

### Gaps and required code changes

1. Standardize all timestamps to `datetime.now(UTC)`.
2. Move auth/social persistence operations behind repository classes.
3. Add DB bootstrap/seed scripts for reproducible local setup.

## E) Version Control

### Target state

- Atomic commits with conventional prefixes.
- No generated/secrets tracked.

### Current state

- Commits are mostly atomic and meaningful.
  - Evidence: `f128b45`, `6184b07`, `5831b52`, `ca07f5e`, `73610a4`
- Prefixes (`feat:`, `fix:`, `docs:`...) are not consistently used historically.
  - Evidence: commit messages above
- Runtime cache outputs are ignored.
  - Evidence: `.gitignore:6`, `.gitignore:7`, `.gitignore:9`

### Gaps and required code changes

1. Enforce conventional commit style going forward.
2. Add changelog/release tagging policy.

## F) Testing

### Target state

- Mapped test concept + executed protocol + automated smoke suite.

### Current state

- No backend/frontend test directories found in baseline.
- No `test` script in webapp package scripts.
  - Evidence: `webapp/package.json:6`

### Gaps and required code changes

1. Add backend smoke tests (`pytest` + `httpx`).
2. Add frontend smoke tests (`playwright` and/or `vitest`).
3. Add CI execution and protocol recording.

## G) Deliverable Readiness

### Target state

- Setup/run/troubleshooting docs + release checklist + known limitations.

### Current state

- Setup/run docs exist in root and webapp readmes.
  - Evidence: `README.md:17`, `README.md:67`, `webapp/README.md:18`
- Release checklist and structured protocol artifacts were missing in baseline.

### Gaps and required code changes

1. Add release checklist.
2. Add test concept/protocol docs.
3. Add explicit architecture/API/persistence docs.

## H) Bonus (Documentation / Error Handling / Observability)

### Target state

- ADR-backed decisions, robust error design, and meaningful operational logs.

### Current state

- Frontend notification stack provides meaningful user feedback with expandable details.
  - Evidence: `webapp/src/components/common/NotificationStack.vue:135`
- Backend lacks documented structured logging policy and still exposes traceback details in one route path.
  - Evidence: `backend/routing/router.py:65`

### Gaps and required code changes

1. Add backend logging strategy (`logging` + request ID middleware).
2. Add unified, sanitized error envelope.
3. Capture critical operation failures with trace IDs.

---

## 4) Minimal Implementation Plan to Reach Maximum Points

1. **Docs package (this commit line):** architecture/API/persistence/ADRs/test/release checklist.
2. **DRY refactor:** extract duplicated owner-loader and file-base64 helpers.
3. **Backend layering:** split auth/social route logic into service/repository modules.
4. **Contract hardening:** implement unified error envelope + ApiClient timeout/retry.
5. **Testing:** add backend + frontend smoke tests and fill protocol evidence.

---

## 5) Assumptions and Missing Evidence Register

- Explicit written rationale for GUI-to-web pivot is not present in commit text/docs.
- Therefore, the pivot motivation in this report is marked as inference based on commit sequence and activity concentration.
