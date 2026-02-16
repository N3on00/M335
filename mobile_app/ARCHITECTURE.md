# SpotOnSight Architecture

## 1) System Context

- Client: Vue SPA (`webapp/`) for authenticated users to manage spots, social graph, profile/settings, and support requests.
  - Evidence: `webapp/src/router/index.js:17`, `webapp/src/router/index.js:22`
- API: FastAPI backend (`backend/`) exposing auth, social, support, and generic CRUD endpoints.
  - Evidence: `backend/routing/routing.py:29`, `backend/routing/routing.py:30`, `backend/routing/router.py:83`
- Database: MongoDB collections for users/social interactions/support and spots.
  - Evidence: `backend/routing/auth_routes.py:53`, `backend/routing/auth_routes.py:67`
- External integration: location search providers (Nominatim primary, Photon fallback).
  - Evidence: `webapp/src/services/locationSearchService.js:80`, `webapp/src/services/locationSearchService.js:112`

## 2) Component Overview

## Frontend Components

- `AppContext` and factory wiring build the service/controller graph.
  - Evidence: `webapp/src/core/context.js:1`, `webapp/src/bootstrap/appBootstrap.js:61`
- UI registry and slot host composition:
  - register components/actions in `registrations/*`
  - render via `SlotScreenLayout -> SlotHost -> registry`
  - Evidence: `webapp/src/core/registry.js:8`, `webapp/src/components/layouts/SlotScreenLayout.vue:14`, `webapp/src/components/core/SlotHost.vue:13`
- Controllers orchestrate state transitions; services perform API/data operations.
  - Evidence: `webapp/src/controllers/spotsController.js:8`, `webapp/src/services/spotsService.js:9`
- `ApiClient` centralizes HTTP transport and unauthorized-session callback integration.
  - Evidence: `webapp/src/services/apiClient.js:4`, `webapp/src/services/apiClient.js:51`

## Backend Components

- FastAPI app builder + middleware + router inclusion.
  - Evidence: `backend/routing/routing.py:18`, `backend/routing/routing.py:20`, `backend/routing/routing.py:27`
- Auth/social route module with DTO classes and endpoint handlers.
  - Evidence: `backend/routing/auth_routes.py:80`, `backend/routing/auth_routes.py:442`
- Generic decorator-based CRUD router registration for simple entities.
  - Evidence: `backend/routing/registry.py:31`, `backend/routing/router.py:12`, `backend/data/dto.py:11`

## 3) Layer Definitions and Responsibility Rules

## Frontend Layer Rules

- **Views (`views/*`)**
  - Route context and screen-entry orchestration only.
  - Must not call HTTP directly.
  - Evidence of current pattern: `webapp/src/views/HomeView.vue:13`, `webapp/src/views/ProfileView.vue:19`

- **Registrations (`registrations/*`)**
  - Bind screen components and action callbacks.
  - Reuse shared loading/error helpers (`uiShared`) where possible.
  - Evidence: `webapp/src/registrations/socialUi.js:4`, `webapp/src/registrations/settingsUi.js:4`

- **Controllers (`controllers/*`)**
  - Orchestrate state and delegate to services.
  - Must not implement transport or persistence details.
  - Evidence: `webapp/src/controllers/socialController.js:24`

- **Services (`services/*`)**
  - API I/O, DTO mapping, and service-local error capture.
  - Evidence: `webapp/src/services/usersService.js:46`, `webapp/src/services/baseService.js:17`

- **Models (`models/*`)**
  - Pure mapping/normalization and utility logic.
  - Evidence: `webapp/src/models/userMapper.js:6`, `webapp/src/models/spotSubscriptions.js:173`

## Backend Layer Rules (Target)

- **Router**: request parsing, auth dependency wiring, response mapping.
- **Service**: business rules and orchestration.
- **Repository**: all MongoDB access.
- **DTO/schema**: external boundary contracts.

Current violation:
- Auth/social route handlers contain direct DB access and domain logic in one file.
  - Evidence: `backend/routing/auth_routes.py:465`, `backend/routing/auth_routes.py:612`, `backend/routing/auth_routes.py:997`

## 4) Dependency Direction Rules

- Frontend direction:
  - `views -> registrations -> controllers -> services -> apiClient`
  - UI components should receive props/callbacks; no service instantiation in components.

- Backend direction (target):
  - `routers -> services -> repositories -> pymongo`
  - DTO modules can be shared inward.

## Must-Not Rules

- UI components must not call backend transport directly.
- Backend routers must not perform direct collection operations after repository refactor.
- Services must not import view components.
- Production secrets must not use hardcoded defaults.

Security baseline gap:
- Default JWT secret exists in code path and must be overridden in production.
  - Evidence: `backend/routing/auth_routes.py:75`

## 5) End-to-End Data Flow

## Login Flow

1. User submits form in `AuthForms`.
   - Evidence: `webapp/src/components/auth/AuthForms.vue:124`
2. Registration callback invokes auth controller flow.
   - Evidence: `webapp/src/registrations/authUi.js:67`
3. `AuthService.login` calls `POST /auth/login`.
   - Evidence: `webapp/src/services/authService.js:22`
4. Backend returns `AuthTokenResponse`.
   - Evidence: `backend/routing/auth_routes.py:477`, `backend/routing/auth_routes.py:167`
5. Session persistence watch stores auth state.
   - Evidence: `webapp/src/main.js:40`, `webapp/src/state/appState.js:109`

## Spot Create Flow

1. User submits spot in map modal.
   - Evidence: `webapp/src/components/map/SpotEditorModal.vue:151`
2. `mapUi` routes callback to spots controller.
   - Evidence: `webapp/src/registrations/mapUi.js:63`
3. `SpotsService.create` calls `/social/spots` with mapped payload.
   - Evidence: `webapp/src/services/spotsService.js:24`
4. Backend validates `SpotUpsertRequest` and inserts spot document.
   - Evidence: `backend/routing/auth_routes.py:607`, `backend/routing/auth_routes.py:612`

## 6) API Contract Policy

## Current Baseline

- DTO classes are explicitly defined for auth/social boundaries.
  - Evidence: `backend/routing/auth_routes.py:80`, `backend/routing/auth_routes.py:149`
- Error formats are inconsistent across backend paths.
  - Evidence: `backend/routing/router.py:62`, `backend/routing/auth_routes.py:450`

## Target Policy (Required for max-points)

- Single error envelope for all endpoints:
  - `error.code`
  - `error.message`
  - `error.details[]`
  - `error.request_id`
  - `error.timestamp_utc`
- Semantic status code contract (`400/401/403/404/409/422/5xx`).
- No traceback exposure in client payloads.

## 7) Persistence Policy

- Repository-only DB access for domain operations.
- UTC timestamps only (`datetime.now(UTC)`).
- Consistent API id serialization.

Current timestamp inconsistency:
- `datetime.now()` used in DTO model validator.
  - Evidence: `backend/data/dto.py:28`
- `datetime.now(UTC)` used in auth/social routes.
  - Evidence: `backend/routing/auth_routes.py:370`

## 8) Security and Stability Baseline

- Restrict CORS in production deployments.
- Enforce explicit secret configuration.
- Add client request timeout/retry strategy.
- Add backend structured logging + request correlation IDs.

Current gaps:
- CORS allows any origin.
  - Evidence: `backend/routing/routing.py:21`
- ApiClient has no timeout/retry.
  - Evidence: `webapp/src/services/apiClient.js:39`

## 9) Active Refactor Backlog

1. Split `backend/routing/auth_routes.py` by layer.
2. Remove duplicated owner-profile and file-base64 helpers in webapp.
3. Standardize error envelope and transport resilience.
4. Add automated smoke tests and release protocol.
