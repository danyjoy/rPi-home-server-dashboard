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

## Deploy on the Raspberry Pi (prebuilt images, no cloning)

A GitHub Actions workflow builds multi-arch images (arm64 + amd64) on every push
to `main` and publishes them to the GitHub Container Registry (GHCR):

- `ghcr.io/danyjoy/rip-home-server-dashboard-backend`
- `ghcr.io/danyjoy/rip-home-server-dashboard-frontend`

On the Pi you only need Docker, the `docker-compose.prod.yml` file, and your
`.env`. No repository clone or local build:

```bash
# One-time: make the GHCR packages public (Package settings on GitHub), OR
# log in with a token that has read:packages:
#   echo <TOKEN> | docker login ghcr.io -u danyjoy --password-stdin

# Fetch just the deploy compose file and env template:
curl -O https://raw.githubusercontent.com/danyjoy/rip-home-server-dashboard/main/docker-compose.prod.yml
curl -o .env https://raw.githubusercontent.com/danyjoy/rip-home-server-dashboard/main/.env.example

# Pull and run the prebuilt images:
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Open `http://<pi-ip>:9180`. To update later, re-pull and bring it up again:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Pin a specific build instead of `latest` by setting `TAG` (e.g. a short commit
SHA or a `v1.0.0` git tag) in `.env`.

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
