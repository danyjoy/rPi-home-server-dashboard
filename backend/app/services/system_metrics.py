"""Collect system metrics for /api/system.

Every read is independent and fail-soft: if a source is missing (common on
macOS during local dev) the corresponding field becomes null/zero rather than
raising. This keeps the endpoint returning a valid 200 on both the Pi and a Mac.
"""

from __future__ import annotations

import glob
import os
import platform
import socket
import time

import psutil

from app.config import Settings, get_settings
from app.models.system import (
    CpuInfo,
    HostInfo,
    LoadAverage,
    MemoryInfo,
    SystemResponse,
)


def _host_path(base: str, relative: str) -> str | None:
    """Resolve a host file: prefer the mounted base if it exists, else native.

    `base` is e.g. settings.host_sys ("/host/sys"); `relative` is the path under
    the real root ("class/thermal/..."). Returns a path that exists, or None.
    """
    if base and os.path.isdir(base):
        candidate = os.path.join(base, relative)
        if os.path.exists(candidate):
            return candidate
    native = "/" + relative
    if os.path.exists(native):
        return native
    return None


def _read_cpu() -> CpuInfo:
    try:
        per_core = psutil.cpu_percent(percpu=True)
    except Exception:
        per_core = []
    try:
        overall = psutil.cpu_percent()
    except Exception:
        overall = 0.0
    core_count = psutil.cpu_count(logical=True) or len(per_core)
    return CpuInfo(
        usage_percent=round(float(overall), 1),
        per_core=[round(float(c), 1) for c in per_core],
        core_count=int(core_count or 0),
    )


def _read_memory() -> MemoryInfo:
    try:
        vm = psutil.virtual_memory()
        return MemoryInfo(
            total_bytes=int(vm.total),
            used_bytes=int(vm.used),
            available_bytes=int(vm.available),
            used_percent=round(float(vm.percent), 1),
        )
    except Exception:
        return MemoryInfo(
            total_bytes=0, used_bytes=0, available_bytes=0, used_percent=0.0
        )


def _read_uptime() -> int:
    try:
        return int(time.time() - psutil.boot_time())
    except Exception:
        return 0


def _read_load_average() -> LoadAverage:
    try:
        one, five, fifteen = psutil.getloadavg()
        return LoadAverage(
            one=round(float(one), 2),
            five=round(float(five), 2),
            fifteen=round(float(fifteen), 2),
        )
    except Exception:
        return LoadAverage(one=0.0, five=0.0, fifteen=0.0)


def _read_temperature(settings: Settings) -> float | None:
    """CPU temperature in °C. Try sysfs thermal zones, then psutil sensors."""
    # 1) Linux sysfs thermal zones (works on the Pi).
    base = settings.host_sys if os.path.isdir(settings.host_sys) else "/sys"
    try:
        pattern = os.path.join(base, "class", "thermal", "thermal_zone*", "temp")
        for temp_file in sorted(glob.glob(pattern)):
            try:
                with open(temp_file, "r", encoding="utf-8") as fh:
                    milli = int(fh.read().strip())
                # Values are typically in millidegrees Celsius.
                return round(milli / 1000.0, 1)
            except (OSError, ValueError):
                continue
    except Exception:
        pass

    # 2) psutil sensors (Linux only; absent on macOS).
    try:
        sensors = getattr(psutil, "sensors_temperatures", None)
        if sensors:
            readings = sensors()
            for entries in readings.values():
                for entry in entries:
                    if entry.current is not None:
                        return round(float(entry.current), 1)
    except Exception:
        pass

    return None


def _read_model(settings: Settings) -> str | None:
    """Raspberry Pi model from device-tree. Null when not a Pi (e.g. macOS)."""
    model_path = _host_path(settings.host_proc, "device-tree/model")
    if model_path is None:
        # Also try the common absolute location directly.
        for candidate in (
            os.path.join(settings.host_root, "proc/device-tree/model"),
            "/proc/device-tree/model",
            "/sys/firmware/devicetree/base/model",
        ):
            if os.path.exists(candidate):
                model_path = candidate
                break
    if model_path is None:
        return None
    try:
        with open(model_path, "rb") as fh:
            raw = fh.read()
        # device-tree strings are null-terminated.
        text = raw.decode("utf-8", errors="ignore").strip("\x00").strip()
        return text or None
    except OSError:
        return None


def _read_os(settings: Settings) -> str:
    """OS description. Prefer /etc/os-release PRETTY_NAME (Debian version)."""
    for candidate in (
        os.path.join(settings.host_root, "etc/os-release"),
        "/etc/os-release",
    ):
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as fh:
                    for line in fh:
                        if line.startswith("PRETTY_NAME="):
                            value = line.split("=", 1)[1].strip().strip('"')
                            if value:
                                return value
            except OSError:
                pass
            break
    # Fallback for non-Linux hosts (macOS dev).
    return f"{platform.system()} {platform.release()}".strip()


def _read_hostname() -> str:
    try:
        return socket.gethostname() or "unknown"
    except Exception:
        return "unknown"


def collect_system() -> SystemResponse:
    settings = get_settings()
    return SystemResponse(
        cpu=_read_cpu(),
        memory=_read_memory(),
        temperature_celsius=_read_temperature(settings),
        uptime_seconds=_read_uptime(),
        load_average=_read_load_average(),
        host=HostInfo(
            model=_read_model(settings),
            os=_read_os(settings),
            hostname=_read_hostname(),
        ),
    )
