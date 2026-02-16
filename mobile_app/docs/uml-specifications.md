# UML Specifications (draw.io-ready)

## Diagram 1: Class Diagram - Frontend Composition

## Title

`SpotOnSight Webapp - UI/Controller/Service Composition`

## Classes / Components (exact names)

- `AppContext` (`webapp/src/core/context.js`)
- `UIController` (`webapp/src/core/uiController.js`)
- `AuthController` (`webapp/src/controllers/authController.js`)
- `SpotsController` (`webapp/src/controllers/spotsController.js`)
- `SocialController` (`webapp/src/controllers/socialController.js`)
- `UsersController` (`webapp/src/controllers/usersController.js`)
- `SupportController` (`webapp/src/controllers/supportController.js`)
- `AuthService` (`webapp/src/services/authService.js`)
- `SpotsService` (`webapp/src/services/spotsService.js`)
- `SocialService` (`webapp/src/services/socialService.js`)
- `UsersService` (`webapp/src/services/usersService.js`)
- `SupportService` (`webapp/src/services/supportService.js`)
- `ApiClient` (`webapp/src/services/apiClient.js`)
- `NotificationService` (`webapp/src/services/notificationService.js`)
- `ActivityWatchService` (`webapp/src/services/activityWatchService.js`)

## Relationships to Draw

- `AppContext` composes service instances (`1 -> *`).
- `AppContext` composes controller instances (`1 -> *`).
- Each `*Controller` depends on one corresponding `*Service` via context lookup.
- `AuthService`, `SpotsService`, `SocialService`, `UsersService`, `SupportService` depend on `ApiClient`.
- `UIController` depends on registry action/component queries.
- `ActivityWatchService` depends on app context and uses social/spots controllers + notification service.

## Suggested Class Box Methods

- `AppContext.service(id)`, `AppContext.controller(id)`
- `UIController.runAction(actionId, payload)`
- `SpotsController.saveSpot()`
- `SocialController.follow()`
- `UsersController.updateProfile()`
- `ApiClient.request(method, path, opts)`
- `NotificationService.push()/remove()/clearLog()`

## Evidence

- Service/controller graph wiring: `webapp/src/bootstrap/appBootstrap.js:64`, `webapp/src/bootstrap/appBootstrap.js:78`
- Context resolution: `webapp/src/core/context.js:11`, `webapp/src/core/context.js:24`
- UI dispatch: `webapp/src/core/uiController.js:20`

---

## Diagram 2: Sequence Diagram - Create Spot Flow

## Title

`Create Spot from Web UI to MongoDB`

## Participants (left -> right)

1. `User`
2. `SpotEditorModal` (`webapp/src/components/map/SpotEditorModal.vue`)
3. `MapWorkspace` (`webapp/src/components/map/MapWorkspace.vue`)
4. `mapUi registration` (`webapp/src/registrations/mapUi.js`)
5. `SpotsController` (`webapp/src/controllers/spotsController.js`)
6. `SpotsService` (`webapp/src/services/spotsService.js`)
7. `ApiClient` (`webapp/src/services/apiClient.js`)
8. `FastAPI social_router.create_spot` (`backend/routing/auth_routes.py`)
9. `MongoDB spots collection`

## Messages

1. `User -> SpotEditorModal`: click Save.
2. `SpotEditorModal -> MapWorkspace`: emit `onSubmit(payload)`.
3. `MapWorkspace -> mapUi`: invoke `onSaveSpot(spot)` callback.
4. `mapUi -> SpotsController`: call `saveSpot(spot)`.
5. `SpotsController -> SpotsService`: call `create(dto)` (or `update` for existing id).
6. `SpotsService -> ApiClient`: `POST /social/spots`.
7. `ApiClient -> FastAPI`: HTTP call with bearer token.
8. `FastAPI -> MongoDB`: validate `SpotUpsertRequest`, insert document.
9. `FastAPI -> ApiClient`: return `SpotPublic` payload.
10. `ApiClient -> SpotsService -> SpotsController -> mapUi -> MapWorkspace`: success propagation.
11. `mapUi -> NotificationService`: push success message.

## Notes

- Spot payload validation constraints are in `SpotUpsertRequest`.
  - Evidence: `backend/routing/auth_routes.py:111`
- Authorization is enforced via `get_current_user` dependency.
  - Evidence: `backend/routing/auth_routes.py:378`, `backend/routing/auth_routes.py:607`

## Evidence

- Modal submit callback: `webapp/src/components/map/SpotEditorModal.vue:151`
- Registration callback: `webapp/src/registrations/mapUi.js:63`
- Controller dispatch: `webapp/src/controllers/spotsController.js:12`
- Service API call: `webapp/src/services/spotsService.js:24`
- Backend insert route: `backend/routing/auth_routes.py:607`, `backend/routing/auth_routes.py:612`
