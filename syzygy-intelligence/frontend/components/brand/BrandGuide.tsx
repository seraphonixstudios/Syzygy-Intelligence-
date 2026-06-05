"use client";

import { useState } from "react";

const BRAND_ASSETS = [
  { file: "pagetop.logo.png", label: "Page Top Logo", w: 1024, h: 1536 },
  { file: "syzygy.logo.png", label: "Syzygy Wordmark", w: 1536, h: 1024 },
  { file: "sol.logo.png", label: "Sol (Masculine)", w: 1024, h: 1536 },
  { file: "luna.logo.png", label: "Luna (Feminine)", w: 1024, h: 1536 },
  { file: "rebis.logo.png", label: "Rebis (Unified)", w: 1024, h: 1536 },
  { file: "seraphonixlogo.png", label: "Favicon", w: 1024, h: 1024 },
];

const POLARITY_THEME = {
  masculine: { symbol: "☉", color: "#d4a843", principle: "Active, Analytical, Assertive" },
  feminine: { symbol: "☽", color: "#8a7f7a", principle: "Receptive, Synthetic, Intuitive" },
  unified: { symbol: "☿", color: "#e8dcc8", principle: "Mediating, Holistic, Dialectical" },
};

const ANIMATIONS = [
  { name: "brand-glow", dur: "3s", desc: "Pulsing golden aura around brand logos" },
  { name: "merge-sun-moon", dur: "3s", desc: "Sol and Luna orbit toward center, scaling and overlapping" },
  { name: "rebis-fusion", dur: "8s", desc: "3D Y-axis rotation of the unified symbol" },
  { name: "solve-coagula", dur: "3s", desc: "Dissolve/appear scale-and-rotate entrance" },
  { name: "ouroboros", dur: "3s", desc: "Infinite spinning ring loader" },
  { name: "particle-drift", dur: "15s", desc: "Drifting golden particles across the screen" },
  { name: "ember-drift", dur: "8s", desc: "Alchemical embers rising from below" },
  { name: "sigil-pulse", dur: "20s", desc: "Slow rotating alchemical sigil decorations" },
  { name: "ring-expand", dur: "3s", desc: "Expanding golden rings from center" },
  { name: "portal-glow", dur: "6s", desc: "Conic gradient rotating portal border" },
  { name: "flicker-gold", dur: "4s", desc: "Candle-like gold text flicker" },
  { name: "radiant-burst", dur: "2s", desc: "Radiating burst shadow effect" },
  { name: "border-rotate", dur: "3s", desc: "Animated gradient border sweep" },
];

export function BrandGuide() {
  const [tab, setTab] = useState<"assets" | "polarity" | "animations">("assets");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <img src="/branding/pagetop.logo.png" alt="" className="h-10 w-auto brightness-110" />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Brand Guide</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Visual identity, polarity system, and animation reference</p>
        </div>
      </div>

      <div className="flex gap-1 rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 p-1">
        {(["assets", "polarity", "animations"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-md px-4 py-2 text-xs uppercase tracking-wider transition-all ${
              tab === t ? "bg-syzygy-gold/20 text-syzygy-gold" : "text-syzygy-grey/40 hover:text-syzygy-grey"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "assets" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {BRAND_ASSETS.map((a) => (
            <div
              key={a.file}
              className="gradient-border-gold group overflow-hidden rounded-xl bg-syzygy-deep/80 p-4 transition-all hover:scale-[1.02]"
            >
              <div className="mb-3 flex items-center justify-center overflow-hidden rounded-lg bg-syzygy-shadow/50 p-4">
                <img
                  src={`/branding/${a.file}`}
                  alt={a.label}
                  className="h-32 w-auto object-contain brightness-90 transition-all duration-500 group-hover:brightness-110 group-hover:scale-110"
                />
              </div>
              <p className="font-alchemical text-sm text-syzygy-gold">{a.label}</p>
              <p className="text-[10px] text-syzygy-grey/40">{a.file} &middot; {a.w}&times;{a.h}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "polarity" && (
        <div className="grid gap-4 md:grid-cols-3">
          {(Object.entries(POLARITY_THEME) as [string, typeof POLARITY_THEME[keyof typeof POLARITY_THEME]][]).map(([key, val]) => (
            <div
              key={key}
              className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-6 text-center transition-all hover:border-syzygy-gold/30"
            >
              <div
                className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full text-4xl"
                style={{ border: `2px solid ${val.color}40`, color: val.color }}
              >
                {val.symbol}
              </div>
              <p className="font-alchemical text-lg capitalize text-syzygy-gold">{key}</p>
              <p className="mt-1 text-xs text-syzygy-grey/60">{val.principle}</p>
              <p className="mt-2 text-[10px] text-syzygy-grey/40" style={{ color: val.color }}>
                {val.color}
              </p>
            </div>
          ))}
        </div>
      )}

      {tab === "animations" && (
        <div className="space-y-2">
          {ANIMATIONS.map((anim) => (
            <div
              key={anim.name}
              className="flex items-center justify-between rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-4 py-3 transition-all hover:border-syzygy-gold/30"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`h-8 w-8 shrink-0 rounded-full bg-syzygy-gold/10 ${anim.name.startsWith("animate-") ? anim.name : "animate-" + anim.name}`}
                  style={
                    anim.name === "ring-expand"
                      ? { border: "1px solid #d4a843", borderRadius: "50%" }
                      : anim.name === "border-rotate"
                        ? { background: "linear-gradient(90deg, #d4a843, #e8c35a, #d4a843)", backgroundSize: "200% 100%" }
                        : {}
                  }
                />
                <div>
                  <p className="text-sm font-medium text-syzygy-gold">{anim.name}</p>
                  <p className="text-xs text-syzygy-grey/40">{anim.dur}</p>
                </div>
              </div>
              <p className="hidden text-right text-xs text-syzygy-grey/60 sm:block max-w-xs">{anim.desc}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
