"use client";

import { cn, polarityColor, polarityGlyph } from "@/lib/utils";
import { Brain, MessageSquare, RefreshCw, Scale, CheckCircle2, Loader2 } from "lucide-react";

const PHASE_ICONS: Record<string, typeof Brain> = {
  proposal: MessageSquare,
  critique: Scale,
  refinement: RefreshCw,
  evaluation: Brain,
};

const PHASE_LABELS: Record<string, string> = {
  proposal: "Proposing",
  critique: "Critiquing",
  refinement: "Refining",
  evaluation: "Evaluating",
};

const PHASE_COLORS: Record<string, string> = {
  proposal: "text-blue-400 border-blue-500/30 bg-blue-500/10",
  critique: "text-red-400 border-red-500/30 bg-red-500/10",
  refinement: "text-purple-400 border-purple-500/30 bg-purple-500/10",
  evaluation: "text-green-400 border-green-500/30 bg-green-500/10",
};

export interface LiveAgentState {
  id: string;
  name: string;
  archetype: string;
  polarity: string;
  phase: string;
  done: boolean;
  thought: string;
}

interface LiveAgentGridProps {
  agents: LiveAgentState[];
  currentRound: number;
}

export function LiveAgentGrid({ agents, currentRound }: LiveAgentGridProps) {
  if (agents.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-syzygy-gold/60">
        <Loader2 className="h-3 w-3 animate-spin" />
        Round {currentRound} &middot; {agents.filter((a) => a.done).length}/{agents.length} agents complete
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {agents.map((agent) => {
          const PhaseIcon = PHASE_ICONS[agent.phase] || Brain;
          return (
            <div
              key={agent.id}
              className={cn(
                "rounded-xl border p-3 transition-all duration-500",
                agent.done
                  ? "border-green-500/20 bg-green-500/5"
                  : "border-syzygy-surface-border bg-syzygy-shadow/50",
              )}
            >
              <div className="flex items-center gap-2">
                <div
                  className="flex h-7 w-7 items-center justify-center rounded-full border text-xs"
                  style={{ borderColor: polarityColor(agent.polarity) }}
                >
                  <span style={{ color: polarityColor(agent.polarity) }}>
                    {polarityGlyph(agent.polarity)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-syzygy-grey-light truncate">
                      {agent.name}
                    </span>
                    <span className="text-[9px] text-syzygy-grey/40 shrink-0">
                      {agent.archetype}
                    </span>
                  </div>
                  {agent.done ? (
                    <div className="flex items-center gap-1 mt-0.5">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      <span className="text-[10px] text-green-400/70">Complete</span>
                    </div>
                  ) : (
                    <div className={cn(
                      "mt-0.5 inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] border transition-colors",
                      PHASE_COLORS[agent.phase] || "text-syzygy-gold border-syzygy-gold/20 bg-syzygy-gold/10",
                    )}>
                      <PhaseIcon className="h-2.5 w-2.5" />
                      {PHASE_LABELS[agent.phase] || agent.phase}
                    </div>
                  )}
                </div>
                {!agent.done && (
                  <div className="ouroboros-ring h-4 w-4 shrink-0" />
                )}
              </div>
              {agent.thought && (
                <p className="mt-2 text-[10px] leading-relaxed text-syzygy-grey/50 line-clamp-2 border-t border-syzygy-surface-border pt-2">
                  {agent.thought}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
