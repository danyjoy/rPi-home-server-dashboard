---
inclusion: always
---

# API Contract

The backend exposes clean REST endpoints under `/api`. Pydantic models are the
source of truth; frontend TypeScript types must mirror them exactly. All sizes
are bytes; the frontend formats for display. Fields that can be unavailable are
nullable and must degrade gracefully (show "unavailable", never crash).

## Conventions

- JSON only. snake_case keys (matching Pydantic field names).
- Sizes in bytes, percentages as floats 0-100, times in seconds, temps in °C.
- Nullable when the host may not provide it (e.g. CPU temperature, Pi model
  when developing off-device).

## Phase 1 Endpoints

### GET /api/health
```json
{ "status": "ok" }
```

### GET /api/system
```json
{
  "cpu": {
    "usage_percent": 23.5,
    "per_core": [12.0, 30.1, 20.0, 31.9],
    "core_count": 4
  },
  "memory": {
    "total_bytes": 4194304000,
    "used_bytes": 1600000000,
    "available_bytes": 2500000000,
    "used_percent": 38.1
  },
  "temperature_celsius": 48.2,
  "uptime_seconds": 184233,
  "load_average": { "one": 0.42, "five": 0.55, "fifteen": 0.60 },
  "host": {
    "model": "Raspberry Pi 4 Model B Rev 1.4",
    "os": "Debian GNU/Linux 12 (bookworm)",
    "hostname": "homeserver"
  }
}
```
`temperature_celsius` and `host.model` are nullable.

### GET /api/storage
```json
{
  "filesystems": [
    {
      "name": "root",
      "mount": "/",
      "total_bytes": 125000000000,
      "used_bytes": 48000000000,
      "free_bytes": 77000000000,
      "used_percent": 38.4
    }
  ]
}
```

## Future Endpoints (do NOT implement in Phase 1)

Reserved for later phases, same conventions:
`/api/network`, `/api/services`, `/api/jellyfin`, `/api/qbittorrent`.

## Health State Thresholds (frontend)

Used to color healthy / warning / critical indicators consistently:

- Usage percent (CPU, RAM, disk): healthy < 70, warning 70-89, critical >= 90.
- CPU temperature (°C): healthy < 60, warning 60-74, critical >= 75.

Keep these thresholds in one shared place on the frontend.
