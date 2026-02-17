# Test Concept (M335-Oriented)

## 1) Scope

This concept covers the active stack (`webapp/` + backend API).

In scope:

- Authentication (register/login/session)
- Spot CRUD + visibility + favorites
- Social follow/request/block flows
- Profile/settings updates
- Support ticket submission
- Error handling and session-expiry behavior
- Mobile shell integration (Capacitor Android/iOS)

Evidence for scope:

- Frontend routes: `webapp/src/router/index.js:17`, `webapp/src/router/index.js:22`
- API endpoints: `backend/routing/auth_routes.py:442`, `backend/routing/auth_routes.py:973`

## 2) Test Environment

- Backend: Python 3.11+, MongoDB 7+, local run or Docker compose.
  - Evidence: `README.md:13`, `README.md:15`, `README.md:23`
- Frontend: Node 20+, Vite dev/build flow.
  - Evidence: `README.md:70`, `README.md:87`, `webapp/package.json:8`
- Mobile packaging: Capacitor CLI with Android/iOS platform toolchains.
  - Evidence: `webapp/package.json:17`, `webapp/capacitor.config.json`

## 3) Acceptance Criteria

- Critical user journeys complete without uncaught runtime errors.
- API failures surface as meaningful notifications.
- Unauthorized session transition redirects to auth and keeps UI stable.
- Production build passes before release sign-off.
- Mobile shell sync/build preparation passes for Android and iOS lanes.

Unauthorized flow evidence:

- `webapp/src/services/apiClient.js:51`
- `webapp/src/main.js:49`

## 4) Manual Test Cases

| ID | Preconditions | Steps | Expected Result |
|---|---|---|---|
| AUTH-01 | Backend running, no account | Register valid user | Account created, redirected to home |
| AUTH-02 | Existing account | Login with wrong password | Error shown, session not created |
| AUTH-03 | Logged in | Reload page | Session restored on protected routes |
| AUTH-04 | Logged in, token invalid server-side | Trigger API call | Session-expired notice + auth redirect |
| MAP-01 | Logged in | Create new public spot | Spot appears in map/home list |
| MAP-02 | Existing own spot | Edit title/description | Data updated and visible after refresh |
| MAP-03 | Existing own spot | Delete spot | Spot removed and no stale list item |
| MAP-04 | Existing visible spot | Toggle favorite on/off | Favorite state persists correctly |
| MAP-05 | Active filter subscription | Subscribe, then add matching spot | Alert only for new/changed matches |
| SOCIAL-01 | Two users | A follows B (approval off) | Follow relation active |
| SOCIAL-02 | Approval required on B | A follows B | Follow request appears for B |
| SOCIAL-03 | Pending request exists | Approve request | Request resolved, follow active |
| SOCIAL-04 | Existing follow relation | Block target user | Follow/request edges removed, block added |
| PROFILE-01 | Logged in | Open profile, switch tabs | Created/favorite spot lists load |
| SETTINGS-01 | Logged in | Update display name + bio | Save succeeds and values persist |
| SETTINGS-02 | Logged in | Invalid password-change input | Submit blocked by validation rules |
| SUPPORT-01 | Logged in | Submit valid ticket | Ticket created with success response |
| ERROR-01 | Backend offline | Open page requiring load | User sees failure notice, no crash |

## 5) Defect Severity Model

- Critical: auth bypass, data loss, crash loop
- High: persistence corruption, permission errors
- Medium: inconsistent behavior or incorrect notifications
- Low: cosmetic and non-blocking UX issues

## 6) Smoke-Test Automation (Implemented)

## Backend smoke tests (pytest)

Implemented in:

- `backend/tests/test_api_routes_smoke.py`
- `backend/tests/test_social_route_helpers.py`

Coverage:

- Route inventory includes all defined auth/social/generic endpoints.
- OpenAPI reachability check.
- Contract/status checks for auth validation and protected endpoint unauthorized handling.
- Spot-id lookup compatibility for both ObjectId and legacy string IDs.

## Frontend contract/resilience tests (vitest)

Implemented in:

- `webapp/src/tests/apiGatewayEndpoints.spec.js`
- `webapp/src/tests/serviceApiCommunication.spec.js`
- `webapp/src/tests/authAndStateResilience.spec.js`
- `webapp/src/tests/activityWatchSubscriptions.spec.js`
- `webapp/src/tests/pageRegistryHarness.spec.js`
- `webapp/src/tests/harness/pageRegistryHarness.js`
- `webapp/src/tests/platformService.spec.js`
- `webapp/src/tests/mapFilterSummary.spec.js`
- `webapp/src/tests/capacitorConfig.spec.js`
- `webapp/src/tests/mobileNativeShell.spec.js`
- `webapp/src/tests/spotSharePayload.spec.js`

Coverage:

- Generic endpoint registry dispatch and token/path/query/body handling.
- Service-to-endpoint communication for auth/spots/social/users/support.
- Unauthorized callback, session restore, and offline fallback behavior.
- User-scoped filter subscription notification behavior.
- Generic per-page registry validation through inherited test harness classes and mock-data action/component assertions.
- Native-platform persistence/lifecycle adapter behavior (mocked Capacitor bridge).
- Collapsed map-filter summary behavior for mobile-first filter widget usage.
- Capacitor config and native shell project contracts for Android/iOS.
- Spot-share payload/deep-link generation behavior.

## Suggested test locations

- Backend: `backend/tests/`
- Frontend unit/contract: `webapp/src/tests/`
