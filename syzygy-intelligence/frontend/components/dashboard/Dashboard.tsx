"use client";

import { useState, useEffect, useCallback } from "react";
import { CommandBar } from "./CommandBar";
import { AgentCard } from "@/components/agents/AgentCard";
import { ConsensusView } from "@/components/consensus/ConsensusView";
import { PolarityMeter } from "@/components/consensus/PolarityMeter";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FlaskConical, Activity, Users as UsersIcon, Loader2, Code2, Search, FileText, Zap, ArrowRight, TrendingUp } from "lucide-react";

import { API_URL as API } from "@/lib/config";

const defaultAgents = [
  { id: "1", name: "Sage", archetype: "sage", polarity: "masculine", model: "qwen3:8b-gpu", shadow: false },
  { id: "2", name: "Nurtura", archetype: "great_mother", polarity: "feminine", model: "dolphin-llama3:8b-gpu", shadow: false },
  { id: "3", name: "Rebis", archetype: "self", polarity: "unified", model: "qwen3:8b-gpu", shadow: false },
  { id: "4", name: "Merlin", archetype: "magician", polarity: "masculine", model: "qwen3:8b-gpu", shadow: false },
  { id: "5", name: "Astra", archetype: "creator", polarity: "feminine", model: "dolphin-llama3:8b-gpu", shadow: false },
  { id: "6", name: "Heracles", archetype: "hero", polarity: "masculine", model: "qwen3:8b-gpu", shadow: false },
  { id: "7", name: "Aphrodite", archetype: "lover", polarity: "feminine", model: "dolphin-llama3:8b-gpu", shadow: false },
  { id: "8", name: "Loki", archetype: "trickster", polarity: "unified", model: "qwen3:8b-gpu", shadow: false },
];

const quickActions = [
  { icon: Code2, label: "Generate Code", href: "/code", color: "gold" },
  { icon: Search, label: "Research Topic", href: "/research", color: "gold" },
  { icon: FileText, label: "Create Content", href: "/content", color: "gold" },
  { icon: TrendingUp, label: "Self-Improve", href: "/improve", color: "gold" },
  { icon: UsersIcon, label: "Manage Agents", href: "/agents", color: "gold" },
];

export function Dashboard() {
  const [agents, setAgents] = useState(defaultAgents);
  const [showConsensus, setShowConsensus] = useState(false);
  const [consensusResult, setConsensusResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${API}/api/agents/`)
      .then((r) => r.json())
      .then((data) => {
        if (data.agents?.length) setAgents(data.agents);
        setApiOnline(true);
      })
      .catch(() => { setApiOnline(false); });
  }, []);

  const handleComposeTeam = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/agents/compose`, { method: "POST" });
      const data = await res.json();
      if (data.agents) setAgents(data.agents);
    } catch {
      setAgents(defaultAgents);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleTaskSubmit = async (task: string) => {
    setShowConsensus(true);
    setConsensusResult(null);
    try {
      const res = await fetch(`${API}/api/consensus/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, max_rounds: 4, threshold: 0.85 }),
      });
      const data = await res.json();
      setConsensusResult(data.synthesis || "Consensus completed successfully.");
    } catch {
      setConsensusResult("Consensus engine ready. (Backend must be running for live execution.)");
    }
  };

  return (
    <div className="space-y-8">
      {/* Brand Hero */}
      <div className="flex flex-col items-center gap-4 py-6 text-center">
        <div className="animate-brand-glow">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-32 w-auto brightness-110 md:h-40"
            width={128} height={128}
          />
        </div>
        <img
          src="/branding/syzygy.logo.png"
          alt="SYZYGY Intelligence"
          className="h-24 w-auto brightness-110 md:h-32"
          width={96} height={96}
        />
        <p className="text-sm text-syzygy-grey/60">
          Aligning opposites into unified intelligence
        </p>
        {apiOnline === false && (
          <div className="flex items-center gap-2 rounded-full border border-syzygy-gold/20 bg-syzygy-gold/5 px-4 py-1.5">
            <div className="h-2 w-2 rounded-full bg-syzygy-gold animate-pulse" />
            <span className="text-xs text-syzygy-grey/60">Backend offline — using local defaults</span>
          </div>
        )}
      </div>

      {/* Command Bar */}
      <CommandBar onSubmit={handleTaskSubmit} />

      {/* Quick Actions */}
      <div className="grid gap-3 sm:grid-cols-5">
        {quickActions.map((action, i) => (
          <a
            key={action.href}
            href={action.href}
            className={`stagger-${i + 1} animate-fade-in-up group flex items-center gap-3 rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-4 transition-all duration-300 hover:border-syzygy-gold/30 hover:bg-syzygy-deep hover:shadow-lg hover:shadow-syzygy-gold/10`}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-syzygy-gold/10 group-hover:bg-syzygy-gold/20 transition-all">
              <action.icon className="h-5 w-5 text-syzygy-gold" />
            </div>
            <span className="text-sm font-medium text-syzygy-grey-light group-hover:text-syzygy-gold-light transition-colors">
              {action.label}
            </span>
            <ArrowRight className="ml-auto h-4 w-4 text-syzygy-grey/30 group-hover:text-syzygy-gold group-hover:translate-x-1 transition-all" />
          </a>
        ))}
      </div>

      {/* Status + Agent Team */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Agent Team */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
              <FlaskConical className="h-4 w-4" />
              Agent Team
            </h2>
            <div className="flex items-center gap-2">
              <div className={cn(
                "flex items-center gap-1.5 rounded-full px-2.5 py-1",
                apiOnline === null ? "bg-syzygy-grey/10" :
                apiOnline ? "bg-green-500/10" : "bg-red-500/10"
              )}>
                <div className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  apiOnline === null ? "bg-syzygy-grey animate-skeleton" :
                  apiOnline ? "bg-green-400" : "bg-red-400"
                )} />
                <span className="text-[10px] text-syzygy-grey/60">
                  {apiOnline === null ? "Connecting" : apiOnline ? `${agents.length} agents` : "Offline"}
                </span>
              </div>
              <Button variant="gold" size="sm" onClick={handleComposeTeam} disabled={loading}>
                {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
                <span className="ml-1">{loading ? "Composing..." : "Compose"}</span>
              </Button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {agents.map((agent, i) => (
              <div key={agent.id} className={`stagger-${Math.min(i + 1, 8)} animate-fade-in-up`}>
                <AgentCard
                  name={agent.name}
                  archetype={agent.archetype}
                  polarity={agent.polarity}
                  model={agent.model}
                  shadow={agent.shadow}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Polarity Meter */}
        <div className="space-y-4">
          <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
            <Activity className="h-4 w-4" />
            Polarity Balance
          </h2>
          <PolarityMeter
            masculine={40}
            feminine={40}
            unified={20}
          />
        </div>
      </div>

      {/* Consensus View */}
      {showConsensus && (
        <div className="animate-fade-in-up space-y-4">
          <ConsensusView result={consensusResult} />
        </div>
      )}
    </div>
  );
}

function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
