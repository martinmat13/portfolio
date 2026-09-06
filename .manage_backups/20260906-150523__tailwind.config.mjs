/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        void: {
          DEFAULT: "#05080D",
          soft: "#080D14",
          raised: "#0D141D",
        },
        glass: "rgba(13, 20, 30, 0.55)",
        hairline: "#142331",
        ink: {
          DEFAULT: "#E8F1F5",
          muted: "#8CA0AD",
          faint: "#54646F",
        },
        flow: {
          // "velocity" — primary accent, cyan
          DEFAULT: "#00E5FF",
          dim: "#0C7A8C",
        },
        vortex: {
          // "vorticity/heat" — secondary accent, orange
          DEFAULT: "#FF7A1A",
          dim: "#8C4310",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to bottom, rgba(20,35,49,0.4) 1px, transparent 1px), linear-gradient(to right, rgba(20,35,49,0.4) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "40px 40px",
      },
      boxShadow: {
        "glow-flow": "0 0 24px rgba(0, 229, 255, 0.35)",
        "glow-vortex": "0 0 24px rgba(255, 122, 26, 0.35)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
