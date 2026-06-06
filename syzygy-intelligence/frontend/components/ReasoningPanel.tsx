"use client";

import { useState } from "react";
import { Brain, ChevronDown, ChevronRight, Loader2, Sparkles } from "lucide-react";

interface ReasoningStep {
  agent: string;
  thought: string;
  confidence?: number;
  model?: string;
}

interface ReasoningPanelProps {
  steps: ReasoningStep[];
  loading?: boolean;
  title?: string;
}

export function ReasoningPanel({ steps, loading, title }: ReasoningPanelProps) {
  const [expanded, setExpanded] = useState(true);

  if (!steps.length && !loading) return null;

  return (
    <div className="rounded-xl border border-syzygy-gold/20 bg-syzygy-deep/50 overflow-hidden transition-all duration-300">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-xs text-syzygy-gold/70 hover:text-syzygy-gold hover:bg-syzygy-gold/5 transition-colors"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <Brain className="h-3.5 w-3.5" />
        <span className="font-medium tracking-wider uppercase">{title || "Reasoning Trace"}</span>
        {loading && <Loader2 className="h-3 w-3 animate-spin ml-auto" />}
        {!loading && steps.length > 0 && (
          <span className="ml-auto text-[10px] text-syzygy-grey/40">{steps.length} step{steps.length > 1 ? "s" : ""}</span>
        )}
      </button>

      {expanded && (
        <div className="space-y-1.5 px-4 pb-3 animate-fade-in">
          {loading && (
            <div className="flex items-center gap-2 py-2">
              <div className="h-1.5 w-1.5 rounded-full bg-syzygy-gold animate-pulse" />
              <span className="text-[10px] text-syzygy-grey/40 italic">Processing...</span>
            </div>
          )}
          {steps.map((step, i) => (
            <div
              key={i}
              className="group relative rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 p-3 transition-all hover:border-syzygy-gold/20"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-syzygy-gold/15 text-[9px] font-bold text-syzygy-gold">
                  {i + 1}
                </span>
                <span className="text-[11px] font-medium text-syzygy-gold-light">{step.agent}</span>
                {step.model && (
                  <span className="rounded bg-syzygy-shadow/70 px-1.5 py-0.5 text-[9px] text-syzygy-grey/40 font-mono">
                    {step.model}
                  </span>
                )}
                {step.confidence !== undefined && (
                  <span className="ml-auto flex items-center gap-1 text-[10px] text-syzygy-grey/40">
                    <Sparkles className="h-3 w-3" />
                    {(step.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <p className="text-[11px] text-syzygy-grey/70 leading-relaxed">{step.thought}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
