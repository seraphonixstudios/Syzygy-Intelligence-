"use client";

import { cn } from "@/lib/utils";

interface PolarityBalanceProps {
  agents: Array<{ polarity: string }>;
}

export function PolarityBalance({ agents }: PolarityBalanceProps) {
  const counts = {
    masculine: agents.filter((a) => a.polarity === "masculine").length,
    feminine: agents.filter((a) => a.polarity === "feminine").length,
    unified: agents.filter((a) => a.polarity === "unified").length,
  };
  const total = agents.length || 1;

  const idealMasc = total * 0.4;
  const idealFem = total * 0.4;
  const idealUni = total * 0.2;

  const mascDiff = Math.abs(counts.masculine - idealMasc);
  const femDiff = Math.abs(counts.feminine - idealFem);
  const uniDiff = Math.abs(counts.unified - idealUni);

  const maxDiff = total;
  const balanceScore = Math.round(100 - ((mascDiff + femDiff + uniDiff) / maxDiff) * 50);
  const clampedBalance = Math.max(0, Math.min(100, balanceScore));

  const barColors: Record<string, string> = {
    masculine: "#d4a843",
    feminine: "#8a7f7a",
    unified: "#e8dcc8",
  };

  const balanceColor =
    clampedBalance > 70 ? "#4ade80" : clampedBalance > 40 ? "#d4a843" : "#ef4444";

  return (
    <div className="syzygy-card-glass rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Polarity Balance</h3>
        <div className="flex items-center gap-2 text-xs text-syzygy-grey/60">
          <span>Harmony</span>
          <div className="h-2 w-20 overflow-hidden rounded-full bg-syzygy-shadow/50">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${clampedBalance}%`,
                backgroundColor: balanceColor,
              }}
            />
          </div>
          <span
            className={cn(
              "font-mono text-xs",
              clampedBalance > 70
                ? "text-green-400"
                : clampedBalance > 40
                  ? "text-syzygy-gold"
                  : "text-red-400"
            )}
          >
            {clampedBalance}%
          </span>
        </div>
      </div>

      <div className="space-y-2">
        {(["masculine", "feminine", "unified"] as const).map((polarity) => {
          const count = counts[polarity];
          const pct = total > 0 ? (count / total) * 100 : 0;
          const glyph = polarity === "masculine" ? "☉" : polarity === "feminine" ? "☽" : "☿";
          const label = polarity === "masculine" ? "Masculine" : polarity === "feminine" ? "Feminine" : "Unified";

          return (
            <div key={polarity} className="flex items-center gap-2">
              <span className="w-6 text-center text-sm">{glyph}</span>
              <span className="w-20 text-xs text-syzygy-grey/60">{label}</span>
              <div className="flex-1 h-2.5 overflow-hidden rounded-full bg-syzygy-shadow/50">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.max(pct, count > 0 ? 4 : 0)}%`,
                    backgroundColor: barColors[polarity],
                    boxShadow: `0 0 8px ${barColors[polarity]}60`,
                  }}
                />
              </div>
              <span className="w-6 text-right text-xs font-mono text-syzygy-grey/40">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
