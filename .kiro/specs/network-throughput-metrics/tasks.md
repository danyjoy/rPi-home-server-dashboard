# Implementation Plan: Network Throughput Metrics

## Overview

This plan implements aggregate-only network throughput monitoring: cumulative
bytes sent/received plus derived download/upload rates (bytes per second),
exposed via `GET /api/network` and rendered on the dashboard.

The work follows the established resource pattern — one backend trio
(models → service → router) plus a single registration line in `main.py`,
then the mirrored frontend client → format helper → hook → components. The
network service is the first **stateful** service: it holds the last
`Counter_Sample` (aggregate counters + `time.monotonic()` timestamp) in memory
behind a `threading.Lock` and derives rates by comparing samples.

Tasks are ordered so each builds on the previous and ends by wiring into the
app. Testing is interleaved per the project's TDD-friendly approach. The pure
rate logic (`_derive_rate`) and the display formatters are exercised with
property-based tests (Properties 1-7); routing, wiring, typing, and UI are
covered by example/integration tests.

Convention anchors (from the design): the service mirrors the fail-soft
`_read_*` style of `app/services/system_metrics.py`; the router mirrors the thin
shape of `app/routers/system.py`; the frontend hook mirrors `src/hooks/useSystem.ts`;
`formatRate` reuses the 1024-scaling of the existing `formatBytes`; frontend
tests reuse the `frontend/src/test/` harness.

## Tasks

- [x] 1. Backend models — define the API contract
  - [x] 1.1 Create `backend/app/models/network.py`
    - Add `from __future__ import annotations` and import `BaseModel` from `pydantic`.
    - Define `AggregateThroughput` with snake_case fields: `bytes_sent: int | None`, `bytes_recv: int | None`, `download_rate_bps: float | None`, `upload_rate_bps: float | None`.
    - Define `NetworkResponse` with a single field `aggregate: AggregateThroughput`.
    - Use PascalCase model names; nullable fields as `X | None` (never `Optional`), matching existing models.
    - _Requirements: 1.3, 1.4, 2.2, 4.2_

- [x] 2. Backend service — stateful collection and pure rate logic
  - [x] 2.1 Implement the pure rate rule and sample container in `backend/app/services/network_metrics.py`
    - Add module docstring explaining this is the first stateful service and why the lock exists (do not remove it).
    - Define a `_Sample` dataclass (or typed tuple) holding `aggregate: tuple[int | None, int | None] | None` and `monotonic: float`.
    - Implement `_derive_rate(prev_bytes, cur_bytes, elapsed) -> float | None`: return `None` when there is no previous value, `elapsed <= 0`, the current counter is lower than the previous (reset/wrap), or either byte value is unreadable; otherwise return `round((cur_bytes - prev_bytes) / elapsed, 2)` (non-negative).
    - Keep `_derive_rate` a pure function of its arguments so it is directly property-testable.
    - _Requirements: 3.2, 3.3, 3.5, 3.6, 3.7, 4.1, 4.3, 4.4_

  - [ ]* 2.2 Write property test for the rate value rule
    - **Property 1: Rate equals delta over elapsed, non-negative, rounded**
    - **Validates: Requirements 3.2, 3.3, 4.1**
    - `hypothesis`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 1: Rate equals delta over elapsed, non-negative, rounded`.
    - Generate prev/cur counters with `cur >= prev` and `elapsed > 0`; assert `_derive_rate` equals `round((cur - prev) / elapsed, 2)` and is `>= 0`.

  - [ ]* 2.3 Write property test for the null conditions of the rate rule
    - **Property 2: Rate is null exactly under the defined conditions**
    - **Validates: Requirements 3.5, 3.6, 3.7, 4.4, 1.4, 2.4**
    - `hypothesis`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 2: Rate is null exactly under the defined conditions`.
    - Assert `_derive_rate` is `None` iff no previous sample, `elapsed <= 0`, current < previous, or a byte value is `None`; otherwise non-null. Confirm nulling one direction leaves the other computable.

  - [x] 2.4 Implement fail-soft counter read and `collect_network()` orchestration
    - Add module-level singleton sample and a module-level `threading.Lock`.
    - Implement `_read_aggregate() -> tuple[int | None, int | None]` wrapping `psutil.net_io_counters()` in its own `try/except`, returning `(None, None)` on failure (fail-soft, matching `system_metrics.py`); read `bytes_sent`/`bytes_recv` independently so one failing does not null the other.
    - Implement `collect_network() -> NetworkResponse`: acquire the lock; read current counters + `time.monotonic()`; derive download rate from `bytes_recv` and upload rate from `bytes_sent` against the retained sample; build `NetworkResponse`; **replace** the retained sample with the current reading only after a reading is obtained; release the lock; return.
    - On a total failure to obtain any reading, let the exception propagate (no partial 200) and do NOT mutate the retained sample.
    - Add a test seam so tests can inject consecutive readings and monotonic timestamps instead of calling real `psutil` (e.g. overridable `_read_aggregate` and a monotonic provider).
    - _Requirements: 1.4, 1.7, 2.1, 2.3, 2.4, 3.1, 3.4, 4.1, 4.2, 4.4, 5.1, 5.2_

  - [ ]* 2.5 Write property test for cumulative byte pass-through
    - **Property 3: Cumulative bytes are non-negative and passed through unchanged**
    - **Validates: Requirements 1.3, 2.2, 2.3**
    - `hypothesis`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 3: Cumulative bytes are non-negative and passed through unchanged`.
    - Inject readings in `[0, 2^64)`; assert response bytes equal the source reading unchanged; a failed read yields `null`.

  - [ ]* 2.6 Write property test for retained-sample update
    - **Property 4: The retained sample after a request equals the current reading**
    - **Validates: Requirements 3.1, 3.4**
    - `hypothesis`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 4: The retained sample after a request equals the current reading`.
    - After `collect_network()` obtains a reading, assert the retained sample's counters and monotonic timestamp equal the injected current reading.

  - [ ]* 2.7 Write property test for failed-collection sample integrity
    - **Property 5: A failed collection does not mutate the retained sample**
    - **Validates: Requirements 1.7**
    - `hypothesis`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 5: A failed collection does not mutate the retained sample`.
    - Seed an arbitrary retained sample; force the current reading to raise; assert `collect_network()` raises and the retained sample is unchanged.

  - [ ]* 2.8 Write property test for fail-soft field independence
    - **Property 6: Fail-soft field independence**
    - **Validates: Requirements 5.1, 5.2, 5.3**
    - `hypothesis`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 6: Fail-soft field independence`.
    - For any subset of reads forced to fail, assert non-failed fields are populated and only failed fields are `null`; all-fail yields a valid `NetworkResponse` with aggregate fields `null`.

  - [ ]* 2.9 Write example unit tests for rate edge cases
    - First-sample → both rates `null`, current recorded as sample (Req 3.5).
    - Counter reset in one direction → that direction `null`, other direction computed (Req 3.7, 4.4).
    - `elapsed <= 0` → both rates `null`, current recorded (Req 3.6).
    - Inject readings/monotonic time via the seam.
    - _Requirements: 3.5, 3.6, 3.7, 4.3, 4.4_

- [x] 3. Checkpoint - backend service
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Backend router and registration
  - [x] 4.1 Create `backend/app/routers/network.py`
    - Thin router mirroring `system.py`: `APIRouter(prefix="/api", tags=["network"])`.
    - `GET /network` with `response_model=NetworkResponse` delegating to `collect_network()` and returning its result unchanged.
    - No metric-collection logic and no `try/except` that would swallow a total failure into a partial 200.
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7_

  - [x] 4.2 Register the router in `backend/app/main.py`
    - Import `network` alongside `storage`, `system` and add `app.include_router(network.router)`.
    - This is the only core-wiring change; leave CORS (`allow_methods=["GET"]`) untouched.
    - _Requirements: 1.1_

  - [ ]* 4.3 Write router tests with FastAPI `TestClient`
    - `GET /api/network` returns 200 with the expected snake_case key set matching `NetworkResponse`/`AggregateThroughput` (Req 1.1, 1.2, 1.6).
    - All-reads-fail scenario returns 200 with an all-null aggregate (Req 5.3).
    - Forced total-collection failure returns a 5xx and emits no partial 200 (Req 1.7).
    - Patch `collect_network` to confirm the router passes its result through unchanged and holds no metric logic (Req 1.2, 1.5).
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7, 5.3_

- [x] 5. Checkpoint - backend endpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Frontend client and formatting
  - [x] 6.1 Add network types and client function in `frontend/src/api/client.ts`
    - Add `AggregateThroughput` and `NetworkResponse` TS interfaces mirroring the Pydantic models exactly, every nullable field as `| null`.
    - Add `getNetwork: () => getJson<NetworkResponse>("/api/network")` to the `api` object; reuse the existing `getJson` (throws on non-ok status and on unparseable JSON).
    - Do not add any direct host/system access; call `/api/network` only.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 6.2 Write client tests for `getNetwork`
    - Mock `fetch`: assert it requests `/api/network`, returns parsed data (Req 6.1), rejects on non-ok status (Req 6.3), and rejects on unparseable JSON (Req 6.4).
    - Reuse the `frontend/src/test/` harness.
    - _Requirements: 6.1, 6.3, 6.4_

  - [x] 6.3 Add `formatRate` in `frontend/src/lib/format.ts`
    - Implement `formatRate(bytesPerSec: number): string` reusing the `formatBytes` 1024-scaling and appending a `/s` suffix (e.g. `"1.2 MB/s"`).
    - Assume a non-null number (callers guard null); handle the zero/non-finite floor consistently with `formatBytes`.
    - _Requirements: 8.1_

  - [ ]* 6.4 Write property + example tests for `formatRate` / `formatBytes`
    - **Property 7: Display formatting scales into the readable band**
    - **Validates: Requirements 8.1, 8.2**
    - `fast-check`, min 100 iterations; tag `Feature: network-throughput-metrics, Property 7: Display formatting scales into the readable band`.
    - For positive inputs assert the numeric part is `>= 1` and `< 1000` with at most 2 decimals plus a unit label (`/s` for rate), except at the smallest-unit floor.
    - Add example cases: `0`, small values, GB/s scale, `/s` suffix.

- [x] 7. Frontend polling hook
  - [x] 7.1 Create `frontend/src/hooks/useNetwork.ts`
    - React Query hook templated on `useSystem.ts`: `queryKey: ["network"]`, `queryFn: api.getNetwork`, `refetchInterval: 2500`, `refetchIntervalInBackground: true`, `placeholderData: (prev) => prev`.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 7.2 Write hook tests for `useNetwork`
    - Render with a `QueryClientProvider` and mocked `api`; assert it calls `api.getNetwork`, exposes loading then data (Req 7.1, 7.4), retains placeholder data on refetch (Req 7.3), and surfaces an error state while retaining the last successful data and continuing to poll (Req 7.5), using fake timers to advance the 2500ms interval (Req 7.2).
    - Reuse the `frontend/src/test/` harness.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Dashboard rendering and wiring
  - [x] 8.1 Add the network section to `frontend/src/pages/Dashboard.tsx`
    - Consume `useNetwork`; add `MetricCard`(s) showing aggregate download rate, upload rate, cumulative bytes sent, and cumulative bytes received, using the existing `MetricCard` / `UsageBar` / `StatusBadge` / `Unavailable` pattern.
    - Format rates with `formatRate` and cumulative bytes with `formatBytes`; guard each value and render `<Unavailable />` in place of any null while sibling values still render (Req 8.3).
    - Keep the network section mounted when `network.isError` is true so retained `placeholderData` values stay on screen and a later success replaces them within one poll (Req 8.4, 8.5).
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 8.2 Write Dashboard network-section tests
    - Non-null values → formatted output shown (Req 8.1, 8.2).
    - One null value → `<Unavailable />` shown while siblings render (Req 8.3).
    - Error state → section stays mounted and last values retained (Req 8.4).
    - Error → success transition replaces the indicator within a poll (Req 8.5).
    - Reuse the `frontend/src/test/` harness.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Final checkpoint - full feature
  - Ensure all backend and frontend tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (test tasks) and can be skipped for a faster MVP; core implementation tasks are never optional.
- Each task references specific requirement sub-clauses (1-8) for traceability.
- Property-based tasks reference a specific design property (1-7); each runs a minimum of 100 iterations and carries the required `Feature: network-throughput-metrics, Property {n}: {text}` tag.
- The backend rate logic is tested by injecting readings and monotonic time through the service seam — no real network I/O in tests.
- Checkpoints provide incremental validation at the service, endpoint, and full-feature boundaries.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "6.1", "6.3"] },
    { "id": 3, "tasks": ["2.5", "2.6", "2.7", "2.8", "2.9", "4.1", "6.2", "6.4", "7.1"] },
    { "id": 4, "tasks": ["4.2", "7.2", "8.1"] },
    { "id": 5, "tasks": ["4.3", "8.2"] }
  ]
}
```
