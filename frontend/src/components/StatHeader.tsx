import { useScrolled } from "../hooks/useScrolled";

interface StatHeaderProps {
  hostname: string;
  online: boolean;
  updating: boolean;
}

export function StatHeader({ hostname, online, updating }: StatHeaderProps) {
  const scrolled = useScrolled(); // true when window.scrollY > 0

  return (
    <header
      className={[
        // sticky to top at all widths; top edge pinned at offset 0 (Req 3.1)
        "sticky top-0 z-20 -mx-4 flex items-center justify-between gap-3 px-4 sm:-mx-6 sm:px-6",
        // fully opaque background occludes scrolled content (Req 3.2)
        "bg-slate-950",
        // condensed when scrolled: height stays <= 56px (Req 3.5)
        scrolled ? "border-b border-slate-800 py-2" : "py-3 sm:py-4",
      ].join(" ")}
    >
      <div className="min-w-0">
        <h1
          className={`truncate font-bold text-slate-100 ${
            scrolled ? "text-base" : "text-xl sm:text-2xl"
          }`}
        >
          Command Center
        </h1>
        {/* hostname: single line, ellipsis on overflow (Req 3.4) */}
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
