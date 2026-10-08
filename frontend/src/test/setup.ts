// Registers the @testing-library/jest-dom custom matchers (e.g. toBeInTheDocument,
// toHaveClass) on Vitest's expect, and cleans up the rendered DOM after each test.
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});
