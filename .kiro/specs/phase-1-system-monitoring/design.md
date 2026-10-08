# Design — Phase 1: System Monitoring

## Overview

Two containers behind a single ingress. nginx serves the built React app and
reverse-proxies `/api` to a non-root FastAPI backend. The backend reads host
metrics with psutil plus read-only `/proc` and `/sys` reads, exposing them as a
small REST API. The frontend polls that API with React Query and renders a
mobile-first dark dashboard. No database, no WebSockets, no cloud.

## Architecture Decisions

- Single nginx ingress (no CORS, one published port). The browser only ever
  talks to nginx on port 9180; nginx proxies `/api` to `backend:8000` on the
  internal compose network. The backend is never published to the LAN.
- Polling, not WebSockets. React Query refetches `/api/system` and
  `/api/storage` every ~2.5s. Stateless and resilient; the API contract is
  unchanged if a WS channel is added later.
- Nullable, fail-soft metrics. Each metric read is independent and guarded; a
  failure yields null/zero for that field, never a 500. This allows a single
  codebase to run on both the Pi and macOS.
- Config via env, host paths overridable. HOST_PROC, HOST_SYS, HOST_ROOT and
  STORAGE_MOUNTS come from the environment. On the Pi they point at read-only
  mounts; on macOS the backend detects missing paths and uses native reads.

## Backend Design

- routers/ are thin and delegate to services/. services/ own all host access
  (psutil, /proc, /sys) and return typed Pydantic models. models/ are the API
  contract. main.py wires the app, health endpoint and dev-only CORS.

### Metric sources
- CPU overall/per-core: psutil.cpu_percent; Memory: psutil.virtual_memory;
  Uptime: now - psutil.boot_time; Load: psutil.getloadavg.
- CPU temperature: host /sys/class/thermal/thermal_zone*/temp, then
  psutil.sensors_temperatures; null when unavailable.
- Pi model: host /proc/device-tree/model; null when not a Pi.
- OS/Debian version: /etc/os-release PRETTY_NAME, else platform string.
- Storage: psutil.disk_usage per configured mount, skipping missing mounts.

## Frontend Design

- api/client.ts holds TS types mirroring the Pydantic models and a fetch wrapper.
- hooks/useSystem.ts and useStorage.ts poll via React Query, keeping prior data
  while refetching; query error drives a global offline indicator.
- lib/thresholds.ts is the single source of healthy/warning/critical logic
  (usage <70 / 70-89 / >=90; temp <60 / 60-74 / >=75), matching the api-contract
  steering file. lib/format.ts formats bytes/percent/uptime/temperature.
- components/: MetricCard, StatusBadge, UsageBar, StatHeader, Unavailable.
- pages/Dashboard.tsx composes CPU, memory, temperature, uptime, load,
  system-info and per-filesystem storage cards in a mobile-first responsive grid.
- Tailwind, dark by default. Mobile-first single column expanding to 2-3 columns.

## Docker Design

- backend/Dockerfile: python:3.12-slim multi-stage, non-root user, uvicorn :8000.
- frontend/Dockerfile: node:20-alpine build stage -> nginx:alpine runtime stage
  serving the SPA and proxying /api to backend:8000.
- docker-compose.yml: two services, publish only 9180, read-only host mounts of
  /proc, /sys and /, restart: unless-stopped. No privileged mode, no Docker
  socket. macOS: the host mounts are harmless; Pi-only fields resolve to null.

## Error Handling

- Backend: per-metric try/except returning null/zero; endpoints always 200.
- Frontend: React Query isError -> offline banner; null fields -> Unavailable.

## Testing Strategy

- Backend: run uvicorn and curl /api/health, /api/system, /api/storage; confirm
  valid JSON and null temp/model on macOS.
- Frontend: npm run build must succeed (type-check); visual check at mobile and
  desktop widths.
- Integration: docker compose up --build, open http://<host>:9180, confirm live
  values and that docker compose down / up restores cleanly.
