"""Router for storage metrics. Thin: delegates to the service layer."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.storage import StorageResponse
from app.services.storage_metrics import collect_storage

router = APIRouter(prefix="/api", tags=["storage"])


@router.get("/storage", response_model=StorageResponse)
def get_storage() -> StorageResponse:
    return collect_storage()
