interface StatHeaderProps {
  hostname: string;
  online: boolean;
  updating: boolean;
}

export function StatHeader({ hostname, online, updating }: StatHeaderProps) {
  return (
    <header className="mb-5 flex items-center justify-between gap-3">
      <div className="min-w-0">
        <h1 className="truncate text-xl font-bold text-slate-100 sm:text-2xl">
          Command Center
        </h1>
        <p className="truncate text-sm text-slate-400">{hostname}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            online ? "bg-healthy" : "bg-critical"
          } ${updating ? "animate-pulse" : ""}`}
        />
        <span className="text-sm text-slate-400">
          {online ? "Online" : "Offline"}
        </span>
      </div>
    </header>
  );
}
