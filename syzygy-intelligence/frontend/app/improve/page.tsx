"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Zap, Brain, TrendingUp, CheckCircle2, XCircle, ArrowRight, RefreshCw, Sparkles } from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

interface Evaluation {
  score: number;
  dimensions: Record<string, number>;
  feedback: string[];
  suggestions: string[];
}

interface Summary {
  total_evaluations: number;
  average_score: number;
  total_proposals: number;
  applied_proposals: number;
  latest_score: number;
}

export default function ImprovePage() {
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [proposals, setProposals] = useState<any[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [applying, setApplying] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/api/meta/summary`)
      .then((r) => r.json())
      .then(setSummary)
      .catch(() => {});
  }, []);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setRunning(true);
    try {
      const res = await fetch(`${API}/api/meta/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output: input.trim(), context: { source: "manual" } }),
      });
      const data = await res.json();
      setEvaluation(data.evaluation);
      setProposals(data.proposals);
      const sumRes = await fetch(`${API}/api/meta/summary`);
      setSummary(await sumRes.json());
    } catch {
      setEvaluation({
        score: 0.85,
        dimensions: { completeness: 0.8, coherence: 0.9, specificity: 0.85, actionability: 0.7, structure: 0.95 },
        feedback: ["Demo mode — connect backend for live evaluation"],
        suggestions: ["Connect backend and Ollama for full self-improvement pipeline"],
      });
      setProposals([
        { id: "demo-1", target: "actionability", change: "Increase actionability score by 0.3", rationale: "Low actionable content", expected_impact: 0.3 },
      ]);
    } finally {
      setRunning(false);
    }
  };

  const handleApply = async (proposalId: string) => {
    setApplying(proposalId);
    try {
      await fetch(`${API}/api/meta/proposals/${proposalId}/apply`, { method: "POST" });
      setProposals((prev) => prev.filter((p) => p.id !== proposalId));
    } catch {}
    setApplying(null);
  };

  const handleFullCycle = async () => {
    setRunning(true);
    try {
      const res = await fetch(`${API}/api/meta/improve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output: input.trim() || "Default output for evaluation", context: {}, auto_apply: true }),
      });
      const data = await res.json();
      setEvaluation(data.evaluation);
      setProposals(data.proposals.filter((p: any) => !data.auto_applied.includes(p.id)));
      const sumRes = await fetch(`${API}/api/meta/summary`);
      setSummary(await sumRes.json());
    } catch {}
    setRunning(false);
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <img src="/branding/pagetop.logo.png" alt="Syzygy" className="h-8 w-auto brightness-110" />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Self-Improvement</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Recursive meta-cognition engine — evaluate, propose, improve</p>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Evaluations</p>
            <p className="mt-1 text-xl font-bold text-syzygy-gold-light">{summary.total_evaluations}</p>
          </div>
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Avg Score</p>
            <p className="mt-1 text-xl font-bold text-syzygy-gold-light">{(summary.average_score * 100).toFixed(0)}%</p>
          </div>
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Proposals</p>
            <p className="mt-1 text-xl font-bold text-syzygy-bone">{summary.total_proposals}</p>
          </div>
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Applied</p>
            <p className="mt-1 text-xl font-bold text-green-400">{summary.applied_proposals}</p>
          </div>
        </div>
      )}

      {/* Evaluate Input */}
      <form onSubmit={handleEvaluate} className="space-y-3">
        <div className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3 transition-all duration-300 focus-within:border-syzygy-gold/50 focus-within:shadow-lg focus-within:shadow-syzygy-gold/10">
          <Brain className="h-4 w-4 shrink-0 text-syzygy-gold/60" />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste an output to evaluate for self-improvement..."
            className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
          />
          <Button type="submit" disabled={!input.trim() || running} variant="gold" size="sm" className="shrink-0 gap-1">
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
            {running ? "Evaluating..." : "Evaluate"}
          </Button>
          <Button type="button" disabled={running} variant="occult" size="sm" onClick={handleFullCycle} className="shrink-0 gap-1">
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Auto-Improve</span>
          </Button>
        </div>
      </form>

      {/* Evaluation Results */}
      {evaluation && (
        <div className="animate-fade-in-up space-y-4">
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="flex items-center gap-2 text-sm font-medium text-syzygy-gold">
                <TrendingUp className="h-4 w-4" />
                Evaluation Score: {(evaluation.score * 100).toFixed(0)}%
              </h3>
              <div className="h-2 w-32 overflow-hidden rounded-full bg-syzygy-shadow">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${evaluation.score * 100}%`,
                    background: "linear-gradient(90deg, #d4a843, #e8c35a)",
                  }}
                />
              </div>
            </div>

            {/* Dimension Bars */}
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(evaluation.dimensions).map(([key, val]) => (
                <div key={key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="capitalize text-syzygy-grey/60">{key}</span>
                    <span className="text-syzygy-grey/40">{(val * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-syzygy-shadow">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${val * 100}%`,
                        background: val > 0.7
                          ? "linear-gradient(90deg, #d4a843, #e8c35a)"
                          : "linear-gradient(90deg, #8a7f7a, #c8c0b8)",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Feedback */}
            {evaluation.feedback.length > 0 && (
              <div className="mt-4 space-y-1">
                <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Feedback</p>
                {evaluation.feedback.map((f, i) => (
                  <p key={i} className="flex items-start gap-2 text-xs text-syzygy-grey/60">
                    <span className="mt-0.5 text-syzygy-gold">•</span>
                    {f}
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* Proposals */}
          {proposals.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-syzygy-bone">Improvement Proposals</h3>
              {proposals.map((p) => (
                <div key={p.id} className={`stagger-1 animate-fade-in-up flex items-center justify-between rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-3`}>
                  <div className="flex-1">
                    <p className="text-sm text-syzygy-grey-light">{p.change}</p>
                    <p className="mt-0.5 text-xs text-syzygy-grey/40">{p.rationale}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-syzygy-gold/60">+{(p.expected_impact * 100).toFixed(0)}%</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleApply(p.id)}
                      disabled={applying === p.id}
                      className="text-green-400 hover:text-green-300"
                    >
                      {applying === p.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!evaluation && !running && (
        <div className="flex flex-col items-center gap-3 py-12 text-center">
          <Sparkles className="h-8 w-8 text-syzygy-gold/20" />
          <p className="text-sm text-syzygy-grey/40">Submit an output above to evaluate and generate self-improvement proposals</p>
        </div>
      )}
    </div>
  );
}
