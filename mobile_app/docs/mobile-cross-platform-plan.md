# Cross-Platform Mobile Integration Plan (Android + iOS)

## Goal

Ship the existing Vue client as native mobile apps without splitting feature logic per platform.

## Why This Direction

- The project initially started with a Python GUI (`app/`) because that was the fastest known path to a cross-platform prototype at the time.
- After gaining more experience with Vue and hybrid mobile tooling, the strategy shifted to a single web frontend (`webapp/`) packaged to Android/iOS via Capacitor.
- This reduced parallel-client maintenance and allowed one UI/service architecture across browser + mobile shells.

## Phase Status

1. **Foundation (Capacitor shell) - Implemented**
   - Added Capacitor config and dependencies in `webapp/`.
   - Added Android and iOS native shell projects (`webapp/android/`, `webapp/ios/`).
   - Added build/sync scripts in `webapp/package.json`.

2. **Mobile UX adaptation - Implemented (baseline)**
   - Added safe-area aware layout and viewport-fit support.
   - Kept map filter widget collapsed by default on map entry while remaining expandable.

3. **Native bridge abstraction - Implemented**
   - Added `PlatformService` and `capacitorBridge` adapter layer.
   - Added native lifecycle hooks and keyboard/status-bar integration points.

4. **Session/storage hardening - Implemented (baseline)**
   - Added native preference persistence/hydration for session, theme, and map filter subscriptions.
   - Kept local web persistence path for browser runtime.

5. **CI integration - Implemented**
   - Extended `.github/workflows/ci.yml` with Android/iOS shell sync jobs.
   - Added mobile-focused tests and dedicated `npm run test:mobile` command.
   - Added native-shell contract tests for Android manifest/package and iOS plist/app identity.

6. **Release rollout lanes - In progress**
   - Remaining: add signed Android release lane (AAB/APK) and iOS archive/TestFlight lane with CI secrets.

## Current Verification Commands

From `webapp/`:

```bash
npm run test:mobile
npm run test:run
npm run build
npm run mobile:add:android  # first time only
npm run mobile:add:ios      # first time only
npm run mobile:sync:android
npm run mobile:sync:ios
```

From repo root:

```bash
python -m pytest backend/tests -q
```
