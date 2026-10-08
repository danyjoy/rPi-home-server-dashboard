# Implementation Plan — Phase 1: System Monitoring

- [x] 1. Project foundation
- [x] 1.1 Root project files (.gitignore, .env.example, README.md)
- [x] 1.2 Backend package skeleton (requirements.txt, app package, config.py)

- [x] 2. Backend metrics API
- [x] 2.1 Pydantic models (API contract)
- [x] 2.2 System metrics service (psutil + host reads, fail-soft)
- [x] 2.3 Storage metrics service (disk usage per configured mount)
- [x] 2.4 Routers and app factory (health, system, storage, dev CORS)
- [x] 2.5 Verify backend locally (curl health/system/storage)

- [x] 3. Frontend foundation
- [x] 3.1 Scaffold Vite + TS + Tailwind (dark default)
- [x] 3.2 Typed API client and polling hooks (React Query)
- [x] 3.3 Formatting and thresholds helpers

- [x] 4. Dashboard UI
- [x] 4.1 Reusable components (MetricCard, StatusBadge, UsageBar, StatHeader, Unavailable)
- [x] 4.2 Dashboard page (responsive grid, offline handling)
- [x] 4.3 Verify frontend build (npm run build)

- [x] 5. Dockerization and integration
- [x] 5.1 Backend Dockerfile (non-root)
- [x] 5.2 Frontend Dockerfile + nginx.conf
- [x] 5.3 docker-compose.yml (publish only 9180, read-only host mounts)
- [x] 5.4 Verify full stack (compose up/down restore)
