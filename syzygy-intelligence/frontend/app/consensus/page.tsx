"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { AgentSelector } from "@/components/consensus/AgentSelector";
import { LiveAgentGrid, LiveAgentState } from "@/components/consensus/LiveAgentGrid";
import { ConsensusView } from "@/components/consensus/ConsensusView";
import { SessionHistory } from "@/components/consensus/SessionHistory";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Brain, Send, Settings2, X } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import { API_URL as API, WS_URL } from "@/lib/config";

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

interface HistoryEntry {
  task: string;
  result: string;
  time: string;
  rounds: number;
  sessionId?: string;
}

const STORAGE_KEY = "syzygy-consensus-history";

export default function ConsensusPage() {
  const [task, setTask] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [synthesis, setSynthesis] = useState<string | null>(null);
  const [fusionReport, setFusionReport] = useState<FusionReport | null>(null);
  const [roundDetails, setRoundDetails] = useState<RoundDetail[]>([]);
  const [roundsCompleted, setRoundsCompleted] = useState(0);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [maxRounds, setMaxRounds] = useState(6);
  const [threshold, setThreshold] = useState(0.85);
  const [showConfig, setShowConfig] = useState(false);
  const [currentRound, setCurrentRound] = useState(1);
  const [liveAgents, setLiveAgents] = useState<LiveAgentState[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const wsClientId = useRef<string>("");

  const saveToHistory = useCallback((entry: HistoryEntry) => {
    setHistory((prev) => {
      const next = [entry, ...prev].slice(0, 20);
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { console.debug("Failed to save history to localStorage"); }
      return next;
    });
  }, []);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setHistory(JSON.parse(stored));
    } catch { console.debug("Failed to load history from localStorage"); }

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "connected" && data.client_id) {
          wsClientId.current = data.client_id;
        }

        if (["consensus_proposal", "consensus_critique", "consensus_refinement", "consensus_evaluation"].includes(data.type)) {
          const phase = data.type.replace("consensus_", "");
          if (data.agent && data.content) {
            setReasoning((prev) => [...prev, {
              agent: data.agent,
              thought: (data.content as string).slice(0, 200),
              confidence: 0.8,
              model: data.archetype as string,
            }]);
          }
          setLiveAgents((prev) => prev.map((a) =>
            a.name === data.agent
              ? { ...a, phase, thought: data.content as string || "" }
              : a,
          ));
        }
        if (data.type === "consensus_started") {
          setLiveAgents([]);
          setCurrentRound(1);
          const taskText = data.task as string || task;
          if (data.agents) {
            setLiveAgents((data.agents as Array<{ id: string; name: string; archetype: string; polarity: string }>).map((a) => ({
              id: a.id,
              name: a.name,
              archetype: a.archetype,
              polarity: a.polarity,
              phase: "proposal",
              done: false,
              thought: "",
            })));
          }
        }
        if (data.type === "consensus_round_complete") {
          setCurrentRound((data.round as number) || 1);
        }
        if (data.type === "consensus_agent_done") {
          setLiveAgents((prev) => prev.map((a) =>
            a.name === data.agent ? { ...a, done: true } : a,
          ));
        }
        if (data.type === "consensus_complete") {
          const s = data.synthesis as string;
          setSynthesis(s);
          setResult(s);
          setRoundsCompleted(data.total_rounds as number || 0);
          setFusionReport((data.fusion_report as FusionReport) || null);
          setRunning(false);
          setLiveAgents((prev) => prev.map((a) => ({ ...a, done: true })));
        }
      } catch (e) { logger.error("Failed to parse WebSocket message: %s", e); }
    };
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [task]);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) return;
    setRunning(true);
    setSynthesis(null);
    setFusionReport(null);
    setRoundDetails([]);
    setRoundsCompleted(0);
    setReasoning([]);
    setLiveAgents([]);

    const headers = useAuthStore.getState().getAuthHeaders();
    const body = {
      task: task.trim(),
      max_rounds: maxRounds,
      threshold,
      agent_ids: selectedAgents.length > 0 ? selectedAgents : undefined,
    };

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: "run_consensus",
        ...body,
        ws_client_id: wsClientId.current || undefined,
      }));
      if (!wsClientId.current) {
        try {
          const res = await fetch(`${API}/api/consensus/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...headers },
            body: JSON.stringify(body),
          });
          if (res.ok) {
            const data = await res.json();
            handleRestResult(data);
          }
        } catch (err) {
          logger.error("Consensus REST fallback failed", err, "Consensus");
          setRunning(false);
          toast.error("Consensus request failed");
        }
      }
    } else {
      try {
        const res = await fetch(`${API}/api/consensus/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...headers },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`Consensus failed: ${res.status}`);
        const data = await res.json();
        handleRestResult(data);
      } catch (err) {
        logger.error("Consensus run failed", err, "Consensus");
        toast.error("Backend unavailable");
        const fallback = "Consensus engine ready. (Backend must have Ollama running for live execution.)";
        setSynthesis(fallback);
        setResult(fallback);
      } finally {
        setRunning(false);
      }
    }
  };

  const handleRestResult = (data: Record<string, unknown>) => {
    const s = (data.synthesis as string) || "Consensus completed.";
    setSynthesis(s);
    setResult(s);
    setRoundsCompleted(data.rounds_completed as number || 0);
    setFusionReport((data.fusion_report as FusionReport) || null);
    setRoundDetails((data.round_details as RoundDetail[]) || []);
    if (data.reasoning) {
      setReasoning(data.reasoning as typeof reasoning);
    }
    setRunning(false);
    saveToHistory({
      task: task.trim(),
      result: s,
      time: new Date().toISOString(),
      rounds: data.rounds_completed as number || 0,
      sessionId: (data.session_id as string) || "",
    });
  };

  const handleHistorySelect = (entry: HistoryEntry) => {
    setTask(entry.task);
    setSynthesis(entry.result);
    setResult(entry.result);
    setRoundsCompleted(entry.rounds);
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <img
          src="/branding/pagetop.logo.png"
          alt="Syzygy"
          className="h-8 w-auto brightness-110"
          width={32} height={32}
        />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Consensus</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Multi-round debate with polarity-aware synthesis</p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cn("h-2 w-2 rounded-full", wsConnected ? "bg-green-500" : "bg-red-500/50")} />
          <span className="text-[10px] text-syzygy-grey/50">
            {wsConnected ? "Live WebSocket" : "REST mode"}
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowConfig(!showConfig)}
          className={cn(
            "flex items-center gap-1 rounded-md px-2 py-1 text-[10px] transition-all",
            showConfig
              ? "bg-syzygy-gold/10 text-syzygy-gold-light"
              : "text-syzygy-grey/40 hover:text-syzygy-grey-light hover:bg-syzygy-shadow",
          )}
        >
          {showConfig ? <X className="h-3 w-3" /> : <Settings2 className="h-3 w-3" />}
          {showConfig ? "Close" : "Settings"}
        </button>
      </div>

      {showConfig && (
        <div className="animate-fade-in rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-4 space-y-3">
          <h3 className="text-xs font-medium text-syzygy-grey-light">Consensus Configuration</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-[10px] text-syzygy-grey/40 uppercase tracking-wider">Max Rounds</label>
              <input
                type="range"
                min={1}
                max={10}
                value={maxRounds}
                onChange={(e) => setMaxRounds(Number(e.target.value))}
                className="w-full accent-syzygy-gold"
              />
              <div className="flex justify-between text-[10px] text-syzygy-grey/40">
                <span>1</span>
                <span className="text-syzygy-gold-light font-medium">{maxRounds}</span>
                <span>10</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] text-syzygy-grey/40 uppercase tracking-wider">Convergence Threshold</label>
              <input
                type="range"
                min={0.5}
                max={1.0}
                step={0.05}
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full accent-syzygy-gold"
              />
              <div className="flex justify-between text-[10px] text-syzygy-grey/40">
                <span>50%</span>
                <span className="text-syzygy-gold-light font-medium">{(threshold * 100).toFixed(0)}%</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleRun} className="space-y-3">
        <div className="group relative syzygy-card-glass rounded-2xl border-syzygy-gold/20 transition-all duration-300 focus-within:border-syzygy-gold/50 focus-within:shadow-lg focus-within:shadow-syzygy-gold/10">
          <div className="flex items-center gap-3 px-4 py-3">
            <Brain className="h-5 w-5 shrink-0 text-syzygy-gold/60" />
            <input
              type="text"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Enter a topic for consensus debate..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
            />
            <VoiceButton onTranscript={(t) => setTask((prev) => prev + t)} />
            <Button type="submit" disabled={!task.trim() || running} variant="gold" size="sm" className="shrink-0 gap-1.5">
              {running ? (
                <div className="ouroboros-ring h-4 w-4" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
              {running ? "Converging..." : "Run Consensus"}
            </Button>
          </div>
        </div>

        <AgentSelector selected={selectedAgents} onChange={setSelectedAgents} />
      </form>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={running} />

      {running && liveAgents.length > 0 && (
        <LiveAgentGrid agents={liveAgents} currentRound={currentRound} />
      )}

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={running} title="Consensus Reasoning" />
      )}

      {synthesis !== null && (
        <ConsensusView
          result={synthesis}
          rounds={roundDetails}
          fusionReport={fusionReport}
          loading={running}
          roundsCompleted={roundsCompleted}
        />
      )}

      <SessionHistory
        entries={history}
        onSelect={handleHistorySelect}
        onClear={() => { setHistory([]); localStorage.removeItem(STORAGE_KEY); }}
      />
    </div>
  );
}
