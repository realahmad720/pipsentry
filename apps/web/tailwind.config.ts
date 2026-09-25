import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "var(--color-base)",
        panel: "var(--color-panel)",
        ink: "var(--color-ink)",
        bullish: "var(--color-bullish)",
        bearish: "var(--color-bearish)",
        accent: "var(--color-accent)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
      },
    },
  },
  plugins: [],
};

export default config;
