# SpotOnSight Web App (Vue 3 + Vite)

This is the active SpotOnSight client.

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

## Environment Variables

Create `.env` in `webapp/` if needed:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPPORT_EMAIL=support@spotonsight.app
```

## Architecture Pointers

- App bootstrap: `src/bootstrap/appBootstrap.js`
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

Planned automation:

- Backend smoke tests with `pytest` + `httpx`
- Frontend smoke/e2e with `playwright`
- Optional frontend unit tests with `vitest`

## Related Docs

- `../ARCHITECTURE.md`
- `../API_SPEC.md`
- `../PERSISTENCE.md`
- `../docs/m335-max-points-assessment.md`
