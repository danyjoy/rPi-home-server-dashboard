---
inclusion: always
---

# Product: Home Server Command Center

A self-hosted, mobile-first web dashboard for a Raspberry Pi 4 (Debian) that
acts as a single "command center" for the Pi's health, storage, network, and
the services it runs (Jellyfin, qBittorrent, Docker containers, etc.).

Primary user: the owner of the Pi, accessing the dashboard from a phone over
the local network.

Primary deployment target is the Raspberry Pi (Debian / arm64). The stack must
also run on macOS for local development and testing, where some host-specific
metrics (CPU temperature, Pi model) are unavailable and degrade gracefully.

## Core Principles

- Lightweight. Must run comfortably on a Raspberry Pi 4 with 4 GB RAM.
- Self-hosted. No AWS, Firebase, or other cloud infrastructure is required.
- Mobile-first. Phone is the primary target; desktop must also work well.
- Read before control. Monitoring comes first; destructive controls come later
  and must be explicit and safe.
- Incremental. Features are delivered in phases; do not build future phases
  early.

## Phased Roadmap

- Phase 1: System monitoring (CPU, RAM, temperature, uptime, load, Pi model,
  Debian version, basic storage).
- Phase 2: Expanded system + storage detail.
- Phase 3: Service monitoring (status, resource usage, ports).
- Phase 4: Jellyfin integration.
- Phase 5: qBittorrent integration.
- Phase 6: Service controls (start / stop / restart).
- Phase 7: Historical metrics and charts.
- Phase 8: Notifications and alerts.
- Phase 9: Secure remote access (Tailscale) and authentication.

## Current Scope: Phase 1 ONLY

Implement only system monitoring and basic storage:

- Project structure, React+TS+Vite frontend, FastAPI backend, Docker Compose.
- CPU usage, RAM usage, CPU temperature, uptime, load average.
- Raspberry Pi model and Debian version.
- Basic storage: total, used, free, usage percent.

### Explicitly OUT of scope for Phase 1

Do not implement any of the following until their phase is reached:
Jellyfin, qBittorrent, Docker container management, service start/stop/restart,
network monitoring, historical metrics, charts needing persisted data, Telegram
notifications, alerts, Home Assistant, ESP32, authentication, Tailscale/remote
access.

### Phase 1 Boundary Rule

Keep the implementation modular so future phases slot in without restructuring,
but do NOT create speculative infrastructure or abstractions for future phases
unless they are required to keep the Phase 1 architecture clean.
