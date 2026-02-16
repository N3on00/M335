# Persistence Report (MongoDB)

## 1) Entities and Collections

## Active collections referenced by auth/social routes

- `users`
- `favorites`
- `follows`
- `shares`
- `follow_requests`
- `blocks`
- `support_tickets`
- `spots`

Evidence: `backend/routing/auth_routes.py:43`, `backend/routing/auth_routes.py:51`

## Decorator-based generic entities

- `Spot` (`/spots` generic CRUD)
- `ClientErrorReport` (`/client-errors` generic CRUD)

Evidence: `backend/data/dto.py:11`, `backend/data/dto.py:31`

## 2) Index List and Purpose

Indexes created in `_ensure_indexes()`:

- `users.username` unique
- `users.email` unique
- `users.display_name`
- `favorites(user_id, spot_id)` unique
- `follows(follower_id, followee_id)` unique
- `shares(user_id, spot_id, created_at)`
- `follow_requests(follower_id, followee_id)` unique
- `blocks(blocker_id, blocked_id)` unique
- `support_tickets(user_id, created_at)`
- `support_tickets(status, created_at)`
- `spots.owner_id`
- `spots.visibility`
- `spots.invite_user_ids`

Evidence: `backend/routing/auth_routes.py:53`, `backend/routing/auth_routes.py:67`

## 3) Repository Pattern Rules and Current Violations

## Rule (target)

- All Mongo access must go through repository classes.
- Routers only call services; services call repositories.

## Existing base repository

- `MongoRepository` exists and provides generic CRUD.
  - Evidence: `backend/data/mongo_repository.py:9`

## Current violations

- Auth/social endpoints perform direct collection writes/reads in route file.
  - user creation: `backend/routing/auth_routes.py:465`
  - spot insert: `backend/routing/auth_routes.py:612`
  - support insert: `backend/routing/auth_routes.py:997`

## Required remediation

1. Add domain repositories (`UsersRepository`, `SpotsRepository`, `SocialRepository`, `SupportRepository`).
2. Add service layer modules and move business logic from routes.
3. Keep routes as request/response boundaries only.

## 4) Timestamp and Timezone Policy

## Current inconsistency

- `datetime.now()` (naive) used in DTO validator.
  - Evidence: `backend/data/dto.py:28`
- `datetime.now(UTC)` used in auth/social route logic.
  - Evidence: `backend/routing/auth_routes.py:370`, `backend/routing/auth_routes.py:461`

## Policy (target)

- Persist all timestamps as UTC-aware datetimes.
- Use field naming consistently:
  - `created_at` mandatory for persisted entities.
  - `updated_at` mandatory for mutable entities.
- API boundary serializes to ISO-8601 UTC.

## 5) Identifier Consistency

- MongoDB internal `_id` remains storage primary key.
- API responses expose string `id` via serializer helper.

Evidence: `backend/routing/auth_routes.py:173`, `backend/routing/auth_routes.py:295`

## 6) Configuration Consistency Risk

- Database defaults are inconsistent across modules:
  - social/auth DB default: `witterungsstation`
  - spots DB default: `spot_on_sight`
  - generic repository default: `spot_on_sight`

Evidence: `backend/routing/auth_routes.py:25`, `backend/routing/auth_routes.py:29`, `backend/data/mongo_repository.py:16`

## Required remediation

- Standardize DB naming policy and expose explicit environment variable documentation.

## 7) Migration and Seed Approach

## Current

- No migration framework is tracked in repository.
- Index bootstrap happens at startup via `_ensure_indexes()`.

Evidence: `backend/routing/auth_routes.py:437`

## Recommended minimal approach

1. Add `backend/scripts/bootstrap_indexes.py` (idempotent index sync).
2. Add `backend/scripts/seed_dev_data.py` (local demo dataset).
3. Add `docs/db-ops.md` with safe operational procedures.
