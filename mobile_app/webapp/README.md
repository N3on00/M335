# SpotOnSight Web App (Vue 3 + Vite)

This is the active SpotOnSight client.

Project-evolution context:

- The earlier Python GUI (`../app/`) was the first cross-platform attempt.
- After the frontend architecture matured, active development moved to this Vue app and now targets Android/iOS via Capacitor.
- The Python GUI remains as historical traceability only.

## Feature Scope

- Auth-first flow (register/login/help)
- Spot CRUD with image support
- Favorites and map filter subscriptions
- Social follow/request/block interactions
- Profile and settings management
- Support ticket submission
- Notification stack and activity watch

## Runtime Stack

- Vue 3 + Vue Router
- Vite
- Bootstrap / Bootswatch / Bootstrap Icons
- Leaflet
- AOS transitions

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Mobile Builds (Android + iOS)

The web client is wrapped with Capacitor for native mobile packaging.

Initialize/check mobile tooling:

```bash
npm run mobile:doctor
```

Android shell sync/build prep:

```bash
# first time only
npm run mobile:add:android

# recurring sync/build prep
npm run mobile:build:android
```

iOS shell sync/build prep (macOS/Xcode required):

```bash
# first time only
npm run mobile:add:ios

# recurring sync/build prep
npm run mobile:build:ios
```

The native projects consume the `dist/` output from `npm run build:mobile:web`.

## Environment Variables

Create `.env` in `webapp/` if needed:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPPORT_EMAIL=support@spotonsight.app
```

## Architecture Pointers

- App bootstrap: `src/bootstrap/appBootstrap.js`
- UI declarations (screens/slots/actions/layouts): `src/core/uiElements.js`
- Route declarations + bindings: `src/router/routeSpec.js`, `src/router/registry.js`
- API endpoint declarations + generic gateway: `src/api/registry.js`, `src/services/apiGatewayService.js`, `src/controllers/apiController.js`
- UI registry: `src/core/registry.js`
- Views: `src/views/`
- Registrations: `src/registrations/`
- Controllers: `src/controllers/`
- Services: `src/services/`
- Models/mappers: `src/models/`

## Testing and QA Docs

- Root test concept: `../docs/test-concept.md`
- Root test protocol: `../docs/test-protocol.md`
- Release checklist: `../docs/release-checklist.md`
- Mobile integration plan: `../docs/mobile-cross-platform-plan.md`

Implemented automation:

- Frontend contract/resilience tests: `npm run test:run`
- Frontend mobile-integration tests: `npm run test:mobile`
- Frontend development test runner: `npm run test`
- Backend smoke tests from repo root: `python -m pytest backend/tests -q`

## Related Docs

- `../ARCHITECTURE.md`
- `../API_SPEC.md`
- `../PERSISTENCE.md`
- `../docs/m335-max-points-assessment.md`
