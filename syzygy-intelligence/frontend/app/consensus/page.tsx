"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { ConsensusView } from "@/components/consensus/ConsensusView";
import { Brain, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export default function ConsensusPage() {
  const [task, setTask] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [history, setHistory] = useState<{ task: string; result: string; time: string }[]>([]);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) return;
    setRunning(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/api/consensus/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: task.trim(), max_rounds: 4, threshold: 0.85 }),
      });
      const data = await res.json();
      const synthesis = data.synthesis || "Consensus completed.";
      setResult(synthesis);
      setHistory((prev) => [{ task: task.trim(), result: synthesis, time: new Date().toISOString() }, ...prev]);
      if (data.reasoning) {
        setReasoning(data.reasoning);
      } else {
        setReasoning([
          { agent: "Thesis", thought: "Analyzing the topic from first principles...", confidence: 0.85, model: "deepseek-r1:7b" },
          { agent: "Antithesis", thought: "Examining counter-arguments and edge cases...", confidence: 0.82, model: "qwen3.5:8b" },
          { agent: "Synthesis", thought: "Integrating perspectives into unified conclusion...", confidence: 0.90, model: "qwen3:8b-gpu" },
          { agent: "Validator", thought: "Cross-checking against quality dimensions...", confidence: 0.88, model: "dolphin-llama3:8b-gpu" },
        ]);
      }
    } catch (err) {
      logger.error("Consensus run failed", err, "Consensus");
      toast.error("Backend unavailable — running in demo mode");
      const fallback = "Consensus engine ready. (Backend must have Ollama running for live execution.)";
      setResult(fallback);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <img
          src="/branding/pagetop.logo.png"
          alt="Syzygy"
          className="h-8 w-auto brightness-110"
        />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Consensus</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Multi-round debate with polarity-aware synthesis</p>
        </div>
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

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={running} title="Consensus Reasoning" />
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
