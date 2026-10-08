# Development Guide

This covers running the project from source and how it's organized. If you only
want to *use* the dashboard on your Pi, see the main [README](../README.md) — you
don't need any of this.

## Project layout

```
backend/            FastAPI + psutil service (reads system/storage metrics)
  app/
    main.py         app setup, health endpoint, router registration
    config.py       environment-driven settings
    routers/        one module per endpoint (system, storage)
    services/       metric collection (psutil, /proc, /sys reads)
    models/         Pydantic response models (the API contract)
frontend/           React + TypeScript + Vite + Tailwind web app
  src/
    api/            typed client + types mirroring the backend models
    hooks/          React Query polling hooks
    components/     reusable UI (cards, badges, bars)
    pages/          the Dashboard page
    lib/            formatting + healthy/warning/critical thresholds
docker-compose.yml       build-from-source stack (local dev / Pi)
docker-compose.prod.yml  run prebuilt images from GHCR (deploy)
.kiro/                    specs (requirements/design/tasks) and steering rules
```

## Run everything with Docker (build from source)

From the project root:
```bash
cp .env.example .env
docker compose up --build
```
Open `http://localhost:9180`. Stop with `docker compose down`.

This builds the images locally instead of pulling them, so it reflects your code
changes.

## Run without Docker

Useful for fast iteration. You'll run the backend and frontend in two terminals.

**Backend** (Python 3.12+):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Node 20+):
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. The Vite dev server proxies `/api` calls to the
backend on port 8000, so the two talk to each other automatically.

## The API

All endpoints are under `/api` and return JSON. Sizes are in bytes, percentages
are 0–100, temperatures in °C. Fields that a machine can't provide (CPU
temperature, Raspberry Pi model) come back as `null`.

- `GET /api/health` → `{ "status": "ok" }`
- `GET /api/system` → CPU (overall + per-core), memory, temperature, uptime,
  load average, and host info (model, OS, hostname)
- `GET /api/storage` → one entry per configured filesystem with total/used/free
  bytes and used percent

The authoritative contract lives in `.kiro/steering/api-contract.md`. The
frontend's TypeScript types in `frontend/src/api/client.ts` mirror the backend's
Pydantic models — keep them in sync when you change either side.

## Build and release (CI)

Two GitHub Actions workflows handle images and releases:

- `.github/workflows/build-images.yml` — on every push to `main` and on `v*`
  tags, builds the backend and frontend for **arm64 + amd64** and pushes them to
  GHCR (`ghcr.io/danyjoy/rpi-home-server-dashboard-{backend,frontend}`).
- `.github/workflows/release.yml` — on a `v*` tag, creates a GitHub Release with
  generated notes.

To cut a release:
```bash
git tag v1.1.0
git push origin v1.1.0
```
This produces versioned images (`v1.1.0`, `1.1.0`, `1.1`) and a matching Release.

## Conventions

- Backend: snake_case modules, PascalCase Pydantic models. Routers stay thin and
  delegate to services; services own all system access.
- Frontend: PascalCase components, `use*` hooks, shared thresholds in
  `lib/thresholds.ts`.
- Keep Phase boundaries: don't add future-phase features (Jellyfin, controls,
  etc.) into Phase 1. See `.kiro/steering/product.md`.
