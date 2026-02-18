# SpotOnSight

SpotOnSight is a map-based platform for discovering, saving, and sharing spots with social features.

## Repository Structure

- `backend/` - FastAPI + MongoDB API
- `webapp/` - Vue 3 + Vite frontend (**active client**)
- `app/` - historical Python GUI prototype (kept for project evolution traceability)

## Evolution and Rationale

The repository contains both `app/` and `webapp/` because the project evolved in two phases:

1. I started with a Python GUI approach to get a cross-platform client running quickly while my web/mobile stack knowledge was still limited.
2. After learning Vue.js and modern hybrid-mobile packaging, I realized I could ship one frontend (`webapp/`) to browser + Android + iOS using a wrapper framework (Capacitor), so active development moved there.
3. The Python GUI was then frozen as historical evidence, while all feature hardening continued in `webapp/`.

Evidence anchors:

- Python GUI start: commit `31f78df "mobile app starts"`
- Web client introduction: commit `253bb95 "add Vue web client with auth, map, social, profile, and support flows"`
- Last `app/` change: commit `c382497`
- Current webapp iteration: commits through `73610a4`

## Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB 7+ (or Docker)
- Android Studio (for APK/AAB generation)
- Xcode + CocoaPods on macOS (for iOS IPA/TestFlight)

## 1) Start Backend

### Option A: Docker

```bash
cd backend
docker compose up --build
```

### Option B: Local Python

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Default backend URL: `http://127.0.0.1:8000`

Main backend environment variables:

- `MONGO_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `CORS_ORIGINS` (comma-separated, e.g. `https://app.example.com,https://admin.example.com`)

## 2) Start Web App (Active Client)

```bash
cd webapp
npm install
npm run dev
```

Production build:

```bash
npm run build
```

## 2b) Build Native Mobile Shells (Capacitor)

Inside `webapp/`:

```bash
# one-time sanity check
npm run mobile:doctor

# Android
# first time only
npm run mobile:add:android

# recurring sync/build prep
npm run mobile:build:android

# iOS (macOS only)
# first time only
npm run mobile:add:ios

# recurring sync/build prep
npm run mobile:build:ios
```

Notes:

- Android release deliverables: APK (internal/sideload) and AAB (Play Store).
- iOS release deliverable: IPA (TestFlight/App Store via Xcode signing).

Optional `webapp/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPPORT_EMAIL=support@spotonsight.app
```

## 3) Python GUI Prototype (Historical)

The `app/` client is retained for history and comparison, but current deliverable hardening targets the web stack.

If needed for local historical run:

```bash
cd app
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Testing

Executed test artifacts:

- Test concept: `docs/test-concept.md`
- Executed test protocol: `docs/test-protocol.md`

Automation commands:

- Backend smoke tests: `python -m pytest backend/tests -q`
- Frontend contract/resilience tests: `cd webapp && npm run test:run`
- Frontend mobile integration tests: `cd webapp && npm run test:mobile`
- Frontend production build validation: `cd webapp && npm run build`

CI workflow:

- `.github/workflows/ci.yml` runs backend smoke tests + frontend tests/build on push and pull requests.

## Documentation Index

- Architecture: `ARCHITECTURE.md`
- Product concept: `concept.md`
- API contract: `API_SPEC.md`
- Persistence report: `PERSISTENCE.md`
- M335 gap and hardening report: `docs/m335-max-points-assessment.md`
- ADRs: `docs/adr/`
- UML specifications: `docs/uml-specifications.md`
- Release checklist: `docs/release-checklist.md`
- Mobile cross-platform plan: `docs/mobile-cross-platform-plan.md`
- Reflection: `docs/reflection.md`

## Troubleshooting

- Login fails:
  - verify backend is running and reachable
  - verify `JWT_SECRET` and token expiry settings
- Empty map/social data:
  - verify MongoDB availability and user data existence
- Build issues:
  - clean install in `webapp/` (`npm install` again after removing `node_modules`)
- CORS/auth issues:
  - verify backend CORS and token validity

## Runtime Files

- Session cache: `cache/session.json`
- Client crash reports: `cache/client_error_reports.jsonl`
- Map tile cache: `.tile_cache/`

These files are generated at runtime and ignored by git.
