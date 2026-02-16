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

Evidence for scope:

- Frontend routes: `webapp/src/router/index.js:17`, `webapp/src/router/index.js:22`
- API endpoints: `backend/routing/auth_routes.py:442`, `backend/routing/auth_routes.py:973`

## 2) Test Environment

- Backend: Python 3.11+, MongoDB 7+, local run or Docker compose.
  - Evidence: `README.md:13`, `README.md:15`, `README.md:23`
- Frontend: Node 20+, Vite dev/build flow.
  - Evidence: `README.md:70`, `README.md:87`, `webapp/package.json:8`

## 3) Acceptance Criteria

- Critical user journeys complete without uncaught runtime errors.
- API failures surface as meaningful notifications.
- Unauthorized session transition redirects to auth and keeps UI stable.
- Production build passes before release sign-off.

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

## 6) Minimal Smoke-Test Automation Plan

## Backend first (pytest + httpx)

Automate:

1. register/login
2. create/list/update/delete spot
3. follow request + approve flow

Reason: highest risk coverage for auth + persistence + social rules.

## Frontend second (Playwright)

Automate:

1. login -> home load
2. create spot from map workflow
3. session-expiry redirect behavior

## Suggested test locations

- Backend: `backend/tests/`
- Frontend e2e: `webapp/tests/e2e/`
- Frontend unit (optional): `webapp/tests/unit/`
