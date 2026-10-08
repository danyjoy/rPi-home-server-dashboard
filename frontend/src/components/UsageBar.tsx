import { statusBar, usageStatus } from "../lib/thresholds";

interface UsageBarProps {
  percent: number;
  // Optional override; by default color is derived from usage thresholds.
  compact?: boolean;
}

export function UsageBar({ percent, compact = false }: UsageBarProps) {
  const clamped = Math.max(0, Math.min(100, percent));
  const status = usageStatus(clamped);
  return (
    <div
      className={`w-full overflow-hidden rounded-full bg-slate-800 ${
        compact ? "h-1.5" : "h-2.5"
      }`}
    >
      <div
        className={`h-full rounded-full transition-all duration-500 ${statusBar[status]}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
