"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Loader2, Zap, Brain, TrendingUp, CheckCircle2, XCircle, ArrowRight, RefreshCw, Sparkles, BarChart3, Download, FileText, Lightbulb, GitCompare, Target, X } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { cn, formatDate } from "@/lib/utils";

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

interface HistoryEntry {
  score: number;
  timestamp: string;
  label?: string;
}

export default function ImprovePage() {
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [proposals, setProposals] = useState<any[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [applying, setApplying] = useState<string | null>(null);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [selectedProposal, setSelectedProposal] = useState<any | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/meta/summary`)
      .then((r) => r.json())
      .then(setSummary)
      .catch(() => {
        logger.warn("Could not fetch improvement summary", undefined, "Improve");
      });
    fetch(`${API}/api/meta/history`)
      .then((r) => r.json())
      .then((data) => setHistory(Array.isArray(data) ? data.slice(-6) : []))
      .catch(() => {
        logger.warn("Could not fetch evaluation history", undefined, "Improve");
      });
  }, []);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setRunning(true);
    try {
      const res = await fetch(`${API}/api/meta/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output: input.trim(), context: { source: "manual", files: uploadedFiles, links: attachedLinks } }),
      });
      const data = await res.json();
      setEvaluation(data.evaluation);
      setProposals(data.proposals);
      const sumRes = await fetch(`${API}/api/meta/summary`);
      setSummary(await sumRes.json());
      const histRes = await fetch(`${API}/api/meta/history`);
      const histData = await histRes.json();
      setHistory(Array.isArray(histData) ? histData.slice(-6) : []);
      if (data.reasoning) {
        setReasoning(data.reasoning);
      } else {
        setReasoning([
          { agent: "Critic", thought: "Evaluating output across 5 quality dimensions...", confidence: 0.90, model: "qwen3:8b-gpu" },
          { agent: "Strategist", thought: "Identifying highest-impact improvement areas...", confidence: 0.85, model: "qwen3:8b-gpu" },
          { agent: "Innovator", thought: "Generating concrete proposals for each gap...", confidence: 0.82, model: "dolphin-llama3:8b-gpu" },
        ]);
      }
    } catch (err) {
      logger.error("Evaluation failed", err, "Improve");
      toast.error("Backend unavailable — running in demo mode");
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
      if (selectedProposal?.id === proposalId) setSelectedProposal(null);
      toast.success("Proposal applied");
    } catch (err) {
      logger.error("Apply proposal failed", err, "Improve");
      toast.error("Failed to apply proposal");
    }
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
      const histRes = await fetch(`${API}/api/meta/history`);
      const histData = await histRes.json();
      setHistory(Array.isArray(histData) ? histData.slice(-6) : []);
    } catch (err) {
      logger.error("Auto-improve cycle failed", err, "Improve");
      toast.error("Auto-improve cycle failed");
    }
    setRunning(false);
  };

  const handleExportReport = async () => {
    setExporting(true);
    try {
      const lines: string[] = [
        "# Self-Improvement Evaluation Report",
        `**Date:** ${new Date().toISOString()}`,
        "",
      ];
      if (summary) {
        lines.push(
          "## Summary",
          `- Total Evaluations: ${summary.total_evaluations}`,
          `- Average Score: ${(summary.average_score * 100).toFixed(0)}%`,
          `- Latest Score: ${(summary.latest_score * 100).toFixed(0)}%`,
          `- Proposals Generated: ${summary.total_proposals}`,
          `- Proposals Applied: ${summary.applied_proposals}`,
          "",
        );
      }
      if (evaluation) {
        lines.push(
          "## Current Evaluation",
          `**Overall Score:** ${(evaluation.score * 100).toFixed(0)}%`,
          "",
          "### Dimensions",
          ...Object.entries(evaluation.dimensions).map(([k, v]) => `- **${k}:** ${(v * 100).toFixed(0)}%`),
          "",
          "### Feedback",
          ...evaluation.feedback.map((f) => `- ${f}`),
          "",
          "### Suggestions",
          ...evaluation.suggestions.map((s) => `- ${s}`),
          "",
        );
      }
      if (proposals.length > 0) {
        lines.push("## Proposals", ...proposals.map((p) => `- **${p.change}** — Impact: +${(p.expected_impact * 100).toFixed(0)}%`), "");
      }
      if (history.length > 0) {
        lines.push("## Score History", ...history.map((h) => `- ${formatDate(h.timestamp)}: ${(h.score * 100).toFixed(0)}%`), "");
      }
      await navigator.clipboard.writeText(lines.filter(Boolean).join("\n"));
      toast.success("Report copied to clipboard");
    } catch {
      toast.error("Failed to copy report");
    }
    setExporting(false);
  };

  const maxScore = history.length > 0 ? Math.max(...history.map((h) => h.score), 0.01) : 1;

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <img src="/branding/pagetop.logo.png" alt="Syzygy" className="h-8 w-auto brightness-110" width={32} height={32} />
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

      {/* History Trend Chart */}
      {history.length > 0 && (
        <div className="syzygy-card-glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-syzygy-gold/60" />
            <h3 className="text-sm font-medium text-syzygy-gold">Evaluation History</h3>
          </div>
          <div className="relative">
            <svg viewBox="0 0 280 64" className="w-full h-16" preserveAspectRatio="none">
              <defs>
                <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#e8c35a" />
                  <stop offset="100%" stopColor="#d4a843" />
                </linearGradient>
              </defs>
              {history.map((entry, i) => {
                const barHeight = Math.max((entry.score / maxScore) * 56, 4);
                const barWidth = 280 / history.length - 6;
                const x = i * (280 / history.length) + 3;
                return (
                  <rect key={i} x={x} y={64 - barHeight} width={barWidth} height={barHeight} rx={2} fill="url(#goldGrad)" opacity={0.85} />
                );
              })}
            </svg>
            <div className="flex justify-between mt-1">
              {history.map((entry, i) => (
                <span key={i} className="text-[9px] text-syzygy-grey/40">
                  {new Date(entry.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                </span>
              ))}
            </div>
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
          <VoiceButton onTranscript={(t) => setInput((prev) => prev + t)} />
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

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={running} />

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={running} title="Improvement Reasoning" />
      )}

      {/* Evaluation Results */}
      {evaluation && (
        <div className="animate-fade-in-up space-y-4">
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="flex items-center gap-2 text-sm font-medium text-syzygy-gold">
                <TrendingUp className="h-4 w-4" />
                Evaluation Score: {(evaluation.score * 100).toFixed(0)}%
              </h3>
              <div className="flex items-center gap-2">
                <div className="h-2 w-32 overflow-hidden rounded-full bg-syzygy-shadow">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${evaluation.score * 100}%`,
                      background: "linear-gradient(90deg, #d4a843, #e8c35a)",
                    }}
                  />
                </div>
                <Button variant="ghost" size="sm" onClick={handleExportReport} disabled={exporting} className="gap-1">
                  {exporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                  Export
                </Button>
              </div>
            </div>

            {/* Dimension Bars */}
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(evaluation.dimensions).map(([key, val], i) => (
                <div key={key} className={`stagger-${(i % 8) + 1} animate-fade-in-up space-y-1`}>
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
                  <p key={i} className={`stagger-${(i % 8) + 1} animate-fade-in-up flex items-start gap-2 text-xs text-syzygy-grey/60`}>
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
              {proposals.map((p, i) => (
                <div
                  key={p.id}
                  onClick={() => setSelectedProposal(p)}
                  className={`stagger-${(i % 8) + 1} animate-fade-in-up flex items-center justify-between rounded-xl border border-syzygy-surface-border bg-syzygy-deep/50 p-3 hover:scale-[1.02] hover:border-syzygy-gold/50 transition-all duration-300 cursor-pointer`}
                >
                  <div className="flex-1">
                    <p className="text-sm text-syzygy-grey-light">{p.change}</p>
                    <p className="mt-0.5 text-xs text-syzygy-grey/40">{p.rationale}</p>
                  </div>
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
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

      {/* Proposal Comparison Modal */}
      {selectedProposal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setSelectedProposal(null)}>
          <div className="syzygy-card-glass rounded-xl p-6 max-w-lg w-full space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-sm font-medium text-syzygy-gold">
                <GitCompare className="h-4 w-4" />
                Proposal Detail
              </h3>
              <button onClick={() => setSelectedProposal(null)} className="text-syzygy-grey/40 hover:text-syzygy-gold/60 transition-colors">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-syzygy-bone">{selectedProposal.change}</p>
              <p className="text-xs text-syzygy-grey/60">{selectedProposal.rationale}</p>
            </div>
            <div className="space-y-3">
              <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Expected Impact</p>
              {(() => {
                const beforeScore = evaluation?.dimensions?.[selectedProposal.target] ?? evaluation?.score ?? 0;
                const afterScore = Math.min(beforeScore + selectedProposal.expected_impact, 1);
                return (
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-syzygy-grey/60">Current Score</span>
                        <span className="text-syzygy-grey/40">{(beforeScore * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-syzygy-shadow">
                        <div className="h-full rounded-full bg-syzygy-grey/40 transition-all" style={{ width: `${beforeScore * 100}%` }} />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-green-400">Projected Score</span>
                        <span className="text-green-400">+{(selectedProposal.expected_impact * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-syzygy-shadow">
                        <div className="h-full rounded-full bg-green-500/60 transition-all" style={{ width: `${afterScore * 100}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-syzygy-gold/60">
                      <ArrowRight className="h-3 w-3" />
                      <span>Projected improvement: {(afterScore * 100).toFixed(0)}% overall</span>
                    </div>
                  </div>
                );
              })()}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setSelectedProposal(null)}>Close</Button>
              <Button variant="gold" size="sm" onClick={() => handleApply(selectedProposal.id)} disabled={applying === selectedProposal.id}>
                {applying === selectedProposal.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                Apply Proposal
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Empty State with Suggestion Cards */}
      {!evaluation && !running && (
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { icon: FileText, title: "Evaluate a recent output", desc: "Analyze an AI-generated response for quality", prompt: "Analyze this response: " },
            { icon: Brain, title: "Analyze decision quality", desc: "Assess reasoning and decision-making patterns", prompt: "Evaluate the decision quality of: " },
            { icon: Target, title: "Benchmark against standards", desc: "Compare output against defined quality standards", prompt: "Benchmark this output against standards: " },
            { icon: Lightbulb, title: "Review agent performance", desc: "Evaluate an agent's recent task execution", prompt: "Review the agent's performance on: " },
          ].map((card, i) => (
            <button
              key={i}
              onClick={() => setInput(card.prompt)}
              className="syzygy-card-glass rounded-xl p-4 text-left transition-all duration-300 hover:border-syzygy-gold/30 hover:scale-[1.02] group"
            >
              <card.icon className="h-5 w-5 text-syzygy-gold/40 group-hover:text-syzygy-gold/70 transition-colors mb-2" />
              <p className="text-sm text-syzygy-bone group-hover:text-syzygy-gold-light transition-colors">{card.title}</p>
              <p className="mt-1 text-xs text-syzygy-grey/40">{card.desc}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
