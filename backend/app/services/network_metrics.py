"""Collect network throughput metrics for /api/network.

This is the first *stateful* service in the codebase. Every other resource
(`system`, `storage`) is a fresh, stateless read. Network *rates* cannot be:
``psutil.net_io_counters()`` returns cumulative counters since boot, so a rate
is only meaningful as the change between two samples over elapsed time. Phase 1
has no database and no persisted state, so the sampling state is held in memory.

Why a background sampler instead of sampling per request
--------------------------------------------------------
A rate must be measured over a *known, stable* interval. If the rate were
derived from the gap between consecutive HTTP requests, that gap would be set by
the client, not the server, and it is neither fixed nor controlled: React
Query's ``refetchInterval`` is best-effort, and ``refetchOnMount`` /
``refetchOnReconnect`` / React 18 StrictMode remounts / a second browser tab can
all fire extra ``/api/network`` requests. An extra request landing a few tens of
milliseconds after the previous one shrinks the measurement window to near zero,
and a short window over a bursty TCP counter reads as a wildly inflated,
flickering rate (e.g. a 60 KB burst caught in 50 ms looks like >1 MB/s when the
real rate is ~100 KB/s).

To make the reported rate correct regardless of how (or how often) the client
polls, sampling is driven by a background thread on a fixed cadence
(``SAMPLE_INTERVAL_SECONDS``). The thread records consecutive counter readings
and derives the rate over its own known interval. A ``GET /api/network`` request
is then **idempotent**: it just returns the most recently computed snapshot and
never touches the sampling window. This removes the coupling between request
timing and the measured rate.

Concurrency: the background sampler writes the shared snapshot and requests read
it, so the read/compute/store critical section and the snapshot read are guarded
by a module-level ``threading.Lock``. The critical section is a couple of reads
and some arithmetic, so the lock is cheap; it exists for correctness of the
derived rates and a torn-read-free snapshot. Do NOT remove it.

Like ``system_metrics.py``, each read is independent and fail-soft: a missing or
unreadable source yields a null field rather than raising, keeping the endpoint
returning a valid 200 on both the Pi and a Mac.
"""

from __future__ import annotations

import atexit
import threading
import time
from dataclasses import dataclass
from typing import Callable

import psutil

from app.models.network import AggregateThroughput, NetworkResponse

# How often the background thread samples the counters. The reported rate is
# measured over this interval, independent of the client's polling cadence.
SAMPLE_INTERVAL_SECONDS = 2.0


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


@dataclass
class _Snapshot:
    """The latest counters plus the rates derived over the last sample interval.

    This is what a ``GET /api/network`` request returns. It is produced by the
    background sampler and read (never mutated) by request handlers.
    """

    bytes_sent: int | None
    bytes_recv: int | None
    download_rate_bps: float | None
    upload_rate_bps: float | None


def _derive_rate(
    prev_bytes: int | None,
    cur_bytes: int | None,
    elapsed: float,
) -> float | None:
    """Derive a throughput rate (bytes/sec) from two counter readings.

    Pure function of its arguments so it is directly property-testable. Returns
    ``None`` when a rate cannot be meaningfully computed:

    - no previous value yet (first sample after boot),
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


# --- In-memory sampling state (the stateful bit) ----------------------------
#
# ``_sample`` is the previous reading the sampler measures the next rate
# against. ``_snapshot`` is the latest computed result a request returns. Both
# are module-level singletons guarded by ``_lock``. They start as ``None``
# meaning "no baseline / nothing computed yet"; the first sample records a
# baseline and publishes null rates.
_sample: _Sample | None = None
_snapshot: _Snapshot | None = None
_lock = threading.Lock()


# --- Test seams -------------------------------------------------------------
#
# The rate logic reads counters and monotonic time through these two
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


def _take_sample() -> _Snapshot:
    """Read current counters, derive rates against the previous sample, publish.

    This is the read-current -> compute -> store critical section, guarded by
    ``_lock``. It is called by the background sampler on a fixed cadence (and
    once synchronously at startup so the first request has data). ``download``
    maps to received bytes (``bytes_recv``); ``upload`` maps to sent bytes
    (``bytes_sent``).

    The retained sample and published snapshot are replaced only *after* a
    reading has been obtained, so if obtaining the current reading raises, the
    exception propagates and the retained state is left untouched.
    """
    global _sample, _snapshot

    with _lock:
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

        snapshot = _Snapshot(
            bytes_sent=cur_sent,
            bytes_recv=cur_recv,
            download_rate_bps=_derive_rate(prev_recv, cur_recv, elapsed),
            upload_rate_bps=_derive_rate(prev_sent, cur_sent, elapsed),
        )

        # Replace retained state only after a reading was obtained.
        _sample = _Sample(aggregate=(cur_sent, cur_recv), monotonic=now)
        _snapshot = snapshot
        return snapshot


def collect_network() -> NetworkResponse:
    """Return the latest sampled throughput snapshot (idempotent read).

    Does NOT sample on the request path, so the reported rate is measured over
    the background sampler's fixed interval, not the gap between HTTP requests.
    If the sampler has not produced a snapshot yet (e.g. the very first request
    before the startup sample ran), one is taken synchronously so the endpoint
    still returns a valid body.
    """
    with _lock:
        snap = _snapshot

    if snap is None:
        snap = _take_sample()

    return NetworkResponse(
        aggregate=AggregateThroughput(
            bytes_sent=snap.bytes_sent,
            bytes_recv=snap.bytes_recv,
            download_rate_bps=snap.download_rate_bps,
            upload_rate_bps=snap.upload_rate_bps,
        )
    )


# --- Background sampler -----------------------------------------------------
#
# A single daemon thread samples on a fixed cadence so rates are decoupled from
# request timing. Daemon so it never blocks interpreter shutdown; an atexit hook
# also signals it to stop for a clean exit under uvicorn's reloader.
_sampler_thread: threading.Thread | None = None
_sampler_stop = threading.Event()
_sampler_lock = threading.Lock()


def _sampler_loop() -> None:
    while not _sampler_stop.is_set():
        try:
            _take_sample()
        except Exception:
            # Fail-soft: a transient read failure must not kill the sampler.
            # The next tick retries; requests keep the last good snapshot.
            pass
        _sampler_stop.wait(SAMPLE_INTERVAL_SECONDS)


def start_sampler() -> None:
    """Start the background sampler once. Idempotent and safe to call at startup."""
    global _sampler_thread
    with _sampler_lock:
        if _sampler_thread is not None and _sampler_thread.is_alive():
            return
        # Take a baseline immediately so the first request has counters to show.
        _take_sample()
        _sampler_stop.clear()
        _sampler_thread = threading.Thread(
            target=_sampler_loop,
            name="network-sampler",
            daemon=True,
        )
        _sampler_thread.start()


def stop_sampler() -> None:
    """Signal the sampler to stop and wait briefly for it to exit."""
    global _sampler_thread
    with _sampler_lock:
        _sampler_stop.set()
        thread = _sampler_thread
        _sampler_thread = None
    if thread is not None:
        thread.join(timeout=SAMPLE_INTERVAL_SECONDS + 1.0)


atexit.register(stop_sampler)
