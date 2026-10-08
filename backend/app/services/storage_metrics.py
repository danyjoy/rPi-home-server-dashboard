"""Collect filesystem usage for /api/storage.

Each configured mount is reported via psutil.disk_usage. Mounts that do not
exist are skipped silently so a misconfigured or absent media drive never breaks
the endpoint. When the host root is mounted read-only into the container
(/host/root on the Pi), configured paths are resolved under that mount.
"""

from __future__ import annotations

import os

import psutil

from app.config import get_settings
from app.models.storage import FilesystemUsage, StorageResponse


def _resolve(host_root: str, mount_path: str) -> str:
    """Map a logical mount path to where it is visible to the backend.

    If the host filesystem is mounted at host_root, join the two; otherwise use
    the path natively (local dev on macOS or bare-metal install).
    """
    if host_root and os.path.isdir(host_root):
        # Strip the leading slash so os.path.join nests under host_root.
        joined = os.path.join(host_root, mount_path.lstrip("/"))
        if os.path.exists(joined):
            return joined
    return mount_path


def collect_storage() -> StorageResponse:
    settings = get_settings()
    filesystems: list[FilesystemUsage] = []

    for name, mount_path in settings.parsed_storage_mounts():
        resolved = _resolve(settings.host_root, mount_path)
        if not os.path.exists(resolved):
            continue
        try:
            usage = psutil.disk_usage(resolved)
        except (OSError, PermissionError):
            continue
        filesystems.append(
            FilesystemUsage(
                name=name,
                mount=mount_path,
                total_bytes=int(usage.total),
                used_bytes=int(usage.used),
                free_bytes=int(usage.free),
                used_percent=round(float(usage.percent), 1),
            )
        )

    return StorageResponse(filesystems=filesystems)
