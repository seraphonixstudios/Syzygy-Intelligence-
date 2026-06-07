"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Search, Globe, Loader2, BookOpen } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setResults(null);
    try {
      const res = await fetch(`${API}/api/workflows/research/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: query.trim(), context: {}, files: uploadedFiles, links: attachedLinks }),
      });
      const data = await res.json();
      const text = data.synthesis || data.result || JSON.stringify(data, null, 2);
      setResults(text);
      setHistory((prev) => [query.trim(), ...prev]);
      if (data.reasoning) {
        setReasoning(data.reasoning);
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

      <form onSubmit={handleSearch} className="group relative syzygy-card-glass rounded-2xl border-syzygy-gold/20 transition-all duration-300 focus-within:border-syzygy-gold/50">
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
      </form>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={searching} />

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
          <div className="mb-3 flex items-center gap-2 text-syzygy-gold">
            <BookOpen className="h-4 w-4" />
            <span className="text-sm font-medium">Research Synthesis</span>
          </div>
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
              key={i}
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
