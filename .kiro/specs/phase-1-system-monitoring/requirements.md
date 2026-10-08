# Requirements — Phase 1: System Monitoring

## Introduction

Phase 1 delivers the foundation of the Home Server Command Center: a lightweight,
mobile-first, self-hosted dashboard that displays the Raspberry Pi's live system
health and basic storage usage. It consists of a React + TypeScript + Vite
frontend served by nginx, a FastAPI + psutil backend, and a Docker Compose setup
that runs both on the Raspberry Pi (Debian / arm64) and on macOS for local
testing. No cloud services, no database, no authentication, and no third-party
integrations are in scope for this phase.

The primary target is the Raspberry Pi, accessed from a phone over the local
network. The stack must also run on macOS, where host-specific metrics (CPU
temperature, Pi model) are unavailable and must degrade gracefully.

## Requirements

### Requirement 1 — Project foundation and Docker Compose

**User Story:** As the server owner, I want a cleanly structured, Dockerized
project, so that I can build and run the whole dashboard with a single command
and extend it in later phases without restructuring.

#### Acceptance Criteria
1. WHEN the repository is inspected THEN it SHALL contain separate `backend/` and
   `frontend/` directories with the module boundaries defined in the structure
   steering file.
2. WHEN `docker compose up --build` is run THEN the system SHALL start exactly two
   services: a frontend (nginx) and a backend (FastAPI).
3. WHEN compose is running THEN only the frontend ingress port (9180) SHALL be
   published to the host; the backend port SHALL NOT be published to the LAN.
4. WHEN the stack is stopped with `docker compose down` and started again THEN it
   SHALL resume with the same configuration and no lost state (config comes from
   `.env` / compose).
5. WHEN secrets or environment values are needed THEN they SHALL be read from
   environment variables; `.env.example` SHALL be committed and `.env` SHALL be
   gitignored.

### Requirement 2 — System metrics API

**User Story:** As the server owner, I want the backend to expose the Pi's system
metrics over a clean API, so that the frontend (and future clients) can read them
without touching the host directly.

#### Acceptance Criteria
1. WHEN `GET /api/health` is called THEN the backend SHALL return `{"status":"ok"}`.
2. WHEN `GET /api/system` is called THEN the backend SHALL return CPU usage
   (overall and per-core with core count), memory (total/used/available bytes and
   used percent), uptime in seconds, and 1/5/15-minute load averages.
3. WHEN `GET /api/system` is called on a host that exposes a CPU temperature
   sensor THEN `temperature_celsius` SHALL be the sensor value; WHEN no sensor is
   available (e.g. macOS) THEN it SHALL be `null`.
4. WHEN `GET /api/system` is called THEN `host` SHALL include the OS description,
   the hostname, and the Raspberry Pi model where available; WHEN the model is
   unavailable THEN `model` SHALL be `null`.
5. WHEN the backend runs on Debian with host `/proc` and `/sys` mounted THEN it
   SHALL read the Pi model and Debian version from the host; WHEN those paths are
   absent THEN it SHALL fall back to native reads without raising.
6. WHEN any individual metric read fails THEN the endpoint SHALL still return a
   valid response with that field null/zero rather than returning an error.

### Requirement 3 — Storage metrics API

**User Story:** As the server owner, I want basic storage usage for the Pi's
filesystems, so that I can see how much disk is used and free.

#### Acceptance Criteria
1. WHEN `GET /api/storage` is called THEN the backend SHALL return a list of
   filesystems, each with name, mount, total/used/free bytes, and used percent.
2. WHEN the `STORAGE_MOUNTS` setting lists multiple mounts THEN each existing
   mount SHALL be reported; mounts that do not exist SHALL be skipped without
   error.
3. WHEN no configured mount exists THEN the response SHALL contain an empty list
   rather than raising.

### Requirement 4 — Dashboard UI

**User Story:** As the server owner, I want a mobile-first dashboard that shows
the metrics clearly, so that I can check my server's health from my phone.

#### Acceptance Criteria
1. WHEN the dashboard loads on a phone-sized viewport THEN it SHALL present
   metrics in a single-column, touch-friendly layout; WHEN loaded on desktop THEN
   it SHALL use a responsive multi-column grid.
2. WHEN the dashboard is open THEN it SHALL display CPU usage, RAM usage, CPU
   temperature, uptime, load average, Pi model, Debian version, and storage
   (total/used/free/percent).
3. WHEN metrics are displayed THEN usage and temperature indicators SHALL be
   colored healthy / warning / critical using the shared thresholds from the API
   contract steering file.
4. WHEN a value is unavailable (null) THEN the UI SHALL show an "unavailable"
   state rather than an error or a crash.
5. WHEN the dashboard is open THEN it SHALL poll the API on an interval (~2–3s)
   and update values without a full page reload.
6. WHEN the backend is unreachable THEN the UI SHALL show a clear error/offline
   state and recover automatically when the backend returns.
7. WHEN rendered THEN the UI SHALL default to a dark theme.

### Requirement 5 — Security and least privilege

**User Story:** As the server owner, I want the dashboard to run with minimal
privilege, so that a monitoring tool never becomes a security liability.

#### Acceptance Criteria
1. WHEN the containers run THEN they SHALL run as a non-root user and SHALL NOT
   use Docker privileged mode.
2. WHEN the backend reads host metrics THEN it SHALL use read-only mounts of host
   `/proc`, `/sys`, and the root filesystem, and nothing more.
3. WHEN the frontend serves the app THEN it SHALL only reach the backend via the
   nginx `/api` proxy and SHALL NOT access the Docker socket or any credentials.
4. WHEN the project is built THEN no credentials, tokens, or passwords SHALL be
   present in source.

### Requirement 6 — Cross-platform operation

**User Story:** As a developer, I want to run the stack on macOS for testing, so
that I can develop without the Raspberry Pi.

#### Acceptance Criteria
1. WHEN the stack runs on macOS THEN `/api/system` and `/api/storage` SHALL return
   valid responses with Pi-only fields null and real values for everything psutil
   can provide.
2. WHEN the stack runs on macOS via Docker Compose THEN it SHALL start without
   requiring host `/proc` or `/sys` mounts to exist.
