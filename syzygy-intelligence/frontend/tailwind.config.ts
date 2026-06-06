import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        syzygy: {
          black: "#000000",
          abyss: "#050505",
          shadow: "#0a0a0a",
          deep: "#111111",
          obsidian: "#1a1a1a",
          coal: "#2a2a2a",
          dark: "#3a3533",
          gold: {
            DEFAULT: "#d4a843",
            light: "#e8c35a",
            pale: "#f0d080",
            dark: "#8b6914",
            ritual: "#b8860b",
          },
          grey: {
            DEFAULT: "#8a7f7a",
            light: "#a8a098",
            pale: "#c8c0b8",
            dark: "#3a3533",
          },
          bone: "#e8dcc8",
          crimson: {
            DEFAULT: "#5c0000",
            light: "#8a0000",
          },
          surface: {
            DEFAULT: "#0d0d0d",
            light: "#141414",
            card: "#111111",
            border: "#2a2a2a",
          },
        },
        background: "#000000",
        foreground: "#c8c0b8",
        card: {
          DEFAULT: "#111111",
          foreground: "#c8c0b8",
        },
        popover: {
          DEFAULT: "#0d0d0d",
          foreground: "#c8c0b8",
        },
        primary: {
          DEFAULT: "#d4a843",
          foreground: "#000000",
        },
        secondary: {
          DEFAULT: "#8a7f7a",
          foreground: "#000000",
        },
        muted: {
          DEFAULT: "#1a1a1a",
          foreground: "#8a7f7a",
        },
        accent: {
          DEFAULT: "#e8c35a",
          foreground: "#000000",
        },
        destructive: {
          DEFAULT: "#5c0000",
          foreground: "#c8c0b8",
        },
        border: "#2a2a2a",
        input: "#2a2a2a",
        ring: "#d4a843",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "occult-glow": "radial-gradient(ellipse at center, #141414 0%, #000000 70%)",
        "gold-gradient": "linear-gradient(135deg, #d4a843, #e8c35a, #d4a843)",
        "bone-gradient": "linear-gradient(135deg, #c8c0b8, #e8dcc8, #c8c0b8)",
        "shadow-gradient": "linear-gradient(180deg, #0a0a0a, #000000)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        alchemical: ["Cinzel", "serif"],
      },
      animation: {
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "rotate-slow": "rotate-slow 20s linear infinite",
        "solve-coagula": "solve-coagula 3s ease-in-out infinite",
        "merge-pulse": "merge-pulse 4s ease-in-out infinite",
        "particle-drift": "particle-drift 15s linear infinite",
        "rebis-fusion": "rebis-fusion 8s ease-in-out infinite",
        "ouroboros": "ouroboros 3s linear infinite",
        "fade-in-up": "fade-in-up 0.5s ease-out both",
        "fade-in": "fade-in 0.4s ease-out both",
        "slide-in-right": "slide-in-right 0.4s ease-out both",
        "scale-in": "scale-in 0.3s ease-out both",
        "brand-glow": "brand-glow 3s ease-in-out infinite",
        "skeleton": "skeleton-pulse 1.5s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "thought-appear": "thought-appear 0.4s ease-out both",
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-drift": "glow-drift 4s ease-in-out infinite",
        "slide-up": "slide-up 0.3s ease-out both",
        "breathe": "breathe 3s ease-in-out infinite",
        "spin-slow": "spin-slow 8s linear infinite",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 20px #d4a84340" },
          "50%": { boxShadow: "0 0 40px #d4a84380, 0 0 60px #b8860b40" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "rotate-slow": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        "solve-coagula": {
          "0%": { opacity: "0", transform: "scale(0.8) rotate(-5deg)" },
          "50%": { opacity: "1", transform: "scale(1.05) rotate(2deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(0deg)" },
        },
        "merge-pulse": {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
        "particle-drift": {
          "0%": { transform: "translate(0, 0) scale(1)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translate(100px, -100px) scale(0)", opacity: "0" },
        },
        "rebis-fusion": {
          "0%": { transform: "rotateY(0deg)" },
          "50%": { transform: "rotateY(180deg)" },
          "100%": { transform: "rotateY(360deg)" },
        },
        ouroboros: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "brand-glow": {
          "0%, 100%": { filter: "brightness(1) drop-shadow(0 0 8px #d4a84340)" },
          "50%": { filter: "brightness(1.15) drop-shadow(0 0 20px #d4a84380) drop-shadow(0 0 40px #b8860b40)" },
        },
        "skeleton-pulse": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% center" },
          "100%": { backgroundPosition: "200% center" },
        },
        "thought-appear": {
          "0%": { opacity: "0", transform: "translateY(8px) scale(0.97)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "pulse-ring": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
        "glow-drift": {
          "0%, 100%": { filter: "brightness(1) drop-shadow(0 0 4px #d4a84320)" },
          "50%": { filter: "brightness(1.1) drop-shadow(0 0 12px #d4a84350) drop-shadow(0 0 24px #b8860b20)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        breathe: {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.03)" },
        },
        "spin-slow": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
