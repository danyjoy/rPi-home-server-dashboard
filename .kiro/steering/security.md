---
inclusion: always
---

# Security Rules (Non-Negotiable)

This application will eventually gain controls that can restart services, so
security discipline starts now.

## Must NOT

- Do NOT run the application as root unnecessarily. Containers run as a
  non-root user.
- Do NOT use Docker privileged mode unless absolutely required and explicitly
  approved.
- Do NOT expose the Docker socket to the frontend. (Not used at all in Phase 1.)
- Do NOT store credentials, API tokens, or passwords in source code.
- Do NOT publish the backend container's port to the LAN. Only the frontend
  (nginx) ingress port is published.

## Must

- The backend is the ONLY component that talks to privileged/system APIs.
- The frontend only calls `/api/*` through the nginx proxy. It never holds or
  accesses Jellyfin/qBittorrent/Docker credentials.
- All secrets and sensitive config come from environment variables / Docker
  secrets. Commit `.env.example` (documented, no real values); gitignore `.env`.
- Host access for metrics uses the least privilege that works: read-only mounts
  of `/proc` and `/sys` (and the root fs for storage), NOT privileged mode.
- When reading files that may contain secrets, never echo secret values.

## Phase 1 Notes

- No authentication in Phase 1 (out of scope). The single nginx ingress is
  where auth will be added later, so keep that entry point clean.
- No external network calls that transmit host data anywhere. All processing is
  local to the Pi.
