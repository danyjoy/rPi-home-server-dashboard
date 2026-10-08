// Shared healthy / warning / critical logic. Values match the thresholds in
// .kiro/steering/api-contract.md. This is the single source of truth for the UI.

export type Status = "healthy" | "warning" | "critical";

// Usage percent (CPU, RAM, disk): <70 healthy, 70-89 warning, >=90 critical.
export function usageStatus(percent: number): Status {
  if (percent >= 90) return "critical";
  if (percent >= 70) return "warning";
  return "healthy";
}

// CPU temperature (°C): <60 healthy, 60-74 warning, >=75 critical.
export function temperatureStatus(celsius: number): Status {
  if (celsius >= 75) return "critical";
  if (celsius >= 60) return "warning";
  return "healthy";
}

export const statusText: Record<Status, string> = {
  healthy: "Healthy",
  warning: "Warning",
  critical: "Critical",
};

// Tailwind utility fragments per status, kept here so components stay consistent.
export const statusBar: Record<Status, string> = {
  healthy: "bg-healthy",
  warning: "bg-warning",
  critical: "bg-critical",
};

export const statusAccent: Record<Status, string> = {
  healthy: "text-healthy",
  warning: "text-warning",
  critical: "text-critical",
};

export const statusPill: Record<Status, string> = {
  healthy: "bg-healthy/15 text-healthy ring-1 ring-healthy/30",
  warning: "bg-warning/15 text-warning ring-1 ring-warning/30",
  critical: "bg-critical/15 text-critical ring-1 ring-critical/30",
};
