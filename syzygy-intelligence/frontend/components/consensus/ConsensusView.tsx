"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Sparkles, Brain } from "lucide-react";

interface ConsensusViewProps {
  result: string | null;
  rounds?: { round: number; proposals: string[] }[];
}

export function ConsensusView({ result, rounds }: ConsensusViewProps) {
  return (
    <Card className="relative overflow-hidden">
      {/* Vesica Piscis background */}
      <div className="vesica-piscis pointer-events-none absolute inset-0 opacity-[0.03]" />

      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-syzygy-gold-light" />
          Consensus Synthesis
          <span className="text-xs font-normal text-syzygy-grey">
            — within the Vesica Piscis
          </span>
        </CardTitle>
      </CardHeader>

      <CardContent>
        {/* Rebis fusion animation */}
        <div className="rebis-container mx-auto mb-6 flex h-28 w-28 items-center justify-center">
          <div className="rebis-fusion relative flex h-full w-full items-center justify-center">
            <img src="/branding/sol.logo.png" alt="Sol" className="polarity-sun absolute left-0 top-1/2 h-[100px] w-auto brightness-110" />
            <img src="/branding/luna.logo.png" alt="Luna" className="polarity-moon absolute right-0 top-1/2 h-[84px] w-auto brightness-110" />
            <span className="relative z-10 text-xl text-syzygy-bone">☿</span>
          </div>
        </div>

        {/* Status */}
        {!result ? (
          <div className="flex flex-col items-center gap-3 py-8">
            <Loader2 className="h-6 w-6 animate-spin text-syzygy-gold-light" />
            <p className="text-sm text-syzygy-grey">
              Agents are converging... (Solve et Coagula)
            </p>
            <div className="ouroboros-ring h-12 w-12" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Rounds timeline */}
            {rounds && rounds.length > 0 && (
              <div className="flex gap-2">
                {rounds.map((r) => (
                  <div
                    key={r.round}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-syzygy-gold/10 text-xs text-syzygy-gold-light"
                    title={`Round ${r.round}: ${r.proposals.length} proposals`}
                  >
                    {r.round}
                  </div>
                ))}
              </div>
            )}

            {/* Result */}
            <div className="solve-et-coagula rounded-lg border border-syzygy-gold/20 bg-syzygy-shadow/50 p-4">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-syzygy-gold" />
                <span className="text-xs font-semibold uppercase tracking-wider text-syzygy-gold">
                  Rebis Oracle
                </span>
              </div>
              <p className="text-sm leading-relaxed text-syzygy-grey">
                {result}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
