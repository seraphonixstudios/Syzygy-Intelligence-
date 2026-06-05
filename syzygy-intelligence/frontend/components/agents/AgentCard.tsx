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
}

export function AgentCard({
  name,
  archetype,
  polarity,
  model,
  shadow,
}: AgentCardProps) {
  const glyph = polarityGlyph(polarity);
  const color = polarityColor(polarity);

  const barWidth =
    polarity === "masculine" ? 75 :
    polarity === "feminine" ? 60 :
    85;

  return (
    <Card
      className={cn(
        "group relative overflow-hidden transition-all duration-300 hover:translate-y-[-2px]",
        shadow && "ring-1 ring-destructive/30"
      )}
    >
      <CardContent className="p-4">
        {/* Glyph */}
        <div className="mb-3 flex items-center justify-between">
          <span
            className="text-2xl transition-transform duration-300 group-hover:scale-110"
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

        {/* Name & Archetype */}
        <h3 className="font-semibold text-foreground">{name}</h3>
        <p className="mt-0.5 text-xs capitalize text-syzygy-grey/60">
          {archetype.replace(/_/g, " ")}
        </p>

        {/* Model & Shadow */}
        <div className="mt-3 flex items-center gap-2">
          <span className="truncate rounded bg-syzygy-shadow/50 px-2 py-0.5 text-[10px] text-syzygy-grey/60">
            {model}
          </span>
          {shadow && (
            <span className="text-[10px] text-destructive">☠ Shadow</span>
          )}
        </div>

        {/* Polarity bar */}
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
