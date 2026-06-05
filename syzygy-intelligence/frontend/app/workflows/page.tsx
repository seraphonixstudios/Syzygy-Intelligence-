"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { Workflow, Play, Loader2, CheckCircle2, XCircle } from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

const WORKFLOW_DESCRIPTIONS: Record<string, string> = {
  code: "Scaffold, edit, test, and debug with polarity-aware pair programming",
  research: "Parallel search with multi-source validation and synthesis",
  content: "Research → Outline → Draft → Edit → Polish pipeline",
  debate: "Multi-round structured debate between agents",
  task_decomposition: "Break complex tasks into dependency-tracked subtasks",
};

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState("");
  const [input, setInput] = useState("");
  const [executing, setExecuting] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/api/workflows/`)
      .then((r) => r.json())
      .then((data) => {
        const list = data.workflows || [];
        setWorkflows(list.map((w: any) => (typeof w === "string" ? w : w.name)));
      })
      .catch(() => setWorkflows(Object.keys(WORKFLOW_DESCRIPTIONS)))
      .finally(() => setLoading(false));
  }, []);

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !input.trim()) return;
    setExecuting(true);
    setOutput(null);
    setError("");
    try {
      const res = await fetch(`${API}/api/workflows/${selected}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: input.trim(), context: {} }),
      });
      const data = await res.json();
      setOutput(JSON.stringify(data, null, 2));
    } catch {
      setError("Workflow execution requires the backend to be running.");
    } finally {
      setExecuting(false);
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
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Workflows</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Visual node-based workflow builder</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {loading ? (
          <div className="col-span-3 flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-syzygy-gold" /></div>
        ) : (
          workflows.map((w) => (
            <button
              key={w}
              onClick={() => setSelected(w)}
              className={`syzygy-card-glass rounded-xl p-4 text-left transition-all hover:border-syzygy-gold/30 ${
                selected === w ? "border-syzygy-gold/50 shadow-lg shadow-syzygy-gold/10" : ""
              }`}
            >
              <div className="flex items-center gap-2">
                <Workflow className="h-4 w-4 text-syzygy-gold" />
                <span className="font-semibold text-sm capitalize text-foreground">{w.replace(/_/g, " ")}</span>
              </div>
              <p className="mt-1 text-xs text-syzygy-grey/60">{WORKFLOW_DESCRIPTIONS[w] || ""}</p>
            </button>
          ))
        )}
      </div>

      {selected && (
        <form onSubmit={handleExecute} className="space-y-3">
          <div className="flex items-center gap-2 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Enter task for ${selected.replace(/_/g, " ")}...`}
              className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
            />
            <VoiceButton onTranscript={(t) => setInput((prev) => prev + t)} />
            <Button type="submit" disabled={!input.trim() || executing} variant="gold" size="sm" className="shrink-0 gap-1">
              {executing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              Execute
            </Button>
          </div>
        </form>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          <XCircle className="h-4 w-4" /> {error}
        </div>
      )}

      {output && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-syzygy-gold">
            <CheckCircle2 className="h-4 w-4" /> Result
          </div>
          <pre className="overflow-auto rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 p-4 text-xs text-syzygy-grey/80 max-h-96">
            {output}
          </pre>
        </div>
      )}
    </div>
  );
}
