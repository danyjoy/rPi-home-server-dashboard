"""FastAPI application factory for the Home Server Command Center backend.

Phase 1 exposes read-only system and storage metrics. In the Docker setup the
frontend reaches this app same-origin via the nginx /api proxy, so CORS is only
relevant for the local Vite dev server.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import network, storage, system


def create_app() -> FastAPI:
    app = FastAPI(
        title="Home Server Command Center",
        version="0.1.0",
        description="Phase 1: system and storage monitoring.",
    )

    # Dev-only: allow the Vite dev server to call the API directly.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(system.router)
    app.include_router(storage.router)
    app.include_router(network.router)
    return app


app = create_app()
