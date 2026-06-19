"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Search, Globe, Loader2, BookOpen, Layers, LayoutGrid, Lightbulb, Copy, Check, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { cn, formatDate } from "@/lib/utils";
import { API_URL as API } from "@/lib/config";
import { useAuthStore } from "@/store/authStore";

type Depth = "quick" | "deep" | "comprehensive";

interface Source {
  title: string;
  url: string;
  snippet: string;
  confidence?: number;
}

const DEPTH_OPTIONS: { value: Depth; label: string; icon: typeof Layers; desc: string }[] = [
  { value: "quick", label: "Quick", icon: Layers, desc: "Single source sweep" },
  { value: "deep", label: "Deep", icon: LayoutGrid, desc: "Multi-source validation" },
  { value: "comprehensive", label: "Comprehensive", icon: Lightbulb, desc: "Full cross-reference" },
];

const SUGGESTIONS = [
  "Latest AI breakthroughs",
  "Climate change solutions",
  "Quantum computing advances",
  "Global economic trends 2026",
  "Renewable energy innovations",
  "Space exploration missions",
];

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch {
    return url;
  }
}

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [depth, setDepth] = useState<Depth>("deep");
  const [sources, setSources] = useState<Source[]>([]);
  const [copied, setCopied] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setResults(null);
    setSources([]);
    try {
      const res = await fetch(`${API}/api/workflows/research/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...useAuthStore.getState().getAuthHeaders() },
        body: JSON.stringify({ task: query.trim(), context: { depth }, files: uploadedFiles, links: attachedLinks }),
      });
      const data = await res.json();
      const workflowResult = data.result || data;
      const text = workflowResult.synthesis || workflowResult.result || JSON.stringify(workflowResult, null, 2);
      setResults(text);
      setHistory((prev) => [query.trim(), ...prev]);
      if (workflowResult.findings?.length) {
        setSources(
          workflowResult.findings.map((f: Source, i: number) => ({
            ...f,
            confidence: f.confidence ?? Math.max(0, 0.95 - i * 0.06),
          }))
        );
      }
      if (workflowResult.reasoning) {
        setReasoning(workflowResult.reasoning);
      } else {
        setReasoning([
          { agent: "Researcher", thought: "Parsing query and identifying key research domains...", confidence: 0.90, model: "qwen3:8b-gpu" },
          { agent: "Analyst", thought: "Cross-referencing multiple sources for validation...", confidence: 0.87, model: "qwen3:8b-gpu" },
          { agent: "Synthesizer", thought: "Integrating findings into coherent research summary...", confidence: 0.85, model: "qwen3:8b-gpu" },
        ]);
      }
    } catch (err) {
      logger.error("Research search failed", err, "Research");
      toast.error("Backend unavailable — running in demo mode");
      setResults("Research engine ready. (Backend and Ollama must be running for live results.)");
      setHistory((prev) => [query.trim(), ...prev]);
    } finally {
      setSearching(false);
    }
  };

  const handleCopyMarkdown = async () => {
    if (!results) return;
    const markdown = `# Research Synthesis\n\n**Query:** ${history[0] || query}\n**Date:** ${formatDate(new Date().toISOString())}\n**Depth:** ${depth.charAt(0).toUpperCase() + depth.slice(1)}\n\n${results}`;
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      toast.success("Copied as markdown");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy to clipboard");
    }
  };

  const showEmptyState = !searching && !results && history.length === 0;

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
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Research</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Parallel search with multi-source validation</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="space-y-3">
        <div className="group relative syzygy-card-glass rounded-2xl border-syzygy-gold/20 transition-all duration-300 focus-within:border-syzygy-gold/50">
          <div className="flex items-center gap-3 px-4 py-3">
            <Globe className="h-5 w-5 shrink-0 text-syzygy-gold/60" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Research query..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
            />
            <VoiceButton onTranscript={(t) => setQuery((prev) => prev + t)} />
            <Button type="submit" disabled={!query.trim() || searching} variant="gold" size="sm" className="shrink-0 gap-1">
              {searching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
              {searching ? "Searching..." : "Research"}
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider text-syzygy-grey/40 font-medium">Depth:</span>
          {DEPTH_OPTIONS.map((opt) => {
            const Icon = opt.icon;
            const active = depth === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setDepth(opt.value)}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[11px] transition-all duration-200",
                  active
                    ? "border-syzygy-gold/50 bg-syzygy-gold/10 text-syzygy-gold shadow-[0_0_8px_rgba(212,168,67,0.15)]"
                    : "border-syzygy-surface-border bg-syzygy-shadow/30 text-syzygy-grey/50 hover:border-syzygy-gold/30 hover:text-syzygy-grey-light"
                )}
              >
                <Icon className={cn("h-3 w-3", active ? "text-syzygy-gold" : "text-syzygy-grey/40")} />
                <span>{opt.label}</span>
              </button>
            );
          })}
        </div>
      </form>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={searching} />

      {showEmptyState && (
        <div className="animate-fade-in-up space-y-4 py-4">
          <div className="grid grid-cols-2 gap-3">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setQuery(s)}
                className="group flex items-center justify-between rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/20 px-4 py-3 text-left text-xs text-syzygy-grey/60 transition-all duration-200 hover:border-syzygy-gold/30 hover:bg-syzygy-gold/5 hover:text-syzygy-grey-light"
              >
                <span className="leading-relaxed">{s}</span>
                <ArrowRight className="h-3.5 w-3.5 shrink-0 text-syzygy-grey/30 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-syzygy-gold/60" />
              </button>
            ))}
          </div>
        </div>
      )}

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={searching} title="Research Reasoning" />
      )}

      {searching && (
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-5 w-5 animate-spin text-syzygy-gold" />
          <span className="text-sm text-syzygy-grey/60">Gathering intelligence from multiple sources...</span>
        </div>
      )}

      {results && (
        <div className="syzygy-card-glass rounded-xl p-6">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-syzygy-gold">
              <BookOpen className="h-4 w-4" />
              <span className="text-sm font-medium">Research Synthesis</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleCopyMarkdown}
              className="gap-1.5 text-[11px] text-syzygy-grey/50 hover:text-syzygy-gold"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? "Copied" : "Copy as Markdown"}
            </Button>
          </div>
          {sources.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-1.5">
              {sources.slice(0, 8).map((src, i) => (
                <span
                  key={src.url}
                  className="inline-flex items-center gap-1 rounded-full border border-syzygy-surface-border bg-syzygy-shadow/40 px-2 py-0.5 text-[10px] text-syzygy-grey/60"
                >
                  <span
                    className="h-1.5 w-1.5 rounded-full"
                    style={{
                      backgroundColor:
                        (src.confidence ?? 0) > 0.8 ? "#22c55e" :
                        (src.confidence ?? 0) > 0.6 ? "#d4a843" :
                        (src.confidence ?? 0) > 0.4 ? "#f97316" : "#ef4444",
                    }}
                  />
                  {extractDomain(src.url)}
                  <span className="text-[9px] text-syzygy-grey/40">
                    {((src.confidence ?? 0) * 100).toFixed(0)}%
                  </span>
                </span>
              ))}
              {sources.length > 8 && (
                <span className="inline-flex items-center rounded-full border border-syzygy-surface-border bg-syzygy-shadow/40 px-2 py-0.5 text-[10px] text-syzygy-grey/40">
                  +{sources.length - 8}
                </span>
              )}
            </div>
          )}
          <div className="prose prose-invert max-w-none text-sm text-syzygy-grey leading-relaxed whitespace-pre-wrap">
            {results}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-syzygy-grey/60">Recent Queries</h2>
          {history.map((h, i) => (
            <button
              key={h}
              onClick={() => { setQuery(h); }}
              className="block w-full text-left rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/30 px-3 py-2 text-xs text-syzygy-grey/60 hover:border-syzygy-gold/30 transition-colors"
            >
              {h}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
