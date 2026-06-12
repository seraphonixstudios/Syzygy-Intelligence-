"use client";

import { cn } from "@/lib/utils";

interface PolarityMeterProps {
  masculine: number;
  feminine: number;
  unified: number;
}

export function PolarityMeter({
  masculine,
  feminine,
  unified,
}: PolarityMeterProps) {
  const total = masculine + feminine + unified;
  const mascPct = total > 0 ? (masculine / total) * 100 : 33.33;
  const femPct = total > 0 ? (feminine / total) * 100 : 33.33;
  const uniPct = total > 0 ? (unified / total) * 100 : 33.34;

  const balance = 1 - Math.abs(mascPct - femPct) / 100;

  return (
    <div className="space-y-4">
      {/* Circular meter */}
      <div className="squared-circle relative mx-auto h-48 w-48">
        {/* Sun */}
        <img src="/branding/sol.logo.png" alt="Sol" className="polarity-sun absolute left-0 top-1/2 h-[144px] w-auto brightness-110" />

        {/* Moon */}
        <img src="/branding/luna.logo.png" alt="Luna" className="polarity-moon absolute right-0 top-1/2 h-[120px] w-auto brightness-110" />

        {/* Center - Rebis third eye */}
        <div className="relative flex flex-col items-center">
          <span className="text-2xl text-syzygy-bone">☿</span>
          <span className="mt-1 text-2xl font-bold text-syzygy-bone">
            {(balance * 100).toFixed(0)}%
          </span>
          <span className="text-[10px] uppercase tracking-wider text-syzygy-bone/60">
            Balance
          </span>
        </div>
      </div>

      {/* Bar indicators */}
      <div className="space-y-3">
        {/* Masculine */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-syzygy-gold">
              <img src="/branding/sol.logo.png" alt="" className="h-14 w-auto brightness-110" />
              Masculine
            </span>
            <span className="text-syzygy-gold/60">{mascPct.toFixed(0)}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-syzygy-shadow">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${mascPct}%`,
                background: "linear-gradient(90deg, #d4a843, #e8c35a)",
                boxShadow: "0 0 16px #d4a84360, 0 0 32px #d4a84320",
              }}
            />
          </div>
        </div>

        {/* Feminine */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-syzygy-grey">
              <img src="/branding/luna.logo.png" alt="" className="h-12 w-auto brightness-110" />
              Feminine
            </span>
            <span className="text-syzygy-grey/60">{femPct.toFixed(0)}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-syzygy-shadow">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${femPct}%`,
                background: "linear-gradient(90deg, #6a6058, #8a7f7a)",
                boxShadow: "0 0 16px #8a7f7a60, 0 0 32px #8a7f7a20",
              }}
            />
          </div>
        </div>

        {/* Unified */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1 text-syzygy-bone">
              ☿ Unified
            </span>
            <span className="text-syzygy-bone/60">{uniPct.toFixed(0)}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-syzygy-shadow">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${uniPct}%`,
                background: "linear-gradient(90deg, #c8c0b8, #e8dcc8)",
                boxShadow: "0 0 16px #e8dcc860, 0 0 32px #e8dcc820",
              }}
            />
          </div>
        </div>
      </div>

      {/* Status */}
      <div
        className={cn(
          "rounded-lg border p-3 text-center text-xs",
          balance >= 0.7
            ? "border-syzygy-bone/20 bg-syzygy-bone/5 text-syzygy-bone"
            : "border-syzygy-gold/20 bg-syzygy-gold/5 text-syzygy-gold"
        )}
      >
        {balance >= 0.7
          ? "☿ Polarity Balance Achieved — Rebis Integration Active"
          : "⚖ Tension of Opposites — Further Integration Needed"}
      </div>
    </div>
  );
}
