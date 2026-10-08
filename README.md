# Home Server Command Center

A lightweight, self-hosted, mobile-first dashboard for a Raspberry Pi 4 (Debian).
**Phase 1** shows live system metrics and basic storage usage:

- CPU usage (overall + per-core), RAM usage, CPU temperature
- Uptime, load average
- Raspberry Pi model, Debian/OS version, hostname
- Storage: total / used / free / usage percent

The primary target is the Raspberry Pi, viewed from a phone on your LAN. The
stack also runs on macOS for local development (Pi-only metrics show as
"unavailable").

## Architecture

```
Browser ──HTTP:9180──▶ nginx (frontend) ──/api──▶ FastAPI (backend) ──ro──▶ host /proc,/sys,/
```

- Frontend: React + TypeScript + Vite + Tailwind, served by nginx.
- Backend: FastAPI + psutil (non-root), reads host metrics via read-only mounts.
- Single published port (9180). The backend is not exposed to the LAN.

## Quick start (Docker Compose)

```bash
cp .env.example .env        # adjust FRONTEND_PORT / STORAGE_MOUNTS if needed
docker compose up --build
```

Then open `http://<pi-ip>:9180` from your phone or `http://localhost:9180` on the
host. Stop with `docker compose down`; configuration persists via `.env`.

### Reporting a media drive

Edit `STORAGE_MOUNTS` in `.env`, e.g. `root:/,media:/mnt/media`, and ensure the
drive is reachable under the backend's read-only host-root mount.

## Local development (without Docker)

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Security

Runs as a non-root user, no privileged mode, no Docker socket exposed. Host
access is limited to read-only `/proc`, `/sys`, and root filesystem mounts.
Secrets (future phases) come from environment variables only.

## Roadmap

Phase 1 is system monitoring only. Later phases add service monitoring,
Jellyfin/qBittorrent integration, controls, charts, alerts, and secure remote
access. See `.kiro/specs/` and `.kiro/steering/` for details.
