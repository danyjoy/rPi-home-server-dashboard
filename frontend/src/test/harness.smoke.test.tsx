// Smoke test confirming the Vitest + jsdom + React Testing Library + jest-dom
// harness is wired up correctly. It renders a trivial component that consumes
// the existing useScrolled hook so the DOM environment, React rendering, and
// the custom matchers are all exercised. Replace/augment with the real
// useScrolled unit tests (task 2.2) later.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useScrolled } from "../hooks/useScrolled";

function ScrollProbe() {
  const scrolled = useScrolled();
  return <span data-testid="probe">{scrolled ? "scrolled" : "top"}</span>;
}

describe("test harness", () => {
  it("renders a component into jsdom and applies jest-dom matchers", () => {
    render(<ScrollProbe />);
    const probe = screen.getByTestId("probe");
    expect(probe).toBeInTheDocument();
    // At initial render in jsdom, window.scrollY is 0, so the hook is false.
    expect(probe).toHaveTextContent("top");
  });
});
