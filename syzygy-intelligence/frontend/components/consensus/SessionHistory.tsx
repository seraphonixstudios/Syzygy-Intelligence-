"use client";

import { Clock, Sparkles, Trash2 } from "lucide-react";
import { formatDate, truncate } from "@/lib/utils";

interface HistoryEntry {
  task: string;
  result: string;
  time: string;
  rounds: number;
  sessionId?: string;
}

interface SessionHistoryProps {
  entries: HistoryEntry[];
  onSelect: (entry: HistoryEntry) => void;
  onClear: () => void;
}

export function SessionHistory({ entries, onSelect, onClear }: SessionHistoryProps) {
  if (entries.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
          <Sparkles className="h-4 w-4" />
          Previous Sessions
        </h2>
        <button
          type="button"
          onClick={onClear}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-[10px] text-syzygy-grey/40 transition-colors hover:text-red-400 hover:bg-red-500/10"
        >
          <Trash2 className="h-3 w-3" />
          Clear
        </button>
      </div>
      <div className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
        {entries.map((h, i) => (
          <button
            key={`${h.time}-${i}`}
            onClick={() => onSelect(h)}
            className="w-full text-left syzygy-card-glass rounded-xl p-3 transition-all hover:border-syzygy-gold/30 group"
          >
            <p className="text-sm font-medium text-syzygy-grey truncate group-hover:text-syzygy-gold-light transition-colors">
              {h.task}
            </p>
            <div className="flex items-center gap-3 mt-1 text-[10px] text-syzygy-grey/40">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDate(h.time)}
              </span>
              <span>{h.rounds} round{h.rounds !== 1 ? "s" : ""}</span>
            </div>
            <p className="mt-1 text-[11px] text-syzygy-grey/50 line-clamp-2 leading-relaxed">
              {truncate(h.result, 120)}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
