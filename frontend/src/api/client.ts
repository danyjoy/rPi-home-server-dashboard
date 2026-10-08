// Typed API client. These types mirror the backend Pydantic models exactly
// (see .kiro/steering/api-contract.md). Keep them in sync.

export interface CpuInfo {
  usage_percent: number;
  per_core: number[];
  core_count: number;
}

export interface MemoryInfo {
  total_bytes: number;
  used_bytes: number;
  available_bytes: number;
  used_percent: number;
}

export interface LoadAverage {
  one: number;
  five: number;
  fifteen: number;
}

export interface HostInfo {
  model: string | null;
  os: string;
  hostname: string;
}

export interface SystemResponse {
  cpu: CpuInfo;
  memory: MemoryInfo;
  temperature_celsius: number | null;
  uptime_seconds: number;
  load_average: LoadAverage;
  host: HostInfo;
}

export interface FilesystemUsage {
  name: string;
  mount: string;
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  used_percent: number;
}

export interface StorageResponse {
  filesystems: FilesystemUsage[];
}

export interface AggregateThroughput {
  bytes_sent: number | null;
  bytes_recv: number | null;
  download_rate_bps: number | null;
  upload_rate_bps: number | null;
}

export interface NetworkResponse {
  aggregate: AggregateThroughput;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  getSystem: () => getJson<SystemResponse>("/api/system"),
  getStorage: () => getJson<StorageResponse>("/api/storage"),
  getNetwork: () => getJson<NetworkResponse>("/api/network"),
};
