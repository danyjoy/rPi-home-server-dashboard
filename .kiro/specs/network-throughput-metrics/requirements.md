# Requirements Document

## Introduction

This feature adds network throughput monitoring to the Home Server Command Center
dashboard: cumulative bytes sent and received since boot, plus derived aggregate
download and upload rates (bytes per second). The data is collected on the
backend via the system-wide `psutil.net_io_counters()` call (not the per-interface
variant) and surfaced through a new `/api/network` endpoint, with a corresponding
typed frontend client, a React Query polling hook, and dashboard components.

The feature follows the existing resource conventions: one thin router + one
service (which owns all psutil/system access) + one Pydantic model trio on the
backend, and a mirrored typed client + `useNetwork` hook + components on the
frontend. All sizes are reported in bytes and all rates in bytes per second;
the frontend formats these for display. Fields a host cannot provide, and rates
that cannot yet be computed, are nullable and degrade gracefully to an
"unavailable" state rather than causing an error.

### Scope Decision (Ahead of Roadmap)

The product roadmap scopes network monitoring to Phase 3, and the `/api/network`
endpoint is reserved there in the API contract. The owner has explicitly chosen
to build network throughput now, ahead of the phased roadmap. This spec is
recorded as a deliberate, out-of-phase addition. It reuses the Phase 1
architecture and conventions without restructuring existing modules, and it
introduces no speculative infrastructure for later phases.

### Technical Context Driving These Requirements

- **No persistence.** The product has no database and keeps state in memory
  only. `psutil.net_io_counters()` returns cumulative counters, not rates.
  Therefore download/upload rates MUST be derived by comparing two counter
  samples taken a measurable interval apart, with the previous sample held in
  memory between requests.
- **First-sample problem.** On the first request after the backend starts there
  is no prior sample, so no rate can be computed. Rate fields MUST be nullable
  and return null until a baseline sample exists.
- **Dual target, fail-soft.** On hosts where counters are unavailable (observed
  during macOS local development) the affected fields MUST be null and the
  endpoint MUST still return a valid response, matching the independent
  fail-soft reads in `system_metrics.py`.

## Glossary

- **Network_Service**: The backend service module that reads the system-wide
  network counters via `psutil.net_io_counters()`, derives rates from sampled
  counters held in memory, and returns typed data to the router.
- **Network_Router**: The thin FastAPI router exposing `GET /api/network` that
  validates/shapes the request and delegates to the Network_Service.
- **Network_Response**: The Pydantic model that defines the shape of the
  `/api/network` response and serves as the single source of truth for the API
  contract.
- **Aggregate_Throughput**: The system-wide totals of cumulative bytes and
  derived rates reported by `psutil.net_io_counters()`.
- **Cumulative_Bytes**: The total bytes sent (`bytes_sent`) and received
  (`bytes_recv`) reported by the host counters since boot.
- **Rate**: A derived value in bytes per second computed as the change in a
  cumulative counter divided by the elapsed seconds between two samples.
- **Counter_Sample**: A single system-wide point-in-time reading of the network
  counters together with the timestamp at which it was taken, retained in memory
  to compute the next Rate.
- **Network_Client**: The frontend typed API client function that calls
  `/api/network` and returns data typed to mirror Network_Response.
- **useNetwork**: The frontend React Query hook that polls `/api/network` on the
  dashboard polling interval.
- **Network_Component**: The frontend UI component(s) that render network
  throughput values and the "unavailable" state.

## Requirements

### Requirement 1: Network Throughput Endpoint

**User Story:** As the owner of the Pi, I want a network metrics endpoint, so
that the dashboard can display the server's download and upload activity.

#### Acceptance Criteria

1. THE Network_Router SHALL expose a GET endpoint at the path `/api/network`.
2. WHEN a request is received at `/api/network`, THE Network_Router SHALL delegate collection to the Network_Service and return the Network_Response produced by the Network_Service.
3. THE Network_Response SHALL be defined as a Pydantic model that is the single source of truth for the `/api/network` response shape, containing the Aggregate_Throughput only: cumulative bytes sent and cumulative bytes received as integers greater than or equal to 0 expressed in bytes, and a derived download Rate and upload Rate that are nullable.
4. WHERE an Aggregate_Throughput rate or byte value cannot be determined on the host, THE Network_Response SHALL represent that value as null so the frontend renders an "unavailable" state rather than failing.
5. THE Network_Router SHALL contain no metric-collection logic and SHALL delegate all network access to the Network_Service.
6. WHEN the Network_Service returns data, THE Network_Router SHALL respond with HTTP status 200 and a JSON body whose keys are snake_case and match the Network_Response Pydantic field names exactly.
7. IF the Network_Service fails to collect network data, THEN THE Network_Router SHALL respond with a server error status and an error indication, SHALL NOT return a partial or malformed 200 response, and SHALL leave no cached or partial state persisted.

### Requirement 2: Cumulative Byte Counters

**User Story:** As the owner of the Pi, I want to see total bytes sent and
received, so that I understand overall network usage since the server booted.

#### Acceptance Criteria

1. WHEN the Network_Response is built, THE Network_Service SHALL read cumulative bytes sent and cumulative bytes received from the host network counters via `psutil.net_io_counters()`.
2. THE Network_Response SHALL include Aggregate_Throughput containing cumulative bytes sent and cumulative bytes received as integer byte counts, each greater than or equal to 0 and less than 2^64, expressed in bytes.
3. WHILE the host network counters remain readable, THE Aggregate_Throughput cumulative byte counts SHALL be monotonically non-decreasing between consecutive readings except where the host counter wraps around or resets.
4. IF the host network counters cannot be read, THEN THE Network_Service SHALL set the Aggregate_Throughput cumulative byte counts to null and SHALL return a valid Network_Response from which the caller can observe the unavailable state.

### Requirement 3: Derived Download and Upload Rates

**User Story:** As the owner of the Pi, I want current download and upload
rates, so that I can see live network throughput on the dashboard.

#### Acceptance Criteria

1. THE Network_Service SHALL retain the most recent Counter_Sample in memory, consisting of the cumulative byte counters and a monotonic timestamp in seconds at which they were read.
2. WHEN a request is received and a previous Counter_Sample exists, THE Network_Service SHALL compute the download Rate and upload Rate as the change in the corresponding cumulative byte counter divided by the elapsed seconds, where elapsed seconds is the current monotonic timestamp minus the previous Counter_Sample timestamp as a floating-point value.
3. THE Network_Response SHALL express each derived Rate as a non-negative numeric value in bytes per second rounded to 2 decimal places.
4. WHEN a Rate has been computed, THE Network_Service SHALL replace the retained Counter_Sample with the current reading and timestamp before the Network_Response is returned.
5. IF no previous Counter_Sample exists, THEN THE Network_Service SHALL set the download Rate and upload Rate to null in the Network_Response and SHALL record the current reading as the Counter_Sample.
6. IF the elapsed seconds between the previous Counter_Sample and the current reading are less than or equal to zero, THEN THE Network_Service SHALL set the download Rate and upload Rate to null and SHALL record the current reading as the Counter_Sample.
7. IF a cumulative counter in the current reading is lower than the value in the previous Counter_Sample, THEN THE Network_Service SHALL set only that direction's Rate to null while still computing the other direction's Rate, and SHALL record the current reading as the Counter_Sample.

### Requirement 4: Aggregate Rate Totals

**User Story:** As the owner of the Pi, I want a single combined download and
upload rate, so that I can read overall throughput at a glance.

#### Acceptance Criteria

1. WHEN a request is received and the system-wide cumulative counters are available, THE Network_Service SHALL compute the Aggregate_Throughput download Rate and upload Rate from the system-wide cumulative byte counters using the rate rules defined in Requirement 3.
2. THE Network_Response SHALL include the Aggregate_Throughput download Rate and upload Rate as numeric values expressed in bytes per second, each present as a field whose value is either the computed rate or null.
3. IF no previous Counter_Sample exists for the system-wide counters, OR the elapsed seconds between the previous Counter_Sample and the current reading are less than or equal to zero, THEN THE Network_Service SHALL set both the Aggregate_Throughput download Rate and upload Rate to null.
4. IF a system-wide cumulative counter in the current reading is lower than the value in the previous Counter_Sample, OR that cumulative counter cannot be read, THEN THE Network_Service SHALL set the corresponding Aggregate_Throughput Rate to null independently of the other direction and SHALL return a valid Network_Response.

### Requirement 5: Fail-Soft Collection

**User Story:** As the owner of the Pi, I want the network endpoint to keep
working on any host, so that the dashboard runs the same on the Pi and on macOS
during development.

#### Acceptance Criteria

1. THE Network_Service SHALL perform each counter read as an independent operation so that the failure of one read does not prevent the remaining fields from being populated.
2. IF a counter read raises an error, THEN THE Network_Service SHALL set the affected field to null, SHALL leave an observable indication of the unavailable field, and SHALL continue collecting the remaining fields.
3. WHEN every network field is unavailable, THE Network_Router SHALL still respond with HTTP status 200 and a valid Network_Response in which the affected fields are null.

### Requirement 6: Typed Frontend Client

**User Story:** As a frontend developer, I want a typed client for the network
endpoint, so that the UI consumes the data with types that match the backend
contract.

#### Acceptance Criteria

1. THE Network_Client SHALL expose a function that requests `/api/network` and returns data typed to mirror the Network_Response field names and types.
2. THE Network_Client types SHALL declare every nullable Network_Response field as nullable.
3. WHEN the response to `/api/network` has a non-success HTTP status, THE Network_Client SHALL raise an error.
4. IF the response body to `/api/network` cannot be parsed as the expected shape, THEN THE Network_Client SHALL raise an error rather than returning malformed data.
5. THE Network_Client SHALL call `/api/network` only and SHALL NOT access the host or any system API directly.

### Requirement 7: Network Polling Hook

**User Story:** As the owner of the Pi, I want network metrics to refresh
automatically, so that the dashboard shows live throughput without manual
reloads.

#### Acceptance Criteria

1. THE useNetwork hook SHALL fetch network data from the `/api/network` resource through the Network_Client using React Query.
2. WHILE the useNetwork hook is mounted, THE useNetwork hook SHALL re-fetch network data on a recurring interval of 2500 milliseconds (within the permitted 2000-to-3000-millisecond range), including while the browser tab is in the background.
3. WHILE a re-fetch is in progress, THE useNetwork hook SHALL expose the most recently fetched successful data as placeholder data rather than an empty or null value.
4. WHILE no successful fetch has completed since mount, THE useNetwork hook SHALL expose a loading state and SHALL NOT expose network data values.
5. IF a fetch to `/api/network` fails, THEN THE useNetwork hook SHALL expose an error state, SHALL retain the most recently fetched successful data when such data exists, and SHALL retry the fetch at the recurring polling interval.

### Requirement 8: Dashboard Rendering and Unavailable State

**User Story:** As the owner of the Pi, I want download and upload throughput
shown on the dashboard, so that I can monitor network activity from my phone.

#### Acceptance Criteria

1. WHEN the Network_Component receives a non-null Aggregate_Throughput download Rate and upload Rate, THE Network_Component SHALL display each Rate converted from its byte-per-second value to a scaled unit selected so the displayed numeric value is at least 1 and less than 1000, shown with at most 2 decimal places and an accompanying per-second unit label.
2. WHEN the Network_Component receives a non-null Aggregate_Throughput cumulative bytes sent and bytes received, THE Network_Component SHALL display each value converted from its byte value to a scaled unit selected so the displayed numeric value is at least 1 and less than 1000, shown with at most 2 decimal places and an accompanying unit label.
3. WHERE a displayed Aggregate_Throughput value is null, THE Network_Component SHALL render a visible "unavailable" indicator in place of that single value while continuing to render all remaining non-null values.
4. IF the request for network data fails, THEN THE Network_Component SHALL render a visible "unavailable" indicator for the network values, SHALL keep the network section visible in the dashboard layout, and SHALL retain the most recently displayed values until replacement data is received.
5. WHEN a network data request succeeds after a prior failed request, THE Network_Component SHALL replace the "unavailable" indicator with the newly received Aggregate_Throughput values within one polling interval.
