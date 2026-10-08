// Consistent rendering for a null/unavailable metric (e.g. Pi-only fields on a
// non-Pi host). Keeps the "degrade gracefully" rule in one place.
export function Unavailable({ label = "Unavailable" }: { label?: string }) {
  return <span className="text-slate-500 italic text-sm">{label}</span>;
}
