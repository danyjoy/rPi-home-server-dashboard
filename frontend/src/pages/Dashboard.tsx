import { useSystem } from "../hooks/useSystem";
import { useStorage } from "../hooks/useStorage";
import { useNetwork } from "../hooks/useNetwork";
import { MetricCard } from "../components/MetricCard";
import { UsageBar } from "../components/UsageBar";
import { StatusBadge } from "../components/StatusBadge";
import { StatHeader } from "../components/StatHeader";
import { Unavailable } from "../components/Unavailable";
import {
  formatBytes,
  formatPercent,
  formatRate,
  formatTemperature,
  formatUptime,
} from "../lib/format";
import { temperatureStatus, usageStatus } from "../lib/thresholds";

export function Dashboard() {
  const system = useSystem();
  const storage = useStorage();
  const network = useNetwork();

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
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3 lg:gap-5">
          {/* CPU */}
          <MetricCard
            title="CPU"
            prominent
            action={<StatusBadge status={usageStatus(sys.cpu.usage_percent)} />}
          >
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <span className="shrink-0 whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
                {formatPercent(sys.cpu.usage_percent)}
              </span>
              <span className="min-w-0 truncate text-xs text-slate-400">
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
            prominent
            action={
              <StatusBadge status={usageStatus(sys.memory.used_percent)} />
            }
          >
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <span className="shrink-0 whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
                {formatPercent(sys.memory.used_percent)}
              </span>
              <span className="min-w-0 truncate text-xs text-slate-400">
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
              <span className="shrink-0 whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
                {formatTemperature(sys.temperature_celsius)}
              </span>
            ) : (
              <Unavailable label="No sensor" />
            )}
          </MetricCard>

          {/* Uptime */}
          <MetricCard title="Uptime">
            <span className="block shrink-0 whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
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
                <div key={label} className="min-w-0 text-center">
                  <div className="whitespace-nowrap text-xl font-bold sm:text-2xl lg:text-3xl">
                    {value.toFixed(2)}
                  </div>
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
              prominent
              action={<StatusBadge status={usageStatus(fs.used_percent)} />}
            >
              <div className="mb-2 flex items-baseline justify-between gap-2">
                <span className="shrink-0 whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
                  {formatPercent(fs.used_percent)}
                </span>
                <span className="min-w-0 truncate text-xs text-slate-400">
                  {fs.mount}
                </span>
              </div>
              <UsageBar percent={fs.used_percent} />
              <div className="mt-3 flex justify-between text-xs text-slate-400">
                <span>{formatBytes(fs.used_bytes)} used</span>
                <span>{formatBytes(fs.free_bytes)} free</span>
                <span>{formatBytes(fs.total_bytes)} total</span>
              </div>
            </MetricCard>
          ))}

          {/* Network */}
          {(() => {
            const net = network.data?.aggregate;
            return (
              <MetricCard title="Network" prominent>
                <div className="grid grid-cols-2 gap-3">
                  <div className="min-w-0">
                    <div className="text-xs text-slate-400">Download</div>
                    <div className="whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
                      {net && net.download_rate_bps !== null ? (
                        formatRate(net.download_rate_bps)
                      ) : (
                        <Unavailable />
                      )}
                    </div>
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs text-slate-400">Upload</div>
                    <div className="whitespace-nowrap text-xl font-bold text-slate-100 sm:text-2xl lg:text-3xl">
                      {net && net.upload_rate_bps !== null ? (
                        formatRate(net.upload_rate_bps)
                      ) : (
                        <Unavailable />
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-3 flex justify-between text-xs text-slate-400">
                  <span>
                    {net && net.bytes_recv !== null ? (
                      <>{formatBytes(net.bytes_recv)} received</>
                    ) : (
                      <Unavailable />
                    )}
                  </span>
                  <span>
                    {net && net.bytes_sent !== null ? (
                      <>{formatBytes(net.bytes_sent)} sent</>
                    ) : (
                      <Unavailable />
                    )}
                  </span>
                </div>
              </MetricCard>
            );
          })()}
        </div>
      )}
    </>
  );
}
