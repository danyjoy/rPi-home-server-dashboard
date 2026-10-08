"""Application configuration, driven by environment variables.

All host-path settings default to the read-only mount points used in
docker-compose on the Raspberry Pi. On macOS (local dev) these paths do not
exist; the metric services detect that and fall back to psutil / native reads,
returning null for anything the host cannot provide.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Where the host's /proc, /sys and root fs are mounted inside the container.
    # Empty / nonexistent paths mean "not mounted" -> use native reads.
    host_proc: str = "/host/proc"
    host_sys: str = "/host/sys"
    host_root: str = "/host/root"

    # Comma-separated "name:path" entries to report under /api/storage.
    storage_mounts: str = "root:/"

    def parsed_storage_mounts(self) -> list[tuple[str, str]]:
        """Return [(name, path), ...] parsed from the STORAGE_MOUNTS string."""
        entries: list[tuple[str, str]] = []
        for item in self.storage_mounts.split(","):
            item = item.strip()
            if not item:
                continue
            name, _, path = item.partition(":")
            name = name.strip()
            path = path.strip()
            if name and path:
                entries.append((name, path))
        if not entries:
            entries.append(("root", "/"))
        return entries


@lru_cache
def get_settings() -> Settings:
    return Settings()
