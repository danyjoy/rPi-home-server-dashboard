# Implementation Plan — Phase 1: System Monitoring

- [x] 1. Project foundation
- [x] 1.1 Root project files
  - Create `.gitignore`, `.env.example`, and `README.md` with run instructions.
  - _Requirements: 1.1, 1.5_
- [x] 1.2 Backend package skeleton
  - Create `backend/requirements.txt`, `backend/app/__init__.py`, and `config.py`
    (pydantic-settings, STORAGE_MOUNTS parsing, host-path settings).
  - _Requirements: 1.1, 1.5, 2.5, 6.2_

- [x] 2. Backend metrics API
- [x] 2.1 Pydantic models (API contract)
  - Add `models/system.py` and `models/storage.py` matching the API-contract
    steering file, with nullable temperature and model.
  - _Requirements: 2.2, 2.3, 2.4, 3.1_
- [x] 2.2 System metrics service
  - Implement `services/system_metrics.py`: psutil for CPU/mem/uptime/load; host
    reads for temperature, Pi model, Debian version; per-metric fail-soft.
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 6.1_
- [x] 2.3 Storage metrics service
  - Implement `services/storage_metrics.py`: disk usage per configured mount,
    skipping missing mounts.
  - _Requirements: 3.1, 3.2, 3.3_
- [x] 2.4 Routers and app factory
  - Add `routers/system.py`, `routers/storage.py`, and `main.py` (health, router
    registration, dev-only CORS).
  - _Requirements: 2.1, 2.2, 3.1_
- [x] 2.5 Verify backend locally
  - Run uvicorn and curl `/api/health`, `/api/system`, `/api/storage`; confirm
    valid JSON and null Pi-only fields on macOS.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1_

- [x] 3. Frontend foundation
- [x] 3.1 Scaffold Vite + TS + Tailwind
  - Create package.json, Vite/TS/Tailwind/PostCSS configs, `index.html`,
    `main.tsx`, `App.tsx`, `index.css` with dark theme default.
  - _Requirements: 4.7_
- [x] 3.2 Typed API client and polling hooks
  - Add `api/client.ts` (types mirroring models), `hooks/useSystem.ts`,
    `hooks/useStorage.ts` with React Query polling.
  - _Requirements: 4.5, 4.6_
- [x] 3.3 Formatting and thresholds helpers
  - Add `lib/format.ts` and `lib/thresholds.ts` (shared healthy/warning/critical).
  - _Requirements: 4.3_

- [x] 4. Dashboard UI
- [x] 4.1 Reusable components
  - `MetricCard`, `StatusBadge`, `UsageBar`, `StatHeader`, `Unavailable`.
  - _Requirements: 4.1, 4.3, 4.4_
- [x] 4.2 Dashboard page
  - Compose CPU, memory, temperature, uptime, load, system-info, and storage
    cards in a mobile-first responsive grid with offline handling.
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
- [x] 4.3 Verify frontend build
  - Run `npm run build` and resolve any type errors.
  - _Requirements: 4.1, 4.2_

- [x] 5. Dockerization and integration
- [x] 5.1 Backend Dockerfile (non-root)
  - Multi-stage, non-root user, uvicorn on 8000.
  - _Requirements: 1.2, 5.1_
- [x] 5.2 Frontend Dockerfile + nginx.conf
  - Multi-stage build, nginx serving SPA and proxying `/api` to backend.
  - _Requirements: 1.2, 5.3_
- [x] 5.3 docker-compose.yml
  - Two services, publish only 9180, read-only host mounts, non-root, no
    privileged, restart: unless-stopped.
  - _Requirements: 1.2, 1.3, 1.4, 5.1, 5.2, 6.2_
- [x] 5.4 Verify full stack
  - `docker compose up --build`, confirm dashboard at :9180 shows live metrics;
    confirm `down`/`up` restores cleanly.
  - _Requirements: 1.2, 1.3, 1.4, 4.2, 6.2_
