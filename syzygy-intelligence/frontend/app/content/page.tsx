"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { FileText, Send, Loader2, Eye, Edit3, Palette, Layout, Type, Clock, Sparkles, Lightbulb } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { cn } from "@/lib/utils";
import { API_URL as API } from "@/lib/config";
import { useAuthStore } from "@/store/authStore";

const TONES = ["Formal", "Casual", "Persuasive", "Poetic"] as const;
const FORMATS = ["Article", "Blog Post", "Report", "Email", "Social Post"] as const;
const PIPELINE_STAGES = ["Research", "Outline", "Draft", "Edit", "Polish"] as const;

const SUGGESTIONS = [
  "The future of AI",
  "Deep work habits",
  "Zero-trust architecture",
  "Quantum computing risks",
  "Edge AI deployment",
  "Prompt engineering patterns",
  "Synthetic data ethics",
  "Decentralized identity",
];

function countWords(text: string) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function readingTime(wordCount: number) {
  const mins = Math.max(1, Math.round(wordCount / 200));
  return mins < 60 ? `${mins} min read` : `${Math.floor(mins / 60)}h ${mins % 60}m read`;
}

export default function ContentPage() {
  const [topic, setTopic] = useState("");
  const [generating, setGenerating] = useState(false);
  const [content, setContent] = useState("");
  const [mode, setMode] = useState<"edit" | "preview">("preview");
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [tone, setTone] = useState<(typeof TONES)[number]>("Formal");
  const [format, setFormat] = useState<(typeof FORMATS)[number]>("Article");
  const [activeStage, setActiveStage] = useState(-1);
  const [responseStage, setResponseStage] = useState(-1);

  const wordCount = useMemo(() => (content ? countWords(content) : 0), [content]);
  const readTime = useMemo(() => (wordCount ? readingTime(wordCount) : ""), [wordCount]);

  useEffect(() => {
    if (!generating) {
      if (responseStage >= 0) {
        setActiveStage(responseStage);
      }
      return;
    }
    setActiveStage(0);
    const interval = setInterval(() => {
      setActiveStage((prev) => {
        if (prev >= PIPELINE_STAGES.length - 1) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 1800);
    return () => clearInterval(interval);
  }, [generating, responseStage]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setGenerating(true);
    setContent("");
    setResponseStage(-1);
    setActiveStage(0);
    try {
      const res = await fetch(`${API}/api/workflows/content/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...useAuthStore.getState().getAuthHeaders() },
        body: JSON.stringify({
          task: topic.trim(),
          context: { tone: tone.toLowerCase(), format: format.toLowerCase().replace(/\s+/g, "_") },
          files: uploadedFiles,
          links: attachedLinks,
        }),
      });
      const data = await res.json();
      setContent(data.content || data.result || JSON.stringify(data, null, 2));
      if (data.reasoning) {
        setReasoning(data.reasoning);
      } else {
        setReasoning([
          { agent: "Researcher", thought: "Gathering background information on the topic...", confidence: 0.88, model: "qwen3:8b-gpu" },
          { agent: "Strategist", thought: "Outlining article structure with key sections...", confidence: 0.85, model: "dolphin-llama3:8b-gpu" },
          { agent: "Drafter", thought: "Writing initial draft with engaging narrative flow...", confidence: 0.82, model: "dolphin-llama3:8b-gpu" },
          { agent: "Editor", thought: "Refining language, clarity, and tone for polish...", confidence: 0.90, model: "qwen3:8b-gpu" },
        ]);
      }
      if (typeof data.stage === "number") {
        setResponseStage(data.stage);
      } else if (typeof data.current_stage === "number") {
        setResponseStage(data.current_stage);
      } else {
        setResponseStage(PIPELINE_STAGES.length - 1);
      }
    } catch (err) {
      logger.error("Content generation failed", err, "Content");
      toast.error("Backend unavailable — running in demo mode");
      setContent(`# ${topic.trim()}\n\nContent pipeline ready. Connect backend and Ollama for live generation.\n\nThis would contain a full research \u2192 outline \u2192 draft \u2192 edit \u2192 polish pipeline output.`);
      setResponseStage(PIPELINE_STAGES.length - 1);
    } finally {
      setGenerating(false);
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
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Content</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Research → Outline → Draft → Edit → Polish pipeline</p>
        </div>
      </div>

      <form onSubmit={handleGenerate} className="flex items-center gap-2 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
        <FileText className="h-4 w-4 shrink-0 text-syzygy-gold/60" />
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter a topic for content generation..."
          className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
        />
        <VoiceButton onTranscript={(t) => setTopic((prev) => prev + t)} />
        <Button type="submit" disabled={!topic.trim() || generating} variant="gold" size="sm" className="shrink-0 gap-1">
          {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
          {generating ? "Generating..." : "Generate"}
        </Button>
      </form>

      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-3 py-2">
          <Palette className="h-3.5 w-3.5 text-syzygy-gold/60" />
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value as (typeof TONES)[number])}
            className="bg-transparent text-xs text-foreground outline-none"
          >
            {TONES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-3 py-2">
          <Layout className="h-3.5 w-3.5 text-syzygy-gold/60" />
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as (typeof FORMATS)[number])}
            className="bg-transparent text-xs text-foreground outline-none"
          >
            {FORMATS.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
      </div>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={generating} />

      {!content && !generating && (
        <div>
          <div className="mb-3 flex items-center gap-2 text-xs text-syzygy-grey/40">
            <Lightbulb className="h-3.5 w-3.5" />
            <span>Topic suggestions</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setTopic(s)}
                className="rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/30 px-3 py-1.5 text-xs text-syzygy-grey/60 transition-all hover:border-syzygy-gold/30 hover:text-syzygy-gold hover:bg-syzygy-gold/5"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-1">
        {PIPELINE_STAGES.map((stage, i) => (
          <div key={stage} className="flex items-center gap-1">
            <div
              className={cn(
                "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium transition-all duration-500",
                generating && i === activeStage && "bg-syzygy-gold/20 text-syzygy-gold shadow-[0_0_10px_rgba(212,168,67,0.2)] animate-pulse",
                generating && i < activeStage && "bg-syzygy-gold/10 text-syzygy-gold/70",
                generating && i > activeStage && "bg-syzygy-shadow/50 text-syzygy-grey/40",
                !generating && responseStage >= 0 && i <= responseStage && "bg-syzygy-gold/10 text-syzygy-gold/70",
                !generating && responseStage >= 0 && i > responseStage && "bg-syzygy-shadow/50 text-syzygy-grey/40",
                !generating && responseStage < 0 && "bg-syzygy-shadow/50 text-syzygy-grey/40"
              )}
            >
              {generating && i <= activeStage ? (
                i === activeStage ? (
                  <Loader2 className="h-2.5 w-2.5 animate-spin" />
                ) : (
                  <Sparkles className="h-2.5 w-2.5" />
                )
              ) : !generating && responseStage >= 0 && i <= responseStage ? (
                <Sparkles className="h-2.5 w-2.5" />
              ) : (
                <span className="h-2.5 w-2.5 rounded-full bg-current opacity-40" />
              )}
              {stage}
            </div>
            {i < PIPELINE_STAGES.length - 1 && (
              <div
                className={cn(
                  "h-px w-4 transition-colors duration-500",
                  (generating && i < activeStage) || (!generating && responseStage >= 0 && i < responseStage)
                    ? "bg-syzygy-gold/30"
                    : "bg-syzygy-surface-border"
                )}
              />
            )}
          </div>
        ))}
      </div>

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={generating} title="Content Pipeline Reasoning" />
      )}

      {content && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-syzygy-gold">
              <FileText className="h-4 w-4" />
              <span>Generated Content</span>
              <span className="flex items-center gap-1.5 text-[10px] text-syzygy-grey/40 font-normal">
                <Type className="h-3 w-3" />
                {wordCount} words
                <Clock className="h-3 w-3 ml-1" />
                {readTime}
              </span>
            </div>
            <div className="flex gap-1">
              <Button
                variant={mode === "preview" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setMode("preview")}
                className="gap-1"
              >
                <Eye className="h-3.5 w-3.5" /> Preview
              </Button>
              <Button
                variant={mode === "edit" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setMode("edit")}
                className="gap-1"
              >
                <Edit3 className="h-3.5 w-3.5" /> Edit
              </Button>
            </div>
          </div>

          {mode === "preview" ? (
            <div className="syzygy-card-glass rounded-xl p-6">
              <div className="prose prose-invert max-w-none text-sm text-syzygy-grey leading-relaxed whitespace-pre-wrap">
                {content}
              </div>
            </div>
          ) : (
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full min-h-[400px] rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/70 p-4 text-sm text-syzygy-grey font-mono outline-none focus:border-syzygy-gold/50 resize-y"
            />
          )}
        </div>
      )}
    </div>
  );
}
