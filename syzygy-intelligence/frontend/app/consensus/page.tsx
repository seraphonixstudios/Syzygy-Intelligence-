"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { ConsensusView } from "@/components/consensus/ConsensusView";
import { Brain, Send, Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";
const WS_URL = process.env.NEXT_PUBLIC_SYZYGY_WS_URL || "ws://localhost:8000/ws";

interface LiveEvent {
  type: string;
  agent?: string;
  archetype?: string;
  polarity?: string;
  phase?: string;
  [key: string]: unknown;
}

export default function ConsensusPage() {
  const [task, setTask] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [history, setHistory] = useState<{ task: string; result: string; time: string }[]>([]);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "consensus_proposal" || data.type === "consensus_critique" || data.type === "consensus_refinement" || data.type === "consensus_evaluation") {
          setLiveEvents((prev) => [...prev, data]);
          if (data.agent && data.content) {
            setReasoning((prev) => [...prev, { agent: data.agent, thought: (data.content as string).slice(0, 200), confidence: 0.8, model: data.archetype as string }]);
          }
        }
        if (data.type === "consensus_complete") {
          setResult(data.synthesis as string);
          setRunning(false);
          toast.success("Consensus complete");
        }
        if (data.type === "consensus_started") {
          setLiveEvents([]);
        }
      } catch {
        // ignore
      }
    };
    return () => { ws.close(); };
  }, []);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) return;
    setRunning(true);
    setResult(null);
    setLiveEvents([]);
    setReasoning([]);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Use WebSocket for live events
      wsRef.current.send(JSON.stringify({
        action: "run_consensus",
        task: task.trim(),
        max_rounds: 2,
      }));
      // Also call REST endpoint to get final result (WS sends completion separately)
      fetch(`${API}/api/consensus/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: task.trim(), max_rounds: 2, threshold: 0.85 }),
      }).then((res) => res.json()).then((data) => {
        const synthesis = data.synthesis || "Consensus completed.";
        setResult(synthesis);
        setHistory((prev) => [{ task: task.trim(), result: synthesis, time: new Date().toISOString() }, ...prev]);
      }).catch(() => {
        // result will come from WS
      });
    } else {
      // Fallback to REST-only
      try {
        const res = await fetch(`${API}/api/consensus/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task: task.trim(), max_rounds: 2, threshold: 0.85, files: uploadedFiles, links: attachedLinks }),
        });
        const data = await res.json();
        const synthesis = data.synthesis || "Consensus completed.";
        setResult(synthesis);
        setHistory((prev) => [{ task: task.trim(), result: synthesis, time: new Date().toISOString() }, ...prev]);
        if (data.reasoning) {
          setReasoning(data.reasoning);
        }
      } catch (err) {
        logger.error("Consensus run failed", err, "Consensus");
        toast.error("Backend unavailable");
        const fallback = "Consensus engine ready. (Backend must have Ollama running for live execution.)";
        setResult(fallback);
      } finally {
        setRunning(false);
      }
    }
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

      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${wsConnected ? "bg-green-500" : "bg-red-500/50"}`} />
        <span className="text-[10px] text-syzygy-grey/50">{wsConnected ? "Live WebSocket connected" : "WebSocket disconnected"}</span>
      </div>

      <form onSubmit={handleRun} className="group relative syzygy-card-glass rounded-2xl border-syzygy-gold/20 transition-all duration-300 focus-within:border-syzygy-gold/50 focus-within:shadow-lg focus-within:shadow-syzygy-gold/10">
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
      </form>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={running} />

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={running} title="Consensus Reasoning" />
      )}

      {liveEvents.length > 0 && running && (
        <div className="space-y-1.5 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
          <div className="flex items-center gap-2 text-xs text-syzygy-gold/60">
            <Loader2 className="h-3 w-3 animate-spin" />
            Live Consensus Progress
          </div>
          {liveEvents.slice(-6).map((ev, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className={`shrink-0 rounded px-1 py-0.5 text-[9px] uppercase ${
                ev.type === "consensus_proposal" ? "bg-blue-500/20 text-blue-400" :
                ev.type === "consensus_critique" ? "bg-red-500/20 text-red-400" :
                ev.type === "consensus_refinement" ? "bg-purple-500/20 text-purple-400" :
                ev.type === "consensus_evaluation" ? "bg-green-500/20 text-green-400" :
                "bg-syzygy-gold/20 text-syzygy-gold"
              }`}>
                {ev.type.replace("consensus_", "").slice(0, 8)}
              </span>
              {ev.agent && <span className="font-mono text-syzygy-grey/70">{ev.agent}</span>}
              {ev.archetype && <span className="text-syzygy-grey/40">({ev.archetype})</span>}
            </div>
          ))}
        </div>
      )}

      {result !== null && (
        <ConsensusView result={result} />
      )}

      {history.length > 0 && (
        <div className="space-y-3">
          <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
            <Sparkles className="h-4 w-4" />
            Previous Sessions
          </h2>
          <div className="max-h-60 space-y-2 overflow-y-auto pr-1">
            {history.map((h, i) => (
              <button
                key={i}
                onClick={() => setResult(h.result)}
                className="w-full text-left syzygy-card-glass rounded-xl p-3 transition-all hover:border-syzygy-gold/30"
              >
                <p className="text-sm font-medium text-syzygy-grey truncate">{h.task}</p>
                <p className="text-[10px] text-syzygy-grey/40 mt-0.5">{new Date(h.time).toLocaleString()}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
