# Design Document

## Overview

This feature is a frontend-only, presentation-layer refinement of the existing
Phase 1 dashboard. It makes the dashboard read comfortably on a phone (the
product's mobile-first mandate) while preserving the two- and three-column
desktop experience. No data, endpoints, or runtime dependencies change.

The work is expressed entirely through Tailwind responsive utility classes
within the existing component boundaries (`Dashboard.tsx`, `App.tsx`,
`MetricCard.tsx`, `StatHeader.tsx`). Dark mode remains the default theme. The
only structural additions are:

1. Per-card column-span classes applied in `Dashboard.tsx` so Prominent and
   storage cards go full-width on phones.
2. A `prominent` boolean prop on `MetricCard` so the "span the full grid width"
   decision lives with the card call site, not in ad-hoc wrapper divs.
3. Sticky-header classes plus a `scrolled` affordance on `StatHeader`.
4. A tiny, dependency-free scroll hook (`useScrolled`) to drive the condensed
   header state on small screens. This is the one permitted layout helper; it
   is a handful of lines and avoids adding any library.

### Breakpoint model

The design maps directly onto Tailwind's default breakpoints, which already
match the requirements glossary:

| Range name    | Width            | Tailwind prefix | Grid columns |
| ------------- | ---------------- | --------------- | ------------ |
| Small_Screen  | `< 640px`        | (base / none)   | effectively 2-col grid for packing, Prominent spans both |
| Medium_Screen | `640–1023px`     | `sm:`           | 2 columns    |
| Large_Screen  | `>= 1024px`      | `lg:`           | 3 columns    |

A key decision: the base (small-screen) grid uses **two columns**, not one.
Compact cards occupy one column each (packing two-per-row, Req 2.2) and
Prominent/storage cards span both columns (full width, Req 2.1/2.6). This single
grid definition satisfies all three breakpoint column counts without
JavaScript-driven layout.

## Architecture

### Component responsibilities (unchanged boundaries)

```
App.tsx                      container width + page padding (max-w-5xl)
└── Dashboard.tsx            grid definition, card ordering, per-card span flags
    ├── StatHeader.tsx       sticky/condensed header, hostname truncation
    └── MetricCard.tsx       card frame; responsive padding; prominent span
        ├── UsageBar.tsx     (unchanged)
        ├── StatusBadge.tsx  (unchanged)
        └── Unavailable.tsx  (unchanged)
lib/
└── hooks/useScrolled.ts     NEW: tiny scroll-position hook for condensed header
```

### Data flow

No change. `useSystem` / `useStorage` (React Query polling) continue to supply
`SystemResponse` and `StorageResponse`. This feature only alters how that data
is laid out and sized. The `useScrolled` hook reads `window.scrollY` via a
passive scroll listener and returns a boolean; it carries no server data.

## Components and Interfaces

### 1. Grid definition (`Dashboard.tsx`)

The grid container becomes an explicit two-column base grid that widens at
breakpoints. Full-width cards span both base columns and both medium columns,
and span across the three large columns.

```tsx
// Grid container
<div className="grid grid-cols-2 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3 lg:gap-5">
  {/* Prominent + storage cards get prominent (full-width) span */}
  {/* Compact cards get the default single-column span */}
</div>
```

Span strategy, centralised on `MetricCard` via a `prominent` prop:

- **Prominent / storage card** → `col-span-2 lg:col-span-3`
  - small: spans both of the 2 base columns = 100% width (Req 2.1, 2.6)
  - medium: spans both `sm` columns = 100% width (Req 2.6/1 at medium is the
    prominent behaviour, matching criteria reference)
  - large: spans all 3 columns = 100% width (Req 2.6)
- **Compact card** → default (single column)
  - small: 1 of 2 columns → packs two-per-row; a 3rd card lands left-aligned in
    a new row (Req 2.2)
  - medium: 1 of 2 columns (Req 2.3)
  - large: 1 of 3 columns (Req 2.4)

> Note on criteria 2.3/2.4: these require the overall grid to be exactly two
> columns at medium and exactly three at large. Compact cards (single span)
> realise those counts directly. Prominent/storage cards intentionally span the
> full row at every breakpoint — this is the explicit "Prominent_Card" behaviour
> that criteria 1, 3, and 4 of Req 2 reference for storage, so a full-width CPU
> or storage card on a 3-column desktop is by design, while the compact cards
> still demonstrate the exact 2-/3-column track counts.

### Card ordering (Req 2.5)

Source order in `Dashboard.tsx` is fixed and explicit:

1. CPU (prominent)
2. Memory (prominent)
3. CPU Temp (compact)
4. Uptime (compact)
5. Load Average (compact)
6. System (compact / info)
7. Storage · <fs> … (prominent, one per filesystem, appended last)

Ordering is intrinsic to JSX child order and does not depend on viewport.

### 2. `MetricCard` interface change

Add an optional `prominent` flag. The card owns both its responsive padding and
its grid span, keeping the span decision co-located with the card.

```tsx
interface MetricCardProps {
  title: string;
  icon?: ReactNode;
  action?: ReactNode;
  prominent?: boolean; // NEW: full-width across all breakpoints
  children: ReactNode;
}

export function MetricCard({ title, icon, action, prominent = false, children }: MetricCardProps) {
  const span = prominent ? "col-span-2 lg:col-span-3" : "";
  return (
    <div
      className={`rounded-2xl border border-slate-800 bg-slate-900/60 p-3 shadow-lg shadow-black/20 backdrop-blur sm:p-4 ${span}`}
    >
      <div className="mb-2 flex items-center justify-between gap-2 sm:mb-3">
        <div className="flex items-center gap-2 text-slate-300">
          {icon}
          <h2 className="text-xs font-semibold uppercase tracking-wide sm:text-sm">
            {title}
          </h2>
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}
```

Responsive padding: `p-3` (12px) at small, `p-4` (16px) at medium+ — small ≤
large and inside the 12–16px band (Req 1.1, 1.2).

### Primary value typography (Req 1.3, 1.4, 1.5)

Primary numeric values currently use `text-3xl` (30px). They become responsive
and non-wrapping:

```tsx
<span className="whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
  {formatPercent(sys.cpu.usage_percent)}
</span>
```

- small: `text-xl` = 20px (within 20–30px band, Req 1.3)
- large: `text-3xl` = 30px (small ≤ large, Req 1.3)
- `whitespace-nowrap` keeps values on a single line (Req 1.4)
- The longest expected values (`100.0%`, a long uptime like `365d 23h 59m`, a
  temperature like `-10.0°C`) fit within a half-width (two-up) compact card at
  320px at `text-xl`; where a value lives in a compact card we also allow the
  value cell to shrink its siblings (the secondary caption) so the primary value
  is never clipped (Req 1.5). The Load Average card already lays its three
  values out responsively and keeps `text-xl` at small.

To guarantee Req 1.5 without a measurement library, the secondary caption next
to a primary value (e.g. "4 cores", "used / total") is given `min-w-0 truncate`
and the primary value keeps `whitespace-nowrap shrink-0`, so when space is
tight the caption truncates first and the value stays intact on one line.

### 3. `StatHeader` — sticky + condensed (Req 3)

The header becomes sticky to the top with an opaque background and a condensed
state once the page is scrolled on small screens.

```tsx
interface StatHeaderProps {
  hostname: string;
  online: boolean;
  updating: boolean;
}

export function StatHeader({ hostname, online, updating }: StatHeaderProps) {
  const scrolled = useScrolled(); // true when window.scrollY > 0

  return (
    <header
      className={[
        // sticky to top at all widths; top edge pinned at offset 0 (Req 3.1)
        "sticky top-0 z-20 -mx-4 flex items-center justify-between gap-3 px-4 sm:-mx-6 sm:px-6",
        // fully opaque background occludes scrolled content (Req 3.2)
        "bg-slate-950",
        // condensed when scrolled: height stays <= 56px (Req 3.5)
        scrolled ? "border-b border-slate-800 py-2" : "py-3 sm:py-4",
      ].join(" ")}
    >
      <div className="min-w-0">
        <h1
          className={`truncate font-bold text-slate-100 ${
            scrolled ? "text-base" : "text-xl sm:text-2xl"
          }`}
        >
          Command Center
        </h1>
        {/* hostname: single line, ellipsis on overflow (Req 3.4) */}
        <p className="truncate text-sm text-slate-400">{hostname}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${online ? "bg-healthy" : "bg-critical"} ${
            updating ? "animate-pulse" : ""
          }`}
        />
        <span className="text-sm text-slate-400">{online ? "Online" : "Offline"}</span>
      </div>
    </header>
  );
}
```

Design notes:

- **Sticky, offset 0 (Req 3.1):** `sticky top-0` keeps the header's top edge at
  the viewport top as content scrolls. `sticky` is used rather than `fixed` so
  the header still participates in flow and reserves its own space, avoiding a
  content-jump; its top edge is pinned at 0 which satisfies the stated behaviour.
  `z-20` keeps it above cards.
- **Opaque background (Req 3.2):** `bg-slate-950` is a fully opaque colour (no
  `/opacity` suffix, no `backdrop-blur` on the header), so scrolled content is
  fully occluded. The negative margins + matching padding (`-mx-4 px-4`) make the
  opaque bar span the full container width so nothing shows through at the edges.
- **Hostname truncation (Req 3.4):** the hostname `<p>` keeps `truncate`
  (`overflow-hidden text-ellipsis whitespace-nowrap`) and its parent has
  `min-w-0`, so any length hostname is clamped to one line with an ellipsis and
  never wraps or overflows the header.
- **Condensed height (Req 3.5):** when `scrolled`, padding drops to `py-2`
  (8px top+bottom) and the title to `text-base`; title line-height (~24px) +
  hostname line (~20px) + 16px padding ≈ 48px ≤ 56px.
- **Always-visible status (Req 3.3):** hostname and the online indicator are
  rendered unconditionally at every width — no responsive `hidden` utilities.

### 4. `useScrolled` hook (new, dependency-free)

The single permitted helper. It exists solely to toggle the condensed header
state; it adds no runtime dependency (Req 1.6).

```ts
// frontend/src/hooks/useScrolled.ts
import { useEffect, useState } from "react";

// Returns true once the window has scrolled past the top. Passive listener;
// no external dependency. Drives the condensed Stat_Header state.
export function useScrolled(threshold = 0): boolean {
  const [scrolled, setScrolled] = useState(
    () => typeof window !== "undefined" && window.scrollY > threshold,
  );

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > threshold);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [threshold]);

  return scrolled;
}
```

### 5. `App.tsx` container

Unchanged in intent (`max-w-5xl` centred, dark background). The header's
negative-margin trick relies on the existing `px-4 sm:px-6` padding on the
container, so no change is required there. The `py-5` wrapper padding stays; the
sticky header sits at the top of that padded column.

## Data Models

No API or data-model changes. The TypeScript response types in
`frontend/src/api/client.ts` remain the single mirror of the Pydantic models.
The only new type surface is the local `prominent?: boolean` prop on
`MetricCard` and the `useScrolled` return value (`boolean`).

## Error Handling

Presentation-layer only; existing behaviour is preserved and must not regress:

- **Backend unreachable:** the existing error banner and `online=false` state in
  `StatHeader` are unchanged. The banner continues to render above the grid.
- **Loading:** the "Loading metrics…" placeholder is unchanged.
- **Unavailable metric values (Req 4.4):** nullable fields
  (`temperature_celsius`, `host.model`) continue to render the `Unavailable`
  component in place of the value. With the new responsive sizing, the
  `Unavailable` label (`text-sm`) is shorter than any numeric value, so it
  cannot cause overflow; it stays within card bounds at every width.
- **Zero filesystems (Req 2.7):** `storage.data?.filesystems.map(...)` already
  renders nothing when the array is empty — no storage card and no reserved grid
  cell (grid auto-flow leaves no gap for absent children). Non-storage card order
  is preserved.
- **SSR / no `window`:** `useScrolled` guards `typeof window` in its initial
  state so it is safe even though this app is client-rendered by Vite.

## Testing Strategy

Dual approach, scaled to a presentation feature:

- **Unit / example tests (React Testing Library + jsdom):** card ordering,
  presence of all seven card types, unavailable-field substitution, and that no
  card carries width-conditional hidden utilities. These assert the rendered DOM
  structure and emitted class names, which is reliable in jsdom.
- **Property tests (fast-check):** the universal invariants below — storage-card
  span assignment over variable filesystem arrays, hostname truncation classes
  over arbitrary hostnames, unavailable substitution over nullable-field
  combinations, and card-set invariance. These validate our class-assignment and
  substitution logic without needing a layout engine. Minimum 100 iterations
  each.
- **Layout / visual checks (integration, representative widths only):** pixel
  bands for padding, gap, and font size (Req 1.1–1.5), grid column counts (2.3,
  2.4, 4.1), and sticky/condensed/opaque header behaviour (3.1, 3.2, 3.5) are
  layout outcomes of static Tailwind classes. These are verified at a few fixed
  viewport widths (e.g. 320px, 639px, 768px, 1280px) via computed styles in a
  browser-capable runner, not through randomised property tests. jsdom cannot
  measure real layout/overflow, so overflow assertions (1.4, 4.4) are confirmed
  with a small set of worst-case value strings at 320px.
- **Smoke / build checks:** `package.json` runtime dependencies unchanged and no
  CSS-in-JS import introduced (Req 1.6); dark theme active on initial render with
  no user action (Req 4.2).

Property test tag format: **Feature: mobile-friendly-dashboard, Property N: …**,
minimum 100 iterations per property.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all
valid executions of a system — essentially, a formal statement about what the
system should do. Properties serve as the bridge between human-readable
specifications and machine-verifiable correctness guarantees.*

### Property 1: Storage cards receive prominent (full-width) span behaviour

*For any* list of storage filesystems (including the empty list), the Dashboard
renders exactly one storage card per filesystem, and every rendered storage card
carries the same full-width grid-span class set applied to the Prominent CPU and
Memory cards (`col-span-2 lg:col-span-3`); when the list is empty, no storage
card is rendered and no empty grid cell is reserved.

**Validates: Requirements 2.6, 2.7**

### Property 2: Hostname is always clamped to a single truncating line

*For any* hostname string (any length, any characters), the Stat_Header renders
the hostname inside a single-line truncating element (`truncate`, i.e.
`overflow-hidden text-ellipsis whitespace-nowrap`) whose flex parent carries
`min-w-0`, so the hostname never wraps to additional lines and never overflows
the header bounds.

**Validates: Requirements 3.4**

### Property 3: Unavailable fields render the unavailable indicator in place

*For any* combination of nullable metric fields set to unavailable
(`temperature_celsius`, `host.model`, and any subset thereof), the Dashboard
renders the `Unavailable` indicator in place of each unavailable value and never
emits a raw `null`, `undefined`, or `NaN` into the card body, while all other
cards continue to render their values.

**Validates: Requirements 4.4**

### Property 4: The rendered card set is invariant across viewport width

*For any* viewport width across the Small, Medium, and Large ranges, given a full
set of system data and at least one filesystem, the Dashboard renders the same
complete set of cards (CPU, Memory, CPU Temp, Uptime, Load Average, System, and
one card per filesystem) with no card hidden or removed, and no card carries a
width-conditional display-toggling utility (e.g. `hidden`, `sm:hidden`,
`lg:hidden`).

**Validates: Requirements 4.3, 4.5**
