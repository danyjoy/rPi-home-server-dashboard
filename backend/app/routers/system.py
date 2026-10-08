"""Router for system metrics. Thin: delegates to the service layer."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.system import SystemResponse
from app.services.system_metrics import collect_system

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system", response_model=SystemResponse)
def get_system() -> SystemResponse:
    return collect_system()
