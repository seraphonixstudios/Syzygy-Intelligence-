"use client";

import { useState, useEffect, useCallback } from "react";
import { AgentCard } from "@/components/agents/AgentCard";
import { Button } from "@/components/ui/button";
import { Loader2, Users, Plus, Trash2, Zap, Sparkles } from "lucide-react";
import { logger } from "@/lib/logger";
import { toast } from "sonner";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [composing, setComposing] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [error, setError] = useState("");

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/agents/`);
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (err) {
      logger.error("Failed to fetch agents", err, "Agents");
      setError("Backend unreachable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  const handleCompose = async () => {
    setComposing(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/agents/compose`, { method: "POST" });
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (err) {
      logger.error("Failed to compose team", err, "Agents");
      setError("Failed to compose team");
    } finally {
      setComposing(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await fetch(`${API}/api/agents/${id}`, { method: "DELETE" });
      setAgents((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      logger.error("Failed to delete agent", err, "Agents");
      setError("Failed to delete agent");
    } finally {
      setDeleting(null);
    }
  };

  const handleToggleShadow = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/agents/${id}/shadow/toggle`, { method: "POST" });
      const data = await res.json();
      setAgents((prev) => prev.map((a) => (a.id === id ? { ...a, shadow_active: data.shadow_active } : a)));
    } catch (err) {
      logger.error("Failed to toggle shadow", err, "Agents");
      setError("Failed to toggle shadow");
    }
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="ouroboros-ring h-10 w-10" />
          <p className="text-sm text-syzygy-grey/60 animate-pulse">Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-8 w-auto brightness-110"
          />
          <div>
            <h1 className="syzygy-title text-2xl font-bold tracking-wider">Agents</h1>
            <p className="mt-0.5 text-xs text-syzygy-grey/60">Polarity-balanced agent team</p>
          </div>
        </div>
        <Button variant="gold" size="sm" onClick={handleCompose} disabled={composing}>
          {composing ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Zap className="mr-1 h-4 w-4" />
          )}
          {composing ? "Composing..." : "Compose Team"}
        </Button>
      </div>

      {error && (
        <div className="animate-slide-in-right rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
          <button className="ml-2 underline" onClick={() => setError("")}>Dismiss</button>
        </div>
      )}

      {agents.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-20">
          <Users className="h-12 w-12 text-syzygy-grey/20" />
          <p className="text-sm text-syzygy-grey/40">No agents yet. Compose a team to get started.</p>
          <Button variant="gold" size="sm" onClick={handleCompose} disabled={composing}>
            <Sparkles className="mr-1 h-4 w-4" />
            Compose Team
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {agents.map((agent, i) => (
            <div
              key={agent.id}
              className={`stagger-${Math.min(i + 1, 8)} animate-fade-in-up group relative`}
            >
              <AgentCard
                name={agent.name}
                archetype={agent.archetype}
                polarity={agent.polarity}
                model={agent.model}
                shadow={agent.shadow_active}
              />
              <div className="absolute right-2 top-2 flex gap-1 opacity-0 transition-all duration-200 group-hover:opacity-100">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => handleToggleShadow(agent.id)}
                  title="Toggle shadow"
                >
                  {agent.shadow_active ? "☀" : "☾"}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  onClick={() => handleDelete(agent.id)}
                  disabled={deleting === agent.id}
                  title="Delete agent"
                >
                  {deleting === agent.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {agents.length > 0 && (
        <div className="flex items-center justify-center gap-2 text-xs text-syzygy-grey/40">
          <span>{agents.filter((a: any) => a.polarity === "masculine").length} Masculine</span>
          <span className="text-syzygy-grey/20">•</span>
          <span>{agents.filter((a: any) => a.polarity === "feminine").length} Feminine</span>
          <span className="text-syzygy-grey/20">•</span>
          <span>{agents.filter((a: any) => a.polarity === "unified").length} Unified</span>
        </div>
      )}
    </div>
  );
}
