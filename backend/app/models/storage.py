"""Pydantic response models for /api/storage."""

from __future__ import annotations

from pydantic import BaseModel


class FilesystemUsage(BaseModel):
    name: str
    mount: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float


class StorageResponse(BaseModel):
    filesystems: list[FilesystemUsage]
