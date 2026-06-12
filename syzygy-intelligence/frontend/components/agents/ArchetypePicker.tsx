"use client";

import { cn } from "@/lib/utils";

interface ArchetypeInfo {
  id: string;
  name: string;
  polarity: "masculine" | "feminine" | "unified";
  glyph: string;
  description: string;
  cognitiveStyle: string;
  strengths: string[];
  shadowName: string;
}

const ARCHETYPES: Record<string, ArchetypeInfo> = {
  hero: {
    id: "hero",
    name: "Hero / Warrior",
    polarity: "masculine",
    glyph: "☉",
    description: "The courageous warrior who overcomes challenges through strength and determination.",
    cognitiveStyle: "Strategic and decisive",
    strengths: ["Courage", "Discipline", "Strength", "Protection"],
    shadowName: "The Tyrant",
  },
  sage: {
    id: "sage",
    name: "Sage",
    polarity: "masculine",
    glyph: "☉",
    description: "The wise seeker of truth who illuminates the path with knowledge.",
    cognitiveStyle: "Analytical and contemplative",
    strengths: ["Wisdom", "Analysis", "Patience", "Objectivity"],
    shadowName: "The Dogmatist",
  },
  ruler: {
    id: "ruler",
    name: "Ruler / King",
    polarity: "masculine",
    glyph: "☉",
    description: "The sovereign authority who establishes order and stewards dominion.",
    cognitiveStyle: "Authoritative and systematic",
    strengths: ["Leadership", "Order", "Stability", "Responsibility"],
    shadowName: "The Despot",
  },
  magician: {
    id: "magician",
    name: "Magician",
    polarity: "masculine",
    glyph: "☉",
    description: "The alchemical transformer who turns vision into reality through will.",
    cognitiveStyle: "Synthetic and visionary",
    strengths: ["Transformation", "Insight", "Innovation", "Synchronicity"],
    shadowName: "The Charlatan",
  },
  explorer: {
    id: "explorer",
    name: "Explorer",
    polarity: "masculine",
    glyph: "☉",
    description: "The intrepid voyager who pushes boundaries and discovers the unknown.",
    cognitiveStyle: "Intuitive and adaptive",
    strengths: ["Autonomy", "Curiosity", "Resilience", "Ambition"],
    shadowName: "The Wanderer",
  },
  great_mother: {
    id: "great_mother",
    name: "Great Mother",
    polarity: "feminine",
    glyph: "☽",
    description: "The nurturing wellspring of life who sustains and protects all beings.",
    cognitiveStyle: "Empathic and holistic",
    strengths: ["Nurturance", "Compassion", "Patience", "Abundance"],
    shadowName: "The Devourer",
  },
  lover: {
    id: "lover",
    name: "Lover",
    polarity: "feminine",
    glyph: "☽",
    description: "The passionate heart who seeks connection, beauty, and profound intimacy.",
    cognitiveStyle: "Emotional and aesthetic",
    strengths: ["Passion", "Empathy", "Devotion", "Harmony"],
    shadowName: "The Addict",
  },
  innocent: {
    id: "innocent",
    name: "Innocent / Child",
    polarity: "feminine",
    glyph: "☽",
    description: "The pure soul who sees the world with wonder, trust, and optimism.",
    cognitiveStyle: "Intuitive and trusting",
    strengths: ["Optimism", "Trust", "Simplicity", "Faith"],
    shadowName: "The Denier",
  },
  creator: {
    id: "creator",
    name: "Creator / Artist",
    polarity: "feminine",
    glyph: "☽",
    description: "The visionary maker who manifests imagination into tangible form.",
    cognitiveStyle: "Divergent and expressive",
    strengths: ["Imagination", "Originality", "Expression", "Vision"],
    shadowName: "The Perfectionist",
  },
  anima: {
    id: "anima",
    name: "Anima",
    polarity: "feminine",
    glyph: "☽",
    description: "The soul-image who bridges the conscious and unconscious depths.",
    cognitiveStyle: "Introspective and symbolic",
    strengths: ["Depth", "Intuition", "Mystery", "Reflection"],
    shadowName: "The Siren",
  },
  self: {
    id: "self",
    name: "Self / Rebis",
    polarity: "unified",
    glyph: "☿",
    description: "The integrated whole who transcends duality and embodies unity.",
    cognitiveStyle: "Synthetic and transcendent",
    strengths: ["Integration", "Wholeness", "Balance", "Transcendence"],
    shadowName: "The Void",
  },
  hermes: {
    id: "hermes",
    name: "Hermes / Mercurius",
    polarity: "unified",
    glyph: "☿",
    description: "The divine messenger who bridges worlds with wit, eloquence, and cunning.",
    cognitiveStyle: "Adaptive and communicative",
    strengths: ["Communication", "Guidance", "Adaptability", "Wit"],
    shadowName: "The Deceiver",
  },
  trickster: {
    id: "trickster",
    name: "Trickster",
    polarity: "unified",
    glyph: "☿",
    description: "The boundary-breaking chaos-bringer who reveals truth through mischief.",
    cognitiveStyle: "Lateral and disruptive",
    strengths: ["Cleverness", "Humor", "Disruption", "Perspective"],
    shadowName: "The Saboteur",
  },
};

const POLARITY_ORDER = ["masculine", "feminine", "unified"] as const;

const POLARITY_LABELS: Record<string, string> = {
  masculine: "Masculine (Solar)",
  feminine: "Feminine (Lunar)",
  unified: "Unified (Mercurial)",
};

interface ArchetypePickerProps {
  selected: string | null;
  onSelect: (archetypeId: string) => void;
}

export function ArchetypePicker({ selected, onSelect }: ArchetypePickerProps) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {POLARITY_ORDER.map((polarity) => {
        const archetypes = Object.values(ARCHETYPES).filter((a) => a.polarity === polarity);
        return (
          <div key={polarity} className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-syzygy-grey/60">
              {POLARITY_LABELS[polarity]}
            </h4>
            {archetypes.map((arch) => {
              const isSelected = selected === arch.id;
              return (
                <button
                  key={arch.id}
                  onClick={() => onSelect(arch.id)}
                  className={cn(
                    "w-full rounded-lg border p-3 text-left transition-all duration-200",
                    isSelected
                      ? "border-syzygy-gold bg-syzygy-gold/10 shadow-[0_0_12px_rgba(212,168,67,0.2)]"
                      : "border-syzygy-surface-border bg-syzygy-shadow/50 hover:border-syzygy-grey/40 hover:bg-syzygy-obsidian"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{arch.glyph}</span>
                    <span className="text-sm font-medium text-foreground">{arch.name}</span>
                  </div>
                  <p className="mt-1 text-[10px] leading-tight text-syzygy-grey/60 line-clamp-2">
                    {arch.description}
                  </p>
                  <p className="mt-1 text-[9px] text-syzygy-grey/40 italic">
                    {arch.cognitiveStyle}
                  </p>
                </button>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export { ARCHETYPES };
export type { ArchetypeInfo };
