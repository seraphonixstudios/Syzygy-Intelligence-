"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight, MessageSquare, Scale, RefreshCw, Brain, Target } from "lucide-react";

interface RoundDetail {
  round: number;
  proposals: string[];
  critiques: string[];
  refinements: string[];
  scores: Record<string, number>;
  convergence_score: number | null;
}

interface RoundTimelineProps {
  rounds: RoundDetail[];
}

const CONVERGENCE_THRESHOLD = 0.85;

export function RoundTimeline({ rounds }: RoundTimelineProps) {
  const [expandedRound, setExpandedRound] = useState<number | null>(null);

  if (!rounds || rounds.length === 0) return null;

  const sorted = [...rounds].sort((a, b) => a.round - b.round);

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 font-alchemical text-sm tracking-wider text-syzygy-gold">
        <Target className="h-4 w-4" />
        Round Timeline
      </h3>

      <div className="space-y-2">
        {sorted.map((r, idx) => {
          const expanded = expandedRound === r.round;
          const converged = (r.convergence_score ?? 0) >= CONVERGENCE_THRESHOLD;
          return (
            <div
              key={r.round}
              className={cn(
                "rounded-xl border transition-all",
                converged
                  ? "border-green-500/20 bg-green-500/5"
                  : "border-syzygy-surface-border bg-syzygy-shadow/30",
              )}
            >
              <button
                type="button"
                onClick={() => setExpandedRound(expanded ? null : r.round)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left"
              >
                <div className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                  converged
                    ? "bg-green-500/15 text-green-400"
                    : "bg-syzygy-gold/10 text-syzygy-gold",
                )}>
                  {r.round}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-syzygy-grey-light">
                      Round {r.round}
                    </span>
                    {converged && (
                      <span className="rounded bg-green-500/15 px-1.5 py-0.5 text-[9px] text-green-400 font-medium uppercase tracking-wider">
                        Converged
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 text-[10px] text-syzygy-grey/40">
                    <span>{r.proposals.length} proposals</span>
                    <span>{r.critiques.length} critiques</span>
                    {r.refinements.length > 0 && <span>{r.refinements.length} refinements</span>}
                    {r.convergence_score !== null && (
                      <span className={converged ? "text-green-400/60" : ""}>
                        {(r.convergence_score! * 100).toFixed(0)}% convergence
                      </span>
                    )}
                  </div>
                </div>
                {expanded ? (
                  <ChevronDown className="h-4 w-4 text-syzygy-grey/40" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-syzygy-grey/40" />
                )}
              </button>

              {expanded && (
                <div className="border-t border-syzygy-surface-border px-4 py-3 space-y-3 animate-fade-in">
                  {r.proposals.length > 0 && (
                    <PhaseSection icon={MessageSquare} label="Proposals" color="text-blue-400" border="border-blue-500/20">
                      {r.proposals.map((p, i) => (
                        <p key={i} className="text-[11px] text-syzygy-grey/70 leading-relaxed">{p}</p>
                      ))}
                    </PhaseSection>
                  )}

                  {r.critiques.length > 0 && (
                    <PhaseSection icon={Scale} label="Critiques" color="text-red-400" border="border-red-500/20">
                      {r.critiques.map((c, i) => (
                        <p key={i} className="text-[11px] text-syzygy-grey/70 leading-relaxed">{c}</p>
                      ))}
                    </PhaseSection>
                  )}

                  {r.refinements.length > 0 && (
                    <PhaseSection icon={RefreshCw} label="Refinements" color="text-purple-400" border="border-purple-500/20">
                      {r.refinements.map((r_, i) => (
                        <p key={i} className="text-[11px] text-syzygy-grey/70 leading-relaxed">{r_}</p>
                      ))}
                    </PhaseSection>
                  )}

                  {Object.keys(r.scores).length > 0 && (
                    <PhaseSection icon={Brain} label="Scores" color="text-green-400" border="border-green-500/20">
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(r.scores).map(([agent, score]) => (
                          <div
                            key={agent}
                            className="flex items-center gap-1.5 rounded-md bg-syzygy-shadow/70 px-2 py-1"
                          >
                            <span className="text-[10px] text-syzygy-grey/50">{agent}</span>
                            <span className="text-[11px] font-medium text-syzygy-gold-light">
                              {(score * 100).toFixed(0)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </PhaseSection>
                  )}

                  {r.convergence_score !== null && (
                    <div className="flex items-center gap-2 pt-1">
                      <div className="flex-1 h-1.5 rounded-full bg-syzygy-surface-border overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-700",
                            converged ? "bg-green-500" : "bg-syzygy-gold/60",
                          )}
                          style={{ width: `${Math.min(100, (r.convergence_score ?? 0) * 100)}%` }}
                        />
                      </div>
                      <span className={cn(
                        "text-[10px] font-medium",
                        converged ? "text-green-400" : "text-syzygy-grey/40",
                      )}>
                        {(r.convergence_score! * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PhaseSection({
  icon: Icon,
  label,
  color,
  border,
  children,
}: {
  icon: typeof MessageSquare;
  label: string;
  color: string;
  border: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`rounded-lg border ${border} bg-syzygy-shadow/30 p-3 space-y-2`}>
      <div className={`flex items-center gap-1.5 text-[10px] uppercase tracking-wider ${color}`}>
        <Icon className="h-3 w-3" />
        {label}
      </div>
      {children}
    </div>
  );
}
