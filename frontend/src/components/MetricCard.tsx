import type { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  icon?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
}

export function MetricCard({ title, icon, action, children }: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-lg shadow-black/20 backdrop-blur">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-slate-300">
          {icon}
          <h2 className="text-sm font-semibold uppercase tracking-wide">
            {title}
          </h2>
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}
