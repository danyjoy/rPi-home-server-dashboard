"""Collect network throughput metrics for /api/network.

This is the first *stateful* service in the codebase. Every other resource
(`system`, `storage`) is a fresh, stateless read. Network *rates* cannot be:
``psutil.net_io_counters()`` returns cumulative counters since boot, so a rate
is only meaningful as the change between two samples over elapsed time. Phase 1
has no database and no persisted state, so the previous sample is held in memory
between requests.

Because uvicorn serves the synchronous endpoint from a thread pool, two
overlapping requests could race on the shared sample — interleaving a read,
compute, and store would risk a torn read (bytes from one request, timestamp
from another) or a lost update. The read-current -> compute -> store-sample
critical section is therefore guarded by a module-level ``threading.Lock``. The
critical section is only a couple of reads and some arithmetic, so the lock is
cheap; it exists for correctness of the derived rates. Do NOT remove it.

Like ``system_metrics.py``, each read is independent and fail-soft: a missing or
unreadable source yields a null field rather than raising, keeping the endpoint
returning a valid 200 on both the Pi and a Mac.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable

import psutil

from app.models.network import AggregateThroughput, NetworkResponse


@dataclass
class _Sample:
    """A single network counter reading plus the monotonic time it was taken.

    ``aggregate`` holds ``(bytes_sent, bytes_recv)``; either element may be
    ``None`` if that counter was unreadable, and the whole tuple is ``None``
    when no reading has ever been obtained. ``monotonic`` is a
    ``time.monotonic()`` timestamp — it never jumps backward on clock changes,
    so the elapsed delta between samples stays sane.
    """

    aggregate: tuple[int | None, int | None] | None
    monotonic: float


def _derive_rate(
    prev_bytes: int | None,
    cur_bytes: int | None,
    elapsed: float,
) -> float | None:
    """Derive a throughput rate (bytes/sec) from two counter readings.

    Pure function of its arguments so it is directly property-testable. Returns
    ``None`` when a rate cannot be meaningfully computed:

    - no previous value yet (first request after boot),
    - ``elapsed <= 0`` (no time passed, or a non-positive delta),
    - the current counter is lower than the previous one (a reset or counter
      wrap in this direction),
    - either byte value is unreadable (``None``).

    Otherwise returns ``round((cur_bytes - prev_bytes) / elapsed, 2)``, which is
    always non-negative because the decrease case is already excluded.
    """
    if prev_bytes is None or cur_bytes is None:
        return None
    if elapsed <= 0:
        return None
    if cur_bytes < prev_bytes:
        return None
    return round((cur_bytes - prev_bytes) / elapsed, 2)


# --- In-memory sample state (the one stateful bit) --------------------------
#
# The retained sample is a module-level singleton guarded by ``_lock``. It holds
# the last reading obtained so the next request can measure a rate against it.
# It starts as ``None`` meaning "no baseline yet" — the first request records a
# sample and returns null rates.
_sample: _Sample | None = None
_lock = threading.Lock()


# --- Test seams -------------------------------------------------------------
#
# ``collect_network()`` reads counters and monotonic time through these two
# indirections so tests can inject consecutive readings and timestamps instead
# of calling real psutil / the real clock. Production uses the defaults below.
def _read_aggregate() -> tuple[int | None, int | None]:
    """Read cumulative ``(bytes_sent, bytes_recv)`` system-wide.

    Fail-soft like ``system_metrics.py``: each counter is read independently so
    one failing does not null the other, and a total failure of
    ``net_io_counters()`` yields ``(None, None)`` rather than raising.
    """
    try:
        counters = psutil.net_io_counters()
    except Exception:
        return (None, None)

    try:
        sent: int | None = int(counters.bytes_sent)
    except Exception:
        sent = None
    try:
        recv: int | None = int(counters.bytes_recv)
    except Exception:
        recv = None
    return (sent, recv)


# Overridable providers (the seam). Tests reassign these; production reads real
# counters and the real monotonic clock.
read_aggregate: Callable[[], tuple[int | None, int | None]] = _read_aggregate
monotonic: Callable[[], float] = time.monotonic


def collect_network() -> NetworkResponse:
    """Collect aggregate network throughput, deriving rates against the last sample.

    Acquires the lock for the whole read-current -> compute -> store-sample
    critical section (see module docstring). ``download`` maps to received bytes
    (``bytes_recv``); ``upload`` maps to sent bytes (``bytes_sent``).

    The retained sample is replaced only *after* a reading has been obtained, so
    if obtaining the current reading raises, the exception propagates (the router
    returns a 5xx, no partial 200) and the retained sample is left untouched.
    """
    global _sample

    with _lock:
        # If this raises, we propagate without mutating ``_sample``.
        cur_sent, cur_recv = read_aggregate()
        now = monotonic()

        prev = _sample
        if prev is None:
            prev_sent: int | None = None
            prev_recv: int | None = None
            elapsed = 0.0
        else:
            prev_sent, prev_recv = prev.aggregate or (None, None)
            elapsed = now - prev.monotonic

        download_rate = _derive_rate(prev_recv, cur_recv, elapsed)
        upload_rate = _derive_rate(prev_sent, cur_sent, elapsed)

        response = NetworkResponse(
            aggregate=AggregateThroughput(
                bytes_sent=cur_sent,
                bytes_recv=cur_recv,
                download_rate_bps=download_rate,
                upload_rate_bps=upload_rate,
            )
        )

        # Replace the retained sample only after a reading was obtained.
        _sample = _Sample(aggregate=(cur_sent, cur_recv), monotonic=now)

        return response
