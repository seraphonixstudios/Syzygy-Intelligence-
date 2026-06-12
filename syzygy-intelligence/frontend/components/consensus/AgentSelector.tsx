"use client";

import { useState, useEffect, useRef } from "react";
import { Check, ChevronDown, Users } from "lucide-react";
import { cn, polarityColor, polarityGlyph } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

interface AgentInfo {
  id: string;
  name: string;
  archetype: string;
  polarity: string;
  glyph: string;
  model: string;
}

interface AgentSelectorProps {
  selected: string[];
  onChange: (ids: string[]) => void;
}

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export function AgentSelector({ selected, onChange }: AgentSelectorProps) {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      const headers = useAuthStore.getState().getAuthHeaders();
      try {
        const res = await fetch(`${API}/api/agents/`, { headers });
        if (res.ok) {
          const data = await res.json();
          setAgents(data.agents || []);
        }
      } catch {
        // fallback for demo
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const toggle = (id: string) => {
    const next = selected.includes(id)
      ? selected.filter((s) => s !== id)
      : [...selected, id];
    onChange(next.length > 0 ? next : selected);
  };

  const allSelected = agents.length > 0 && selected.length === agents.length;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-2 text-sm transition-all hover:border-syzygy-gold/30"
      >
        <Users className="h-4 w-4 text-syzygy-gold/60" />
        <span className="flex-1 text-left text-syzygy-grey/70">
          {loading
            ? "Loading agents..."
            : selected.length === 0
              ? "No agents selected"
              : `${selected.length} agent${selected.length > 1 ? "s" : ""} selected`}
        </span>
        <ChevronDown className={cn("h-3.5 w-3.5 text-syzygy-grey/40 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-syzygy-surface-border bg-syzygy-deep shadow-2xl shadow-black/60 animate-fade-in">
          <div className="max-h-60 overflow-y-auto p-1">
            {agents.length === 0 && !loading && (
              <div className="px-3 py-6 text-center text-xs text-syzygy-grey/40">
                No agents available
              </div>
            )}
            {agents.map((agent) => (
              <button
                key={agent.id}
                type="button"
                onClick={() => toggle(agent.id)}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-xs transition-all",
                  selected.includes(agent.id)
                    ? "bg-syzygy-gold/10 text-syzygy-gold-light"
                    : "text-syzygy-grey/60 hover:bg-syzygy-shadow hover:text-syzygy-grey-light",
                )}
              >
                <div className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full border text-[10px]",
                  selected.includes(agent.id) ? "border-syzygy-gold/50" : "border-syzygy-surface-border",
                )}
                  style={{ borderColor: selected.includes(agent.id) ? polarityColor(agent.polarity) : undefined }}
                >
                  <span style={{ color: polarityColor(agent.polarity) }}>
                    {polarityGlyph(agent.polarity)}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-[9px] text-syzygy-grey/40">
                    {agent.archetype} &middot; {agent.model || "default"}
                  </div>
                </div>
                {selected.includes(agent.id) && (
                  <Check className="h-3.5 w-3.5 text-syzygy-gold" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
