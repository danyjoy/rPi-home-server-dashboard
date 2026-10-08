"""Pydantic response models for /api/system. These models ARE the API contract.

Fields that a host may not provide (CPU temperature, Pi model) are nullable so
the frontend can render an "unavailable" state instead of the API failing. This
is what lets the same backend run on both the Raspberry Pi and macOS.
"""

from __future__ import annotations

from pydantic import BaseModel


class CpuInfo(BaseModel):
    usage_percent: float
    per_core: list[float]
    core_count: int


class MemoryInfo(BaseModel):
    total_bytes: int
    used_bytes: int
    available_bytes: int
    used_percent: float


class LoadAverage(BaseModel):
    one: float
    five: float
    fifteen: float


class HostInfo(BaseModel):
    model: str | None  # Raspberry Pi model; null when unavailable (e.g. macOS)
    os: str
    hostname: str


class SystemResponse(BaseModel):
    cpu: CpuInfo
    memory: MemoryInfo
    temperature_celsius: float | None  # null when the host exposes no sensor
    uptime_seconds: int
    load_average: LoadAverage
    host: HostInfo
