/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#0a0e17",
          surface: "#111827",
          border: "#1e293b",
          muted: "#64748b",
          accent: "#22d3ee",
        },
      },
    },
  },
  plugins: [],
};

