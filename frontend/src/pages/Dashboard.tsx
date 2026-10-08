import { useSystem } from "../hooks/useSystem";
import { useStorage } from "../hooks/useStorage";
import { MetricCard } from "../components/MetricCard";
import { UsageBar } from "../components/UsageBar";
import { StatusBadge } from "../components/StatusBadge";
import { StatHeader } from "../components/StatHeader";
import { Unavailable } from "../components/Unavailable";
import {
  formatBytes,
  formatPercent,
  formatTemperature,
  formatUptime,
} from "../lib/format";
import { temperatureStatus, usageStatus } from "../lib/thresholds";

export function Dashboard() {
  const system = useSystem();
  const storage = useStorage();

  const sys = system.data;
  const online = !system.isError;
  const hostname = sys?.host.hostname ?? "home-server";

  return (
    <>
      <StatHeader
        hostname={hostname}
        online={online}
        updating={system.isFetching}
      />

      {system.isError && (
        <div className="mb-5 rounded-xl border border-critical/40 bg-critical/10 p-4 text-sm text-critical">
          Can't reach the backend. Retrying automatically…
        </div>
      )}

      {!sys ? (
        <p className="text-slate-400">Loading metrics…</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* CPU */}
          <MetricCard
            title="CPU"
            action={<StatusBadge status={usageStatus(sys.cpu.usage_percent)} />}
          >
            <div className="mb-2 flex items-baseline justify-between">
              <span className="text-3xl font-bold text-slate-100">
                {formatPercent(sys.cpu.usage_percent)}
              </span>
              <span className="text-xs text-slate-400">
                {sys.cpu.core_count} cores
              </span>
            </div>
            <UsageBar percent={sys.cpu.usage_percent} />
            {sys.cpu.per_core.length > 0 && (
              <div className="mt-3 grid grid-cols-4 gap-1.5">
                {sys.cpu.per_core.map((core, i) => (
                  <UsageBar key={i} percent={core} compact />
                ))}
              </div>
            )}
          </MetricCard>

          {/* Memory */}
          <MetricCard
            title="Memory"
            action={
              <StatusBadge status={usageStatus(sys.memory.used_percent)} />
            }
          >
            <div className="mb-2 flex items-baseline justify-between">
              <span className="text-3xl font-bold text-slate-100">
                {formatPercent(sys.memory.used_percent)}
              </span>
              <span className="text-xs text-slate-400">
                {formatBytes(sys.memory.used_bytes)} /{" "}
                {formatBytes(sys.memory.total_bytes)}
              </span>
            </div>
            <UsageBar percent={sys.memory.used_percent} />
          </MetricCard>

          {/* Temperature */}
          <MetricCard
            title="CPU Temp"
            action={
              sys.temperature_celsius !== null ? (
                <StatusBadge
                  status={temperatureStatus(sys.temperature_celsius)}
                />
              ) : undefined
            }
          >
            {sys.temperature_celsius !== null ? (
              <span className="text-3xl font-bold text-slate-100">
                {formatTemperature(sys.temperature_celsius)}
              </span>
            ) : (
              <Unavailable label="No sensor" />
            )}
          </MetricCard>

          {/* Uptime */}
          <MetricCard title="Uptime">
            <span className="text-3xl font-bold text-slate-100">
              {formatUptime(sys.uptime_seconds)}
            </span>
          </MetricCard>

          {/* Load average */}
          <MetricCard title="Load Average">
            <div className="flex items-center justify-between gap-2 text-slate-100">
              {(
                [
                  ["1m", sys.load_average.one],
                  ["5m", sys.load_average.five],
                  ["15m", sys.load_average.fifteen],
                ] as const
              ).map(([label, value]) => (
                <div key={label} className="text-center">
                  <div className="text-2xl font-bold">{value.toFixed(2)}</div>
                  <div className="text-xs text-slate-400">{label}</div>
                </div>
              ))}
            </div>
          </MetricCard>

          {/* System info */}
          <MetricCard title="System">
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-3">
                <dt className="text-slate-400">Model</dt>
                <dd className="text-right text-slate-200">
                  {sys.host.model ?? <Unavailable />}
                </dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-400">OS</dt>
                <dd className="text-right text-slate-200">{sys.host.os}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-slate-400">Host</dt>
                <dd className="text-right text-slate-200">
                  {sys.host.hostname}
                </dd>
              </div>
            </dl>
          </MetricCard>

          {/* Storage */}
          {storage.data?.filesystems.map((fs) => (
            <MetricCard
              key={fs.name}
              title={`Storage · ${fs.name}`}
              action={<StatusBadge status={usageStatus(fs.used_percent)} />}
            >
              <div className="mb-2 flex items-baseline justify-between">
                <span className="text-3xl font-bold text-slate-100">
                  {formatPercent(fs.used_percent)}
                </span>
                <span className="text-xs text-slate-400">{fs.mount}</span>
              </div>
              <UsageBar percent={fs.used_percent} />
              <div className="mt-3 flex justify-between text-xs text-slate-400">
                <span>{formatBytes(fs.used_bytes)} used</span>
                <span>{formatBytes(fs.free_bytes)} free</span>
                <span>{formatBytes(fs.total_bytes)} total</span>
              </div>
            </MetricCard>
          ))}
        </div>
      )}
    </>
  );
}
