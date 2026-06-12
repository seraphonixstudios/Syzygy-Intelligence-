"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, polarityColor, polarityGlyph } from "@/lib/utils";

interface AgentCardProps {
  name: string;
  archetype: string;
  polarity: string;
  model: string;
  shadow?: boolean;
  persona?: {
    name: string;
    style: string;
    tone: string;
    traits: string[];
  };
}

const SHADOW_NAMES: Record<string, string> = {
  hero: "The Tyrant",
  sage: "The Dogmatist",
  ruler: "The Despot",
  magician: "The Charlatan",
  explorer: "The Wanderer",
  great_mother: "The Devourer",
  lover: "The Addict",
  innocent: "The Denier",
  creator: "The Perfectionist",
  anima: "The Siren",
  self: "The Void",
  hermes: "The Deceiver",
  trickster: "The Saboteur",
};

export function AgentCard({
  name,
  archetype,
  polarity,
  model,
  shadow,
  persona,
}: AgentCardProps) {
  const glyph = polarityGlyph(polarity);
  const color = polarityColor(polarity);
  const shadowArchetype = SHADOW_NAMES[archetype] || "The Shadow";
  const displayArchetype = archetype.replace(/_/g, " ");

  const barWidth =
    polarity === "masculine" ? 75 :
    polarity === "feminine" ? 60 :
    85;

  return (
    <Card
      className={cn(
        "group relative overflow-hidden transition-all duration-300 hover:translate-y-[-2px] hover:shadow-[0_0_20px_rgba(212,168,67,0.15)]",
        shadow && "ring-1 ring-destructive/30 ring-offset-1 ring-offset-syzygy-deep"
      )}
    >
      <div
        className={cn(
          "absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100 pointer-events-none",
          polarity === "masculine"
            ? "bg-gradient-to-br from-syzygy-gold/5 to-transparent"
            : polarity === "feminine"
              ? "bg-gradient-to-br from-syzygy-grey/5 to-transparent"
              : "bg-gradient-to-br from-syzygy-bone/5 to-transparent"
        )}
      />
      <CardContent className="relative p-4">
        <div className="mb-3 flex items-center justify-between">
          <span
            className="text-2xl transition-all duration-300 group-hover:scale-110 group-hover:drop-shadow-[0_0_8px_var(--tw-shadow-color)]"
            style={{ color }}
          >
            {glyph}
          </span>
          <Badge
            variant={
              polarity === "masculine"
                ? "masculine"
                : polarity === "feminine"
                  ? "feminine"
                  : "unified"
            }
            className="text-[10px]"
          >
            {polarity}
          </Badge>
        </div>

        <h3 className="font-semibold text-foreground">{name}</h3>
        <p className="mt-0.5 text-xs capitalize text-syzygy-grey/60">
          {displayArchetype}
        </p>

        {persona && (
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium text-syzygy-gold/80">{persona.name}</span>
              <span className="text-[8px] text-syzygy-grey/40">•</span>
              <span className="text-[9px] capitalize text-syzygy-grey/50">{persona.style}</span>
              <span className="text-[8px] text-syzygy-grey/40">•</span>
              <span className="text-[9px] capitalize text-syzygy-grey/50">{persona.tone}</span>
            </div>
            {persona.traits && persona.traits.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {persona.traits.slice(0, 3).map((trait) => (
                  <span
                    key={trait}
                    className="rounded bg-syzygy-shadow/50 px-1.5 py-0.5 text-[8px] text-syzygy-grey/50"
                  >
                    {trait}
                  </span>
                ))}
                {persona.traits.length > 3 && (
                  <span className="text-[8px] text-syzygy-grey/40">+{persona.traits.length - 3}</span>
                )}
              </div>
            )}
          </div>
        )}

        <div className="mt-3 flex items-center gap-2">
          <span className="truncate rounded bg-syzygy-shadow/50 px-2 py-0.5 text-[10px] text-syzygy-grey/60">
            {model}
          </span>
          {shadow && (
            <span
              className="text-[10px] text-destructive transition-all duration-300"
              title={shadowArchetype}
            >
              ☠ {shadowArchetype}
            </span>
          )}
        </div>

        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-syzygy-shadow/50">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${barWidth}%`,
              backgroundColor: color,
              boxShadow: `0 0 12px ${color}80`,
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
