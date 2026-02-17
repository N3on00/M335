# UML Specifications

This repository provides two Draw.io UML-style architecture diagrams for the current implementation baseline.

## Diagram Files

1. `docs/backend-architecture.drawio`
   - Focuses on FastAPI bootstrap, decorator-based router registration, auth session routing, authenticated generic CRUD routing, repositories, and MongoDB targets.
   - Includes two execution examples: login flow and authenticated spot creation flow.

2. `docs/frontend-architecture.drawio`
   - Focuses on Vue router -> registered screen composition -> UI registry/controller -> controller/service/api-gateway stack -> backend API.
   - Includes automated test layer coverage for the new generic page harness and existing contract/resilience suites.

## How to Open

- Go to `https://app.diagrams.net/`.
- Select **Device**.
- Open the `.drawio` files from `docs/`.

## Mapping to Project Artifacts

- Backend runtime references:
  - `backend/main.py`
  - `backend/routing/routing.py`
  - `backend/routing/registry.py`
  - `backend/routing/router.py`
  - `backend/routing/auth_routes.py`
  - `backend/data/dto.py`
  - `backend/data/mongo_repository.py`

- Frontend runtime references:
  - `webapp/src/main.js`
  - `webapp/src/bootstrap/appBootstrap.js`
  - `webapp/src/router/index.js`
  - `webapp/src/router/registry.js`
  - `webapp/src/views/RegisteredScreenView.vue`
  - `webapp/src/core/screenRegistry.js`
  - `webapp/src/core/registry.js`
  - `webapp/src/services/apiGatewayService.js`
  - `webapp/src/api/registry.js`

- Frontend testing references:
  - `webapp/src/tests/harness/pageRegistryHarness.js`
  - `webapp/src/tests/pageRegistryHarness.spec.js`
  - `webapp/src/tests/apiGatewayEndpoints.spec.js`
  - `webapp/src/tests/serviceApiCommunication.spec.js`
  - `webapp/src/tests/authAndStateResilience.spec.js`
  - `webapp/src/tests/activityWatchSubscriptions.spec.js`
