import { useEffect, useState } from "react";

// Returns true once the window has scrolled past the given threshold. Uses a
// passive scroll listener and adds no runtime dependency (React only). Drives
// the condensed Stat_Header state on small screens.
export function useScrolled(threshold = 0): boolean {
  const [scrolled, setScrolled] = useState(
    () => typeof window !== "undefined" && window.scrollY > threshold,
  );

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > threshold);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [threshold]);

  return scrolled;
}
