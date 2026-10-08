import { statusPill, statusText, type Status } from "../lib/thresholds";

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusPill[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {statusText[status]}
    </span>
  );
}
