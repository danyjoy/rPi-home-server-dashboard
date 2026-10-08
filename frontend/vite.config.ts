import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// During local dev, proxy /api to the FastAPI backend so the frontend uses the
// same relative paths it will use behind nginx in production.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    // jsdom gives React Testing Library a DOM to render into.
    environment: "jsdom",
    globals: true,
    // Registers @testing-library/jest-dom matchers before each test file.
    setupFiles: ["./src/test/setup.ts"],
  },
});
