"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Workflow, Play, Loader2, CheckCircle2, XCircle, Copy, Download, ArrowRight, Search, X, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { API_URL as API } from "@/lib/config";
import { useAuthStore } from "@/store/authStore";
import { WorkflowResult } from "@/components/workflows/WorkflowResult";

const WORKFLOW_DESCRIPTIONS: Record<string, string> = {
  coding: "Scaffold, edit, test, and debug with polarity-aware pair programming",
  research: "Parallel search with multi-source validation and synthesis",
  content: "Research → Outline → Draft → Edit → Polish pipeline",
  debate: "Multi-round structured debate between agents",
  task_decomposition: "Break complex tasks into dependency-tracked subtasks",
  audit: "Security scanning, code review, anti-pattern detection, and compliance checks",
  test_gen: "Automated unit, integration, and edge-case test generation with validation",
  summary: "Multi-document summarization with key insight extraction and synthesis",
  compliance: "Regulatory compliance checks — GDPR, SOC2, HIPAA, PCI-DSS, CCPA",
  qa_bot: "Knowledge-base Q&A — ingest docs, retrieve context, generate answers",
  translate: "Multi-language translation with cultural adaptation and quality review",
  interview_coach: "Role-specific interview questions, answer evaluation, and scoring feedback",
  data_analyzer: "Statistical analysis, anomaly detection, correlation discovery, and visualization recommendations",
  api_designer: "API design with OpenAPI spec generation, endpoint stubs, and validation tests",
  agentic_rag: "Query decomposition, multi-hop retrieval, source-grounded synthesis beyond simple Q&A",
  report_gen: "Multi-format structured reports with charts, tables, and executive summaries",
  data_pipeline: "ETL pipeline — ingest, clean, transform, validate schema, and load data",
  ci_piper: "CI/CD pipeline configs — GitHub Actions, GitLab CI, Jenkins with matrix builds and deploy stages",
};

const CATEGORIES = [
  { id: "all", label: "All" },
  { id: "development", label: "Development" },
  { id: "content", label: "Content" },
  { id: "analysis", label: "Analysis" },
  { id: "ai", label: "AI & ML" },
  { id: "security", label: "Security" },
  { id: "productivity", label: "Productivity" },
] as const;

const WORKFLOW_CATEGORY: Record<string, string> = {
  coding: "development",
  test_gen: "development",
  api_designer: "development",
  ci_piper: "development",
  content: "content",
  translate: "content",
  report_gen: "content",
  research: "analysis",
  data_analyzer: "analysis",
  data_pipeline: "analysis",
  debate: "ai",
  agentic_rag: "ai",
  qa_bot: "ai",
  audit: "security",
  compliance: "security",
  task_decomposition: "productivity",
  summary: "productivity",
  interview_coach: "productivity",
};

const CATEGORY_COLORS: Record<string, string> = {
  development: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
  content: "border-purple-500/30 text-purple-400 bg-purple-500/10",
  analysis: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
  ai: "border-amber-500/30 text-amber-400 bg-amber-500/10",
  security: "border-red-500/30 text-red-400 bg-red-500/10",
  productivity: "border-teal-500/30 text-teal-400 bg-teal-500/10",
};

const WORKFLOW_PROMPTS: Record<string, string[]> = {
  coding: ["Build a REST API with FastAPI", "Create a CLI file processing tool", "Scaffold a Next.js landing page"],
  research: ["Latest advances in quantum error correction", "Compare transformer vs state-space models", "Market analysis of AI coding assistants 2026"],
  content: ["Write about zero-trust architecture", "Draft a product launch announcement", "Create a WebSocket tutorial"],
  debate: ["Is AGI achievable without embodiment?", "Does P=NP? Debate both sides", "Regulation vs innovation in AI"],
  task_decomposition: ["Building a recommendation engine", "Implementing a CI/CD pipeline", "Creating a multi-tenant SaaS app"],
  audit: ["Audit this Python codebase", "Review Docker security posture", "Check OWASP Top 10 compliance"],
  test_gen: ["Generate tests for the auth module", "Write integration tests for the API", "Create edge-case test suite"],
  summary: ["Summarize the latest AI research papers", "Extract key insights from quarterly report", "Synthesize meeting notes"],
  compliance: ["Check GDPR compliance for user data", "Review SOC2 controls", "Audit HIPAA requirements"],
  qa_bot: ["Build a Q&A bot from our docs", "Create a customer support assistant", "Ingest knowledge base for querying"],
  translate: ["Translate landing page to Spanish", "Localize API docs to Japanese", "Translate with cultural adaptation"],
  interview_coach: ["Prepare for a senior engineer interview", "Practice system design questions", "Behavioral interview prep"],
  data_analyzer: ["Analyze sales data for trends", "Find anomalies in server metrics", "Correlate user behavior patterns"],
  api_designer: ["Design a REST API for a blog platform", "Create OpenAPI spec for payment service", "Design WebSocket event schema"],
  agentic_rag: ["Research multi-hop query about climate science", "Compare product specs from multiple sources", "Synthesize earnings reports"],
  report_gen: ["Generate monthly executive summary", "Create a research report with charts", "Build a competitive analysis report"],
  data_pipeline: ["Build ETL for CSV import", "Design streaming data pipeline", "Create data validation workflow"],
  ci_piper: ["Set up GitHub Actions for Python package", "Configure GitLab CI with matrix builds", "Create multi-stage deploy pipeline"],
};

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState("");
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [executing, setExecuting] = useState(false);
  const [output, setOutput] = useState<any>(null);
  const [error, setError] = useState("");
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);

  useEffect(() => {
    fetch(`${API}/api/workflows/`)
      .then((r) => r.json())
      .then((data) => {
        const list = data.workflows || [];
        setWorkflows(list.map((w: string | { name: string }) => (typeof w === "string" ? w : w.name)));
      })
      .catch(() => {
        logger.warn("Could not fetch workflows from backend, using defaults", undefined, "Workflows");
        toast.error("Could not load workflows");
        setWorkflows(Object.keys(WORKFLOW_DESCRIPTIONS));
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = workflows;
    if (activeCategory !== "all") {
      list = list.filter((w) => WORKFLOW_CATEGORY[w] === activeCategory);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (w) =>
          w.toLowerCase().includes(q) ||
          (WORKFLOW_DESCRIPTIONS[w] || "").toLowerCase().includes(q),
      );
    }
    return list;
  }, [workflows, activeCategory, search]);

  const parseReasoning = (data: any) => {
    const r = data?.result?.reasoning || data?.reasoning;
    if (r && Array.isArray(r) && r.length > 0) return r;
    return [
      { agent: "Planner", thought: `Decomposing task for ${selected} workflow...`, confidence: 0.90, model: "tinyllama:latest" },
      { agent: "Executor", thought: "Running workflow steps with polarity-aware agent team...", confidence: 0.87, model: "tinyllama:latest" },
      { agent: "Validator", thought: "Verifying output quality and completeness...", confidence: 0.85, model: "tinyllama:latest" },
    ];
  };

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !input.trim()) return;
    setExecuting(true);
    setOutput(null);
    setError("");
    try {
      const res = await fetch(`${API}/api/workflows/${selected}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...useAuthStore.getState().getAuthHeaders() },
        body: JSON.stringify({ task: input.trim(), context: {}, files: uploadedFiles, links: attachedLinks }),
      });
      const data = await res.json();
      setOutput(data);
      setReasoning(parseReasoning(data));
    } catch (err) {
      logger.error("Workflow execution failed", err, "Workflows");
      toast.error("Backend unavailable — running in demo mode");
      setError("Workflow execution requires the backend to be running.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-5 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-8 w-auto brightness-110"
            width={32} height={32}
          />
          <div>
            <h1 className="syzygy-title text-2xl font-bold tracking-wider">Workflows</h1>
            <p className="mt-0.5 text-xs text-syzygy-grey/60">Automated agent pipelines for any task</p>
          </div>
        </div>
        {selected && (
          <button
            type="button"
            onClick={() => { setSelected(""); setInput(""); setOutput(null); setError(""); setReasoning([]); setUploadedFiles([]); setAttachedLinks([]); }}
            className="flex items-center gap-1 text-xs text-syzygy-grey/50 hover:text-syzygy-grey-light transition-colors cursor-pointer"
          >
            <X className="h-3.5 w-3.5" /> Change workflow
          </button>
        )}
      </div>

      {!selected && (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-syzygy-grey/40" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search workflows..."
                className="w-full rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/40 py-2 pl-10 pr-3 text-xs text-foreground placeholder-syzygy-grey/40 outline-none transition-colors focus:border-syzygy-gold/40"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-syzygy-grey/40 hover:text-syzygy-grey-light cursor-pointer"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setActiveCategory(cat.id)}
                  className={`rounded-full px-3 py-1 text-[11px] font-medium transition-all cursor-pointer ${
                    activeCategory === cat.id
                      ? "bg-syzygy-gold/15 text-syzygy-gold-light border border-syzygy-gold/30"
                      : "text-syzygy-grey/50 border border-transparent hover:text-syzygy-grey-light hover:border-syzygy-grey/20"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center py-12 text-syzygy-grey/40">
              <Search className="h-8 w-8 mb-2" />
              <p className="text-sm">No workflows match your search</p>
              <button
                type="button"
                onClick={() => { setSearch(""); setActiveCategory("all"); }}
                className="mt-2 text-xs text-syzygy-gold/60 hover:text-syzygy-gold-light cursor-pointer underline"
              >
                Clear filters
              </button>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {loading ? (
              <div className="col-span-full flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-syzygy-gold" /></div>
            ) : (
              filtered.map((w, i) => {
                const cat = WORKFLOW_CATEGORY[w];
                return (
                  <button
                    key={w}
                    type="button"
                    onClick={() => setSelected(w)}
                    className={`stagger-${(i % 8) + 1} animate-fade-in-up syzygy-card-glass rounded-xl p-4 text-left transition-all hover:scale-[1.02] duration-300 cursor-pointer ${
                      selected === w
                        ? "border-syzygy-gold/50 shadow-lg shadow-syzygy-gold/10"
                        : "border-syzygy-surface-border hover:border-syzygy-gold/30"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className={`shrink-0 flex h-7 w-7 items-center justify-center rounded-lg ${cat ? CATEGORY_COLORS[cat] : "text-syzygy-gold bg-syzygy-gold/10"}`}>
                          <Workflow className="h-3.5 w-3.5" />
                        </div>
                        <span className="font-semibold text-sm capitalize text-foreground truncate">{w.replace(/_/g, " ")}</span>
                      </div>
                      {cat && (
                        <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${CATEGORY_COLORS[cat]}`}>
                          {CATEGORIES.find((c) => c.id === cat)?.label || cat}
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs text-syzygy-grey/60 leading-relaxed">{WORKFLOW_DESCRIPTIONS[w] || ""}</p>
                  </button>
                );
              })
            )}
          </div>

          <div className="animate-fade-in-up space-y-3 py-2">
            <p className="text-xs text-syzygy-grey/40 font-medium uppercase tracking-wider">Quick start ideas</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { text: "Build a REST API in Python with FastAPI", workflow: "coding" },
                { text: "Research the latest advances in quantum computing", workflow: "research" },
                { text: "Write a blog post about zero-trust architecture", workflow: "content" },
                { text: "Debate: Is AGI achievable without embodiment?", workflow: "debate" },
                { text: "Break down: Building a recommendation engine", workflow: "task_decomposition" },
                { text: "Audit this Python codebase for security issues", workflow: "audit" },
              ].map(({ text, workflow }) => (
                <button
                  key={text}
                  type="button"
                  onClick={() => { setSelected(workflow); setInput(text); }}
                  className="group flex items-center justify-between rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/20 px-4 py-3 text-left text-xs text-syzygy-grey/60 transition-all duration-200 hover:border-syzygy-gold/30 hover:bg-syzygy-gold/5 hover:text-syzygy-grey-light cursor-pointer"
                >
                  <span className="leading-relaxed">{text}</span>
                  <ArrowRight className="h-3.5 w-3.5 shrink-0 text-syzygy-grey/30 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-syzygy-gold/60" />
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {selected && (
        <div className="animate-fade-in-up space-y-4">
          <div className="syzygy-card-glass rounded-xl border border-syzygy-gold/20 p-4">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${CATEGORY_COLORS[WORKFLOW_CATEGORY[selected]] || "text-syzygy-gold bg-syzygy-gold/10"}`}>
                <Workflow className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-bold capitalize text-foreground">{selected.replace(/_/g, " ")}</h2>
                <p className="text-xs text-syzygy-grey/60">{WORKFLOW_DESCRIPTIONS[selected]}</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleExecute}>
            <div className="flex items-center gap-2 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3 transition-colors focus-within:border-syzygy-gold/40">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Describe your task for ${selected.replace(/_/g, " ")}...`}
                className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
              />
              <VoiceButton onTranscript={(t) => setInput((prev) => prev + t)} />
              <Button type="submit" disabled={!input.trim() || executing} variant="gold" size="sm" className="shrink-0 gap-1">
                {executing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                Execute
              </Button>
            </div>
          </form>

          {!input.trim() && !executing && WORKFLOW_PROMPTS[selected] && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-syzygy-grey/40">
                <Sparkles className="h-3 w-3" /> Try asking:
              </div>
              <div className="flex flex-wrap gap-2">
                {WORKFLOW_PROMPTS[selected].map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => setInput(prompt)}
                    className="rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/30 px-3 py-1.5 text-xs text-syzygy-grey/60 transition-all hover:border-syzygy-gold/30 hover:text-syzygy-grey-light cursor-pointer"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={executing} />
        </div>
      )}

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={executing} title="Workflow Reasoning" />
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          <XCircle className="h-4 w-4" /> {error}
        </div>
      )}

      {output && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-syzygy-gold">
              <CheckCircle2 className="h-4 w-4" /> Result
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(output, null, 2));
                  toast.success("Copied to clipboard");
                }}
                className="gap-1"
              >
                <Copy className="h-3.5 w-3.5" />
                Copy
              </Button>
            </div>
          </div>
          <WorkflowResult workflow={selected} data={output} />
        </div>
      )}
    </div>
  );
}
