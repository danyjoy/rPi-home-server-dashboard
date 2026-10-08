# Implementation Plan: Mobile-Friendly Dashboard

## Overview

This is a frontend-only, presentation-layer refinement expressed through Tailwind
responsive utility classes plus one tiny dependency-free scroll hook. The plan
starts by adding the `prominent` span affordance and responsive padding to
`MetricCard`, adds the `useScrolled` hook, then rewires the `Dashboard` grid
(explicit 2-col base, per-card spans, fixed card order, responsive value
typography) and the sticky/condensed `StatHeader`. A test framework
(Vitest + React Testing Library + jsdom) is set up so unit/example tests,
property tests (fast-check), and fixed-viewport layout checks can validate the
four correctness properties and the acceptance criteria. The feature closes by
confirming the build passes with no new runtime dependency.

All implementation is in TypeScript + React + Tailwind, matching the existing
codebase.

## Tasks

- [x] 1. Add responsive padding and `prominent` span prop to `MetricCard`
  - Add an optional `prominent?: boolean` prop to the `MetricCardProps` interface
  - Apply responsive padding `p-3 sm:p-4` on the card container (12px small, 16px medium+)
  - When `prominent` is true, add span classes `col-span-2 lg:col-span-3`; otherwise no span class
  - Keep the existing border, background, rounding, and header-row markup intact
  - File: `frontend/src/components/MetricCard.tsx`
  - _Requirements: 1.1, 1.2, 1.6, 2.1, 2.6_

- [x] 2. Create the dependency-free `useScrolled` hook
  - [x] 2.1 Implement `useScrolled`
    - Create `frontend/src/hooks/useScrolled.ts` exporting `useScrolled(threshold = 0): boolean`
    - Initialize state SSR-guarded with `typeof window !== "undefined" && window.scrollY > threshold`
    - Register a passive `scroll` listener in `useEffect`, call once on mount, and clean up on unmount
    - Add no new runtime dependency (React only)
    - _Requirements: 1.6, 3.5_

  - [ ]* 2.2 Write unit tests for `useScrolled`
    - Test initial `false` at top, `true` after simulated `scrollY > threshold`, SSR-safe initial state, and listener cleanup
    - _Requirements: 3.5_

- [x] 3. Checkpoint - set up the frontend test framework
  - Add Vitest + React Testing Library + jsdom + fast-check as devDependencies in `frontend/package.json`
  - Add a `test` script (single-run, e.g. `vitest run`) and configure jsdom test environment in `vite.config.ts`
  - Add a test setup file registering `@testing-library/jest-dom` matchers
  - Confirm the harness runs with the existing `useScrolled` tests, ask the user if questions arise
  - _Requirements: 1.6_

- [x] 4. Rewire the `Dashboard` metric grid, card order, and value typography
  - [x] 4.1 Update the Metric_Grid container and per-card span flags
    - Set the grid container classes to `grid grid-cols-2 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3 lg:gap-5`
    - Mark CPU, Memory, and each storage card as `prominent`; leave Compact cards (CPU Temp, Uptime, Load Average, System) default single-column
    - Fix source order: CPU (1), Memory (2), then Compact cards, with storage cards appended last via `storage.data?.filesystems.map(...)`
    - Ensure zero filesystems renders no storage card and reserves no empty grid cell
    - File: `frontend/src/pages/Dashboard.tsx`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 4.1_

  - [x] 4.2 Make primary metric values responsive and non-clipping
    - Apply `whitespace-nowrap text-xl font-bold sm:text-2xl lg:text-3xl` to primary numeric values (CPU, Memory, Temp, Uptime, etc.)
    - Give the primary value `shrink-0` and its sibling secondary caption `min-w-0 truncate` so the caption truncates first and the value stays on one line
    - Preserve the existing `Unavailable` substitution for nullable fields (temperature, host model)
    - File: `frontend/src/pages/Dashboard.tsx`
    - _Requirements: 1.3, 1.4, 1.5, 4.3, 4.4_

  - [ ]* 4.3 Write property test for storage-card prominent span
    - **Feature: mobile-friendly-dashboard, Property 1: Storage cards receive prominent (full-width) span behaviour**
    - **Validates: Requirements 2.6, 2.7**
    - fast-check over arbitrary filesystem arrays (including empty); assert one card per filesystem, each carrying `col-span-2 lg:col-span-3`, none when empty; minimum 100 iterations
    - _Requirements: 2.6, 2.7_

  - [ ]* 4.4 Write property test for card-set invariance across widths
    - **Feature: mobile-friendly-dashboard, Property 4: The rendered card set is invariant across viewport width**
    - **Validates: Requirements 4.3, 4.5**
    - fast-check over viewport widths (Small/Medium/Large) with full data + >=1 filesystem; assert all seven card types present and no card carries `hidden`/`sm:hidden`/`lg:hidden`; minimum 100 iterations
    - _Requirements: 4.3, 4.5_

  - [ ]* 4.5 Write property test for unavailable-field substitution
    - **Feature: mobile-friendly-dashboard, Property 3: Unavailable fields render the unavailable indicator in place**
    - **Validates: Requirements 4.4**
    - fast-check over nullable-field combinations (`temperature_celsius`, `host.model`, subsets); assert `Unavailable` renders in place and no raw `null`/`undefined`/`NaN` reaches the card body while other cards render; minimum 100 iterations
    - _Requirements: 4.4_

  - [ ]* 4.6 Write unit/example tests for card ordering and presence
    - Assert source order CPU, Memory, then Compact cards, storage last; all seven card types present on load; no width-conditional hidden utilities on any card
    - _Requirements: 2.5, 4.3, 4.5_

- [x] 5. Make `StatHeader` sticky and condensed
  - [x] 5.1 Apply sticky/opaque/condensed classes and hostname truncation
    - Consume `useScrolled()` to drive the condensed state
    - Apply `sticky top-0 z-20` with full-width occlusion via `-mx-4 px-4 sm:-mx-6 sm:px-6` and opaque `bg-slate-950`
    - Condensed when scrolled: `py-2` + smaller title (`text-base`), expanded otherwise (`py-3 sm:py-4`), keeping height <= 56px when scrolled
    - Render hostname as a single-line `truncate` element inside a `min-w-0` parent; render hostname and online indicator unconditionally at all widths
    - File: `frontend/src/components/StatHeader.tsx`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 5.2 Write property test for hostname truncation
    - **Feature: mobile-friendly-dashboard, Property 2: Hostname is always clamped to a single truncating line**
    - **Validates: Requirements 3.4**
    - fast-check over arbitrary hostname strings; assert the hostname element carries `truncate` and its flex parent carries `min-w-0`; minimum 100 iterations
    - _Requirements: 3.4_

  - [ ]* 5.3 Write unit tests for sticky/condensed header behaviour
    - Assert `sticky top-0 z-20` and opaque `bg-slate-950` present; condensed classes applied when scrolled and expanded when at top; hostname and online indicator always rendered
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ]* 6. Add fixed-viewport layout checks
  - At representative widths (320px, 639px, 768px, 1280px) assert padding/gap/font-size bands (Req 1.1-1.5), grid column counts (2.3, 2.4, 4.1), and sticky/opaque/condensed header outcomes (3.1, 3.2, 3.5) via computed styles
  - Confirm worst-case value strings (`100.0%`, `365d 23h 59m`, `-10.0°C`) stay single-line within card bounds at 320px (Req 1.4, 4.4)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.3, 2.4, 3.1, 3.2, 3.5, 4.1, 4.4_

- [x] 7. Final checkpoint - verify build and dependency integrity
  - Run the build (`tsc --noEmit && vite build`) and confirm it passes with no type errors
  - Confirm `package.json` runtime `dependencies` are unchanged (no CSS-in-JS or other new runtime dependency; test tooling is devDependencies only) (Req 1.6)
  - Confirm dark theme renders on initial load with no user action (Req 4.2)
  - Ensure all tests pass, ask the user if questions arise
  - _Requirements: 1.6, 4.2_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP (all are test tasks).
- Each task references specific requirements for traceability.
- Property tests validate the four universal correctness properties from the design; each runs a minimum of 100 iterations with the tag format "Feature: mobile-friendly-dashboard, Property N: …".
- jsdom cannot measure real layout, so overflow/pixel-band assertions live in the fixed-viewport layout checks (task 6), while class-assignment logic is covered by property and unit tests.
- Checkpoints (tasks 3, 7) ensure the test harness and build stay green incrementally.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2.1"] },
    { "id": 1, "tasks": ["2.2", "4.1", "5.1"] },
    { "id": 2, "tasks": ["4.2", "5.2", "5.3"] },
    { "id": 3, "tasks": ["4.3", "4.4", "4.5", "4.6"] },
    { "id": 4, "tasks": ["6"] }
  ]
}
```
