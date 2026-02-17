# Test Protocol (Executed)

## Metadata

- Date: 2026-02-17
- Tester: OpenCode (CLI execution)
- Scope: frontend + backend regression validation and Capacitor mobile-shell integration checks
- Commit under test: working tree (pre-release commit)

## Executed Commands and Results

- `python -m pytest backend/tests -q`
  - Result: `15 passed in 4.64s`

- `npm run test:run` (inside `webapp/`)
  - Result: `18 test files passed, 102 tests passed`

- `npm run test:mobile` (inside `webapp/`)
  - Result: `4 test files passed, 10 tests passed`

- `npm run build` (inside `webapp/`)
  - Result: success, production bundle generated
  - Main JS artifact: `webapp/dist/assets/index-YswEats2.js`

- `npm run mobile:doctor` (inside `webapp/`)
  - Result: Capacitor CLI/core/android/ios all installed on `8.1.0`

- `npm run mobile:add:android` and `npm run mobile:add:ios` (inside `webapp/`)
  - Result: Android and iOS native shell projects created successfully

- `npm run mobile:sync:android` and `npm run mobile:sync:ios` (inside `webapp/`)
  - Result: web assets and plugin bindings synced successfully

## Validation Summary

- [x] Backend route inventory smoke tests pass
- [x] Backend OpenAPI endpoint reachable
- [x] Protected backend routes correctly enforce authentication (`401`)
- [x] Frontend contract/resilience tests pass
- [x] New generic page registry harness tests pass
- [x] Frontend production build succeeds
- [x] Mobile integration unit/config tests pass
- [x] Capacitor Android shell creation + sync succeeds
- [x] Capacitor iOS shell creation + sync succeeds

## Test Matrix

| Test ID | Result | Evidence | Notes |
|---|---|---|---|
| BE-SMOKE-01 | PASS | `backend/tests/test_api_routes_smoke.py` | Route inventory, OpenAPI reachability, and unauthorized status checks validated. |
| FE-CONTRACT-01 | PASS | `webapp/src/tests/apiGatewayEndpoints.spec.js` | API endpoint registry and method/path binding coverage validated. |
| FE-CONTRACT-02 | PASS | `webapp/src/tests/serviceApiCommunication.spec.js` | Service-to-API communication and endpoint mapping validated. |
| FE-RESILIENCE-01 | PASS | `webapp/src/tests/authAndStateResilience.spec.js` | Session restore, unauthorized handling, and fallback behavior validated. |
| FE-RESILIENCE-02 | PASS | `webapp/src/tests/activityWatchSubscriptions.spec.js` | User-scoped subscription delta/notification behavior validated. |
| FE-REGISTRY-01 | PASS | `webapp/src/tests/pageRegistryHarness.spec.js` | Per-page registry contracts (components, actions, lifecycle) validated. |
| FE-REGISTRY-02 | PASS | `webapp/src/tests/harness/pageRegistryHarness.js` | Generic inherited page harness classes used with mock data across all registered screens. |
| FE-MOBILE-01 | PASS | `webapp/src/tests/platformService.spec.js` | Native lifecycle/persistence adapter behavior validated via mocked Capacitor bridge. |
| FE-MOBILE-02 | PASS | `webapp/src/tests/capacitorConfig.spec.js` | Capacitor app identity and plugin-config contract validated. |
| FE-MOBILE-03 | PASS | `webapp/src/tests/mapFilterSummary.spec.js` | Collapsed map-filter summary behavior validated for mobile-first map UX. |
| FE-MOBILE-04 | PASS | `webapp/src/tests/mobileNativeShell.spec.js` | Android/iOS native shell contract files validated (manifest/plist/package). |
| FE-SHARE-01 | PASS | `webapp/src/tests/spotSharePayload.spec.js` | Spot-share payload and deep-link generation validated. |
| FE-BUILD-01 | PASS | `webapp/dist/assets/index-YswEats2.js` | Production build completed successfully. |
| FE-BUILD-02 | PASS | `webapp/android/` + `webapp/ios/` | Capacitor native shell projects added and synchronized from `dist/`. |

## Defect Register

- No new defects introduced during this final validation run.

## Sign-Off

- QA/Test responsible: OpenCode
- Release recommendation: Go (for currently validated shell-integration scope)
- Known risk kept explicit: native release signing/distribution lanes (AAB/IPA publishing) still require environment-specific credential hardening in CI secrets.
