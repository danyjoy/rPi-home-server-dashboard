# Requirements Document

## Introduction

The Home Server Command Center dashboard is mobile-first by product mandate, but
its current layout feels cramped and oversized on a phone: card padding, text
sizes, and the metric grid are tuned for wider screens. This feature refines the
responsive layout, spacing, and typography of the existing dashboard so it reads
comfortably on a phone while preserving the two- and three-column desktop
experience.

Scope is confined to presentation of the existing Phase 1 dashboard — sizing,
spacing, typography, the responsive grid, per-card column spanning, card
ordering, and a condensed sticky header. No new data, endpoints, or heavy
dependencies are introduced. Work stays within React + TypeScript + Tailwind CSS
with dark mode as the default theme.

## Glossary

- **Dashboard**: The React single-page view rendered by `Dashboard.tsx` that
  displays all system and storage metric cards.
- **Metric_Card**: A reusable card component (`MetricCard`) that frames a single
  metric with a title, optional status badge, and body content.
- **Prominent_Card**: A high-signal metric card, specifically the CPU and Memory
  cards.
- **Compact_Card**: A low-density stat card, specifically the Uptime, Load
  Average, and CPU Temp cards.
- **Stat_Header**: The dashboard header component (`StatHeader`) showing the
  title, hostname, and online status.
- **Small_Screen**: A viewport whose width is less than 640px (below the Tailwind
  `sm` breakpoint), representing the phone-first target.
- **Medium_Screen**: A viewport whose width is from 640px up to 1023px (Tailwind
  `sm` up to `lg`).
- **Large_Screen**: A viewport whose width is 1024px or greater (Tailwind `lg`
  and above), representing the desktop experience.
- **Metric_Grid**: The CSS grid container in `Dashboard.tsx` that lays out all
  metric cards.

## Requirements

### Requirement 1: Mobile-Appropriate Spacing and Typography

**User Story:** As a Pi owner viewing the dashboard on my phone, I want the metric cards to use mobile-appropriate spacing and typography, so that content feels comfortable rather than cramped or oversized.

#### Acceptance Criteria

1. WHILE the viewport width is within the Small_Screen range (320px to 639px inclusive), THE Dashboard SHALL render each Metric_Card with internal padding between 12px and 16px inclusive, and SHALL render the inter-card gap in the Metric_Grid between 8px and 16px inclusive.
2. WHILE the viewport width is within the Small_Screen range (320px to 639px inclusive), THE Dashboard SHALL render each Metric_Card padding and Metric_Grid inter-card gap at a value less than or equal to the corresponding value rendered at Large_Screen widths (>=1024px).
3. WHILE the viewport width is within the Small_Screen range (320px to 639px inclusive), THE Dashboard SHALL render primary metric values at a font size between 20px and 30px inclusive, and at a value less than or equal to the font size rendered for the same values at Large_Screen widths (>=1024px).
4. WHERE a Metric_Card displays a primary numeric value, THE Dashboard SHALL render that value on a single line with no character clipping and no horizontal overflow beyond the Metric_Card boundary at every viewport width from 320px to 639px inclusive.
5. IF a primary numeric value would exceed the Metric_Card width at a viewport width within the Small_Screen range (320px to 639px inclusive), THEN THE Dashboard SHALL reduce the rendered value to fit within the Metric_Card boundary while keeping it on a single line.
6. THE Dashboard SHALL apply all spacing and typography changes through Tailwind responsive utility classes only, without adding a CSS-in-JS library or any new runtime dependency.

### Requirement 2: Responsive Card Stacking and Ordering

**User Story:** As a Pi owner on a phone, I want cards to stack and pair in a sensible order, so that the most important metrics are easy to scan first.

#### Acceptance Criteria

1. WHILE the viewport width is less than 640px (Small_Screen), THE Dashboard SHALL render each Prominent_Card spanning 100% of the Metric_Grid content width.
2. WHILE the viewport width is less than 640px (Small_Screen), THE Metric_Grid SHALL arrange Compact_Cards exactly two per row, with any final odd Compact_Card spanning a single column and left-aligned in its row.
3. WHILE the viewport width is from 640px to 1023px inclusive (Medium_Screen), THE Metric_Grid SHALL display cards in exactly two equal-width columns.
4. WHILE the viewport width is 1024px or greater (Large_Screen), THE Metric_Grid SHALL display cards in exactly three equal-width columns.
5. THE Dashboard SHALL order cards in the Metric_Grid source order such that the CPU card is at position 1, the Memory card is at position 2, and all Compact_Cards (Uptime, Load Average, CPU Temp) follow at positions 3 and later.
6. WHERE one or more storage filesystems are present, THE Dashboard SHALL render each storage card using the same per-breakpoint column span behavior defined for a Prominent_Card in criteria 1, 3, and 4.
7. IF zero storage filesystems are present, THEN THE Dashboard SHALL render the Metric_Grid without any storage card and without reserving empty grid space, and SHALL preserve the card order defined in criterion 5.

### Requirement 3: Condensed Sticky Header

**User Story:** As a Pi owner scrolling a long dashboard on my phone, I want the header to stay accessible and compact, so that I always know the hostname and connection status without scrolling back to the top.

#### Acceptance Criteria

1. WHILE the viewport is a Small_Screen, THE Stat_Header SHALL remain fixed to the top of the viewport as the Dashboard content scrolls, such that the top edge of the Stat_Header stays at vertical offset 0 regardless of scroll position.
2. WHILE the Stat_Header is fixed during scroll, THE Stat_Header SHALL render an opaque (0% transparency) background that fully occludes any Dashboard content scrolling beneath it, leaving no scrolled content visible through the Stat_Header area.
3. THE Stat_Header SHALL display the hostname and the online status indicator at all supported viewport widths (Small_Screen <640px, Medium_Screen 640-1023px, and Large_Screen >=1024px).
4. IF the hostname text exceeds the available header width, THEN THE Stat_Header SHALL truncate the hostname text to the available width with a trailing ellipsis indicator and SHALL constrain the hostname to a single line, rather than wrapping to additional lines or overflowing the header bounds.
5. WHILE the viewport is a Small_Screen and the Dashboard is scrolled such that vertical scroll offset is greater than 0, THE Stat_Header SHALL render in a condensed state whose rendered height is no greater than 56 pixels.

### Requirement 4: Desktop Experience Preservation

**User Story:** As a Pi owner, I want the desktop dashboard to keep working well after the mobile refinements, so that improving the phone view does not degrade the larger-screen experience.

#### Acceptance Criteria

1. WHILE the viewport is a Large_Screen (>=1024px), THE Dashboard SHALL render the Metric_Grid as exactly three columns.
2. THE Dashboard SHALL apply dark mode as the default theme at all supported viewport widths from 320px up to 3840px inclusive, with no user action required to activate it.
3. THE Dashboard SHALL render all seven Phase 1 metric card types on every page load: CPU, Memory, CPU Temp, Uptime, Load Average, System information, and per-filesystem storage cards.
4. WHERE a metric value is unavailable, THE Dashboard SHALL render the unavailable-state indicator in place of that value such that the rendered content remains within its Metric_Card bounds, producing no horizontal scrollbar and no clipped or overlapping content, at all supported viewport widths from 320px to 3840px inclusive.
5. WHEN the viewport width transitions across the Small_Screen (<640px), Medium_Screen (640-1023px), and Large_Screen (>=1024px) breakpoints, THE Dashboard SHALL continue to render every metric card listed in criterion 3 without removing or hiding any card.
