# ADR 0002: Enforce Layered Architecture and Repository-Only Persistence Access

- Status: Proposed
- Date: 2026-02-16

## Context

Frontend already follows a layered style (`view -> registration -> controller -> service -> apiClient`), but backend auth/social code combines routing, business logic, and persistence operations in one module.

Evidence:

- Frontend layering and composition:
  - `webapp/src/bootstrap/appBootstrap.js:64`
  - `webapp/src/controllers/baseController.js:7`
- Backend mixed concerns:
  - `backend/routing/auth_routes.py:445`
  - `backend/routing/auth_routes.py:612`
  - `backend/routing/auth_routes.py:973`
- Repository class exists but is bypassed by auth/social routes:
  - `backend/data/mongo_repository.py:9`

## Decision

Adopt strict backend layering:

- Router: request parsing, auth dependencies, response mapping.
- Service: business rules/orchestration.
- Repository: all MongoDB reads/writes.
- DTO/schema: boundary contracts only.

Repository-only DB access is the required policy.

## Alternatives Considered

1. Keep `auth_routes.py` monolithic.
2. Force all domains into generic CRUD generator.
3. Introduce full heavyweight DDD package structure immediately.

## Consequences

### Positive

- Better separation of concerns and testability.
- Lower duplication risk for persistence logic.
- Clearer rubric alignment for architecture criteria.

### Negative

- Requires moderate refactor across backend modules.
- Temporary increase in module count and wiring complexity.

## Implementation Notes

- Add service modules:
  - `backend/services/auth_service.py`
  - `backend/services/social_service.py`
- Add repository modules:
  - `backend/repositories/users_repository.py`
  - `backend/repositories/spots_repository.py`
  - `backend/repositories/social_repository.py`
  - `backend/repositories/support_repository.py`
- Refactor routes to call service layer only.
