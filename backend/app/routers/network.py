"""Router for network metrics. Thin: delegates to the service layer."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.network import NetworkResponse
from app.services.network_metrics import collect_network

router = APIRouter(prefix="/api", tags=["network"])


@router.get("/network", response_model=NetworkResponse)
def get_network() -> NetworkResponse:
    return collect_network()
