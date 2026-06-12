"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PolarityMeter } from "@/components/consensus/PolarityMeter";
import { RoundTimeline } from "@/components/consensus/RoundTimeline";
import { Loader2, Sparkles, Brain, Eye, EyeOff, ScrollText } from "lucide-react";
import { cn } from "@/lib/utils";

interface RoundDetail {
  round: number;
  proposals: string[];
  critiques: string[];
  refinements: string[];
  scores: Record<string, number>;
  convergence_score: number | null;
}

interface FusionReport {
  masculine: number;
  feminine: number;
  unified: number;
  balance_score: number;
}

interface ConsensusViewProps {
  result: string | null;
  rounds?: RoundDetail[];
  fusionReport?: FusionReport | null;
  loading?: boolean;
  roundsCompleted?: number;
}

export function ConsensusView({
  result,
  rounds,
  fusionReport,
  loading,
  roundsCompleted,
}: ConsensusViewProps) {
  const [showRounds, setShowRounds] = useState(false);
  const [showPolarity, setShowPolarity] = useState(false);

  return (
    <Card className="relative overflow-hidden">
      <div className="vesica-piscis pointer-events-none absolute inset-0 opacity-[0.03]" />

      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-syzygy-gold-light" />
          Consensus Synthesis
          {roundsCompleted !== undefined && (
            <span className="text-xs font-normal text-syzygy-grey">
              &middot; {roundsCompleted} round{roundsCompleted !== 1 ? "s" : ""}
            </span>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="rebis-container mx-auto mb-6 flex h-28 w-28 items-center justify-center">
          <div className="rebis-fusion relative flex h-full w-full items-center justify-center">
            <img src="/branding/sol.logo.png" alt="Sol" className="polarity-sun absolute left-0 top-1/2 h-[100px] w-auto brightness-110" />
            <img src="/branding/luna.logo.png" alt="Luna" className="polarity-moon absolute right-0 top-1/2 h-[84px] w-auto brightness-110" />
            <span className="relative z-10 text-xl text-syzygy-bone">☿</span>
          </div>
        </div>

        {loading && !result ? (
          <div className="flex flex-col items-center gap-3 py-8">
            <Loader2 className="h-6 w-6 animate-spin text-syzygy-gold-light" />
            <p className="text-sm text-syzygy-grey">
              Agents are converging... (Solve et Coagula)
            </p>
            <div className="ouroboros-ring h-12 w-12" />
          </div>
        ) : result ? (
          <div className="space-y-5">
            <div className="solve-et-coagula rounded-lg border border-syzygy-gold/20 bg-syzygy-shadow/50 p-4">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-syzygy-gold" />
                <span className="text-xs font-semibold uppercase tracking-wider text-syzygy-gold">
                  Rebis Oracle
                </span>
              </div>
              <p className="text-sm leading-relaxed text-syzygy-grey whitespace-pre-wrap">
                {result}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {fusionReport && (
                <button
                  type="button"
                  onClick={() => setShowPolarity(!showPolarity)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs transition-all",
                    showPolarity
                      ? "border-syzygy-gold/30 bg-syzygy-gold/10 text-syzygy-gold-light"
                      : "border-syzygy-surface-border bg-syzygy-shadow/30 text-syzygy-grey/50 hover:border-syzygy-gold/20 hover:text-syzygy-grey-light",
                  )}
                >
                  {showPolarity ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  Polarity Balance
                </button>
              )}
              {rounds && rounds.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowRounds(!showRounds)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs transition-all",
                    showRounds
                      ? "border-syzygy-gold/30 bg-syzygy-gold/10 text-syzygy-gold-light"
                      : "border-syzygy-surface-border bg-syzygy-shadow/30 text-syzygy-grey/50 hover:border-syzygy-gold/20 hover:text-syzygy-grey-light",
                  )}
                >
                  {showRounds ? <EyeOff className="h-3.5 w-3.5" /> : <ScrollText className="h-3.5 w-3.5" />}
                  Round Details
                </button>
              )}
            </div>

            {showPolarity && fusionReport && (
              <div className="animate-fade-in">
                <PolarityMeter
                  masculine={fusionReport.masculine}
                  feminine={fusionReport.feminine}
                  unified={fusionReport.unified}
                />
              </div>
            )}

            {showRounds && rounds && rounds.length > 0 && (
              <div className="animate-fade-in">
                <RoundTimeline rounds={rounds} />
              </div>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
