# SpotOnSight

SpotOnSight is a multi-client project for discovering and sharing map spots.

This repository contains:

- `backend/`: FastAPI + MongoDB API (auth, social features, spots)
- `app/`: Kivy desktop/mobile-style client
- `webapp/`: Vue 3 + Vite web client

## Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB 7+ (or Docker)

## 1) Start the backend

### Option A: Docker (quickest)

```bash
cd backend
docker compose up --build
```

Backend runs on `http://127.0.0.1:8000`.

### Option B: Local Python

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Default Mongo connection is `mongodb://localhost:27017`.

You can override backend env vars:

- `MONGO_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`

## 2) Run the Kivy app

```bash
cd app
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

The app reads backend config from `app_config.json` in repository root.

## 3) Run the web app

```bash
cd webapp
npm install
npm run dev
```

Web app defaults to `http://127.0.0.1:8000`.

Optional `webapp/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPPORT_EMAIL=support@spotonsight.app
```

Production build:

```bash
npm run build
```

## Runtime files

- Session cache: `cache/session.json`
- Client crash reports: `cache/client_error_reports.jsonl`
- Map tile cache: `.tile_cache/`

These files are generated at runtime and ignored by git.

## Typical local workflow

1. Start backend (`backend/`)
2. Run either `app/` or `webapp/` client
3. Login/register and test spots/social flows
