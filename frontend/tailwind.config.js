/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        healthy: "#22c55e",
        warning: "#f59e0b",
        critical: "#ef4444",
      },
    },
  },
  plugins: [],
};
