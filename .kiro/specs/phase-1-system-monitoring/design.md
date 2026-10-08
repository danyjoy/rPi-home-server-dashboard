# Design — Phase 1: System Monitoring

## Overview

Two containers behind a single ingress. nginx serves the built React app and
reverse-proxies `/api` to a non-root FastAPI backend. The backend reads host
metrics with psutil plus read-only `/proc` and `/sys` reads, exposing them as a
small REST API. The frontend polls that API with React Query and renders a
mobile-first dark dashboard. No database, no WebSockets, no cloud.

```
Phone / Desktop (LAN)
      │  HTTP :9180
      ▼
┌──────────────────────────┐
│ frontend (nginx:alpine)  │  static React assets + /api reverse proxy
└───────────┬──────────────┘
            │  proxy_pass http://backend:8000
            ▼
┌──────────────────────────┐
│ backend (python:slim)    │  FastAPI + uvicorn (non-root)
│  routers → services      │  psutil + read-only /host/proc, /host/sys
└───────────┬──────────────┘
            │ read-only
            ▼
   Host /proc, /sys, root fs
```

## Architecture Decisions

- **Single nginx ingress (no CORS, one published port).** The browser only ever
  talks to nginx on port 9180; nginx proxies `/api` to `backend:8000` on the
  internal compose network. The backend is never published to the LAN. This also
  gives a single future home for auth / Tailscale.
- **Polling, not WebSockets.** React Query refetches `/api/system` and
  `/api/storage` every ~2.5s. Stateless, trivially resilient, no reconnection
  logic. The API contract is unchanged if a WS channel is added later.
- **Nullable, fail-soft metrics.** Each metric read is independent and guarded;
  a failure yields null/zero for that field, never a 500. This is what allows a
  single codebase to run on both the Pi and macOS.
- **Config via env, host paths overridable.** `HOST_PROC`, `HOST_SYS`,
  `HOST_ROOT`, and `STORAGE_MOUNTS` come from the environment. On the Pi they
  point at read-only mounts; on macOS the backend detects missing paths and uses
  native psutil reads.

## Backend Design

### Layout
```
backend/app/
├── main.py              # app factory, router registration, dev CORS, health
├── config.py            # Settings (pydantic-settings), STORAGE_MOUNTS parsing
├── routers/
│   ├── system.py        # GET /api/system -> SystemResponse
│   └── storage.py       # GET /api/storage -> StorageResponse
├── services/
│   ├── system_metrics.py   # psutil + host reads, returns SystemResponse
│   └── storage_metrics.py  # psutil disk usage, returns StorageResponse
└── models/
    ├── system.py        # CpuInfo, MemoryInfo, LoadAverage, HostInfo, SystemResponse
    └── storage.py       # FilesystemUsage, StorageResponse
```

### Metric sources
| Metric | Source | Fallback |
|---|---|---|
| CPU overall/per-core % | `psutil.cpu_percent(percpu=...)` | 0.0 |
| Memory | `psutil.virtual_memory()` | zeros |
| Uptime | now − `psutil.boot_time()` | 0 |
| Load average | `psutil.getloadavg()` | zeros (Windows/n-a) |
| CPU temperature | host `/sys/class/thermal/thermal_zone*/temp`, then `psutil.sensors_temperatures()` | null |
| Pi model | host `/proc/device-tree/model` (or `/host/proc/...`) | null |
| OS / Debian version | `/etc/os-release` PRETTY_NAME, else `platform` | platform string |
| Hostname | `socket.gethostname()` | "unknown" |
| Storage | `psutil.disk_usage(path)` for each configured mount | skip missing |

Host paths are resolved through settings: if `HOST_SYS` exists use it, else read
the native path; same for proc. On macOS none of the Linux files exist, so
temperature and model resolve to null and OS falls back to the platform string.

### Routers
Thin: call the matching service and return its typed result. No metric logic.

### CORS
Enabled only for local Vite dev (`http://localhost:5173`) so the frontend dev
server can call the backend directly. In the Docker setup, same-origin via nginx
means CORS is irrelevant.

## Frontend Design

### Layout
```
frontend/src/
├── api/client.ts        # fetch wrapper + TS types mirroring Pydantic models
├── hooks/
│   ├── useSystem.ts      # React Query poll of /api/system
│   └── useStorage.ts     # React Query poll of /api/storage
├── lib/
│   ├── format.ts         # bytes, percent, uptime, temperature formatting
│   └── thresholds.ts     # healthy/warning/critical logic (shared source)
├── components/
│   ├── MetricCard.tsx     # titled card wrapper with status accent
│   ├── StatusBadge.tsx    # healthy/warning/critical pill
│   ├── UsageBar.tsx       # labeled progress bar colored by threshold
│   ├── StatHeader.tsx     # top bar: hostname, OS, model, online state
│   └── Unavailable.tsx    # consistent "unavailable" rendering for nulls
├── pages/Dashboard.tsx    # responsive grid composing the cards
├── App.tsx, main.tsx, index.css
```

### Data flow
`useSystem`/`useStorage` use React Query with `refetchInterval` ~2500ms and keep
previous data while refetching. Query error state drives the global offline
indicator; on recovery React Query resumes automatically.

### Cards (Dashboard)
- CPU card: overall % as a UsageBar + per-core mini bars + core count.
- Memory card: used/total with UsageBar and used %.
- Temperature card: value with threshold color, or "unavailable".
- Uptime card: humanized uptime.
- Load card: 1 / 5 / 15 figures.
- System info card: Pi model (or "unavailable"), Debian/OS version, hostname.
- Storage: one UsageBar card per filesystem (used/total/free + %).

### Theming & responsiveness
Tailwind, dark by default (`<html class="dark">` + dark palette as base).
Mobile-first: single column, `sm:`/`lg:` breakpoints expand to 2–3 columns.
Thresholds come from `lib/thresholds.ts`, matching the API-contract steering
values (usage: <70 healthy, 70–89 warning, ≥90 critical; temp °C: <60 / 60–74 /
≥75).

## Docker Design

### backend/Dockerfile
`python:3.12-slim`, multi-stage (install deps, then copy app), create and run as
a non-root user, `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

### frontend/Dockerfile
Stage 1 `node:20-alpine` runs `npm ci && npm run build`. Stage 2 `nginx:alpine`
serves `/usr/share/nginx/html` and uses a custom `nginx.conf` that serves the SPA
and proxies `/api` to `backend:8000`.

### nginx.conf
- `location /api/ { proxy_pass http://backend:8000; }`
- `location / { try_files $uri /index.html; }` for SPA routing.

### docker-compose.yml
- `backend`: build `./backend`, `expose: 8000` (not published), read-only host
  mounts `/proc:/host/proc:ro`, `/sys:/host/sys:ro`, `/:/host/root:ro`,
  `restart: unless-stopped`, env `HOST_PROC/HOST_SYS/HOST_ROOT/STORAGE_MOUNTS`.
- `frontend`: build `./frontend`, `ports: ["${FRONTEND_PORT:-9180}:80"]`,
  `depends_on: backend`, `restart: unless-stopped`.
- One bridge network (compose default). The host mounts are the only privileged
  trade-off and are strictly read-only — no privileged mode, no Docker socket.

### macOS note
Mounting `/:/host/root:ro` and `/proc`, `/sys` is harmless on Docker Desktop
(the backend simply finds no Linux sensor files and returns nulls). The stack
runs unchanged; only Pi-specific fields are null.

## Error Handling

- Backend: per-metric try/except returning null/zero; endpoints always 200 with
  a valid body. uvicorn logs failures.
- Frontend: React Query `isError` → offline banner; null fields → `Unavailable`
  component. No crash paths from missing data.

## Testing Strategy

- Backend: run the API locally (uvicorn) and curl `/api/health`, `/api/system`,
  `/api/storage`; confirm valid JSON and that macOS yields null temp/model.
- Frontend: `npm run build` must succeed (type-check); visual check at mobile and
  desktop widths.
- Integration: `docker compose up --build`, open `http://<host>:9180`, confirm
  live values and that `docker compose down` / `up` restores cleanly.
