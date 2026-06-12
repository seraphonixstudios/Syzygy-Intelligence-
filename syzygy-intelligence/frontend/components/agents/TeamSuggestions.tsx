"use client";

import { Button } from "@/components/ui/button";
import { Sparkles, Loader2 } from "lucide-react";
import { useState } from "react";

interface TeamSuggestion {
  name: string;
  description: string;
  archetypes: string[];
}

const SUGGESTIONS: TeamSuggestion[] = [
  {
    name: "Default",
    description: "2 Masculine, 2 Feminine, 1 Unified",
    archetypes: ["hero", "sage", "great_mother", "lover", "self"],
  },
  {
    name: "Analytical",
    description: "Sage, Ruler, Explorer, Lover, Self",
    archetypes: ["sage", "ruler", "explorer", "lover", "self"],
  },
  {
    name: "Creative",
    description: "Creator, Magician, Lover, Innocent, Hermes",
    archetypes: ["creator", "magician", "lover", "innocent", "hermes"],
  },
  {
    name: "Critical",
    description: "Hero, Sage, Trickster, Anima, Self",
    archetypes: ["hero", "sage", "trickster", "anima", "self"],
  },
];

interface TeamSuggestionsProps {
  onCompose: (archetypes: string[]) => Promise<void>;
}

export function TeamSuggestions({ onCompose }: TeamSuggestionsProps) {
  const [applying, setApplying] = useState<string | null>(null);

  const handleApply = async (name: string, archetypes: string[]) => {
    setApplying(name);
    try {
      await onCompose(archetypes);
    } finally {
      setApplying(null);
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Team Suggestions</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {SUGGESTIONS.map((suggestion) => (
          <div
            key={suggestion.name}
            className="rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 p-3 space-y-2 hover:border-syzygy-gold/30 transition-all duration-200"
          >
            <div>
              <h4 className="text-sm font-medium text-foreground">{suggestion.name}</h4>
              <p className="text-[10px] text-syzygy-grey/60 mt-0.5">{suggestion.description}</p>
            </div>
            <Button
              variant="occult"
              size="sm"
              className="w-full"
              onClick={() => handleApply(suggestion.name, suggestion.archetypes)}
              disabled={applying !== null}
            >
              {applying === suggestion.name ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <Sparkles className="mr-1 h-3 w-3" />
              )}
              {applying === suggestion.name ? "Applying..." : "Apply"}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
