---
inclusion: always
---

# Project Structure & Module Boundaries

Keep frontend and backend cleanly separated. Each new phase should add modules
without rewriting existing ones.

## Repository Layout

```
home-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py            # app factory, router registration, health
│   │   ├── config.py          # settings via pydantic-settings (env-driven)
│   │   ├── routers/           # one module per resource (system, storage, ...)
│   │   ├── services/          # metric collection logic (psutil, host reads)
│   │   └── models/            # pydantic response models = the API contract
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               # typed client + response types mirroring models
│   │   ├── hooks/             # React Query polling hooks (useSystem, ...)
│   │   ├── components/        # reusable UI (MetricCard, StatusBadge, ...)
│   │   ├── pages/             # Dashboard and future pages
│   │   └── lib/               # formatting, thresholds, helpers
│   ├── nginx.conf             # static serving + /api proxy
│   ├── Dockerfile
│   └── (vite, tailwind, ts configs)
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Boundary Rules

- Routers are thin: validate/shape requests and delegate to services. No metric
  logic in routers.
- Services own all system access (psutil, /proc, /sys). They return typed data.
- Models (Pydantic) are the single source of truth for the API shape. Frontend
  types mirror them.
- Frontend never talks to Docker, Jellyfin, or qBittorrent directly. It only
  calls `/api/*`.
- One router + one service per resource. Adding a phase = adding a new
  router/service/model trio and new frontend hook/components, not editing the
  core app wiring beyond registration.

## Naming

- Backend: snake_case modules, PascalCase Pydantic models.
- Frontend: PascalCase components, camelCase hooks/functions, `use*` for hooks.
