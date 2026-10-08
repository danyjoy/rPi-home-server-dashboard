"""Pydantic response models for /api/network. These models ARE the API contract.

Cumulative byte counters and derived throughput rates are nullable because a
host read can fail (fail-soft) and because rates are undefined until a baseline
sample exists. The frontend renders an "unavailable" state for any null value
instead of the API failing.
"""

from __future__ import annotations

from pydantic import BaseModel


class AggregateThroughput(BaseModel):
    bytes_sent: int | None  # cumulative since boot; null if unreadable
    bytes_recv: int | None  # cumulative since boot; null if unreadable
    download_rate_bps: float | None  # bytes/sec; null until a baseline exists
    upload_rate_bps: float | None  # bytes/sec; null until a baseline exists


class NetworkResponse(BaseModel):
    aggregate: AggregateThroughput
