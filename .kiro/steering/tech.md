---
inclusion: always
---

# Technology Stack & Technical Rules

The stack is fixed. Do not introduce alternatives without a strong, stated
technical reason and explicit approval.

## Frontend

- React + TypeScript
- Vite (build + dev server)
- Tailwind CSS (dark mode is the default/preferred theme)
- React Query (TanStack Query) for data fetching and polling
- Recharts (or another lightweight charting library) ONLY when charts are
  actually required — not in Phase 1

## Backend

- Python 3.12+
- FastAPI + uvicorn
- psutil for host system metrics
- pydantic / pydantic-settings for models and configuration

## Deployment

- Docker + Docker Compose
- All images must support the Pi's architecture (linux/arm64, or arm/v7 for
  32-bit OS). Prefer multi-arch base images: python:slim, node:alpine,
  nginx:alpine.

## Technical Decisions

- Single ingress: the frontend container (nginx) serves static assets AND
  reverse-proxies `/api` to the backend. The backend port is NOT published to
  the LAN. This avoids CORS and keeps one entry point for future auth/Tailscale.
- Ingress port is 9180 (deliberately uncommon so it does not collide with
  Jellyfin 8096, qBittorrent 8080, or common dev ports 3000/5173/8000). The
  backend listens on 8000 internally and is reachable only inside the compose
  network.
- Dual target: the Raspberry Pi (Debian / arm64) is the primary production
  target, but the full stack must also run on macOS for local testing. Metrics
  that macOS cannot provide (CPU temperature, Pi model) return null and render
  as "unavailable" rather than erroring.
- Live data via polling: the frontend polls REST endpoints on an interval
  (~2-3s) using React Query. Do NOT add WebSockets in Phase 1.
- No database in Phase 1. No persisted metrics. State lives in memory only.
- Host metrics are read via psutil plus read-only host mounts (/proc, /sys).
  Fields that may be unavailable (CPU temperature, Pi model) are nullable and
  must degrade gracefully rather than raise.

## Lightweight-for-Pi Rules

- Keep container images small (multi-stage builds, slim/alpine bases).
- Avoid heavy dependencies and background workers unless a phase requires them.
- Prefer standard-library / psutil reads over spawning subprocesses where
  practical.

## Common Commands

- Dev (frontend): `npm run dev` inside `frontend/`
- Dev (backend): `uvicorn app.main:app --reload` inside `backend/`
- Full stack: `docker compose up --build`
- Stop: `docker compose down`
