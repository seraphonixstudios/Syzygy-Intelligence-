"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import {
  CodeXml, Play, Loader2, Copy, CheckCircle2, Terminal, Sparkles,
  Shield, FileCode, FileJson, Braces, AlertTriangle, Hash, Type
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { logger } from "@/lib/logger";
import { API_URL as API } from "@/lib/config";
import { useAuthStore } from "@/store/authStore";

const languageOptions = ["python", "javascript", "typescript", "go", "rust", "bash"];

const suggestions = [
  { label: "A REST API in Python", icon: FileCode },
  { label: "Data visualization in JS", icon: FileJson },
  { label: "CLI tool in Go", icon: Terminal },
  { label: "Web scraper in Rust", icon: Braces },
];

const defaultReviews = [
  { category: "Security", status: "ok", message: "No vulnerabilities detected" },
  { category: "Performance", status: "ok", message: "No performance issues" },
  { category: "Style", status: "warning", message: "Minor style issues", count: 2 },
  { category: "Complexity", status: "ok", message: "Maintainable complexity" },
];

function getFileIcon(language: string) {
  switch (language) {
    case "python": return FileCode;
    case "javascript":
    case "typescript": return FileJson;
    case "go": return Terminal;
    case "rust": return Braces;
    default: return FileCode;
  }
}

export default function CodePage() {
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState("python");
  const inputRef = useRef<HTMLInputElement>(null);
  const [showLangPicker, setShowLangPicker] = useState(false);
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [codeFiles, setCodeFiles] = useState<{ path: string; language: string; content: string }[]>([]);
  const [activeFileIndex, setActiveFileIndex] = useState(0);
  const [reviews, setReviews] = useState<{ category: string; status: string; message: string; count?: number }[]>([]);

  const activeFile = codeFiles[activeFileIndex] || null;
  const code = activeFile?.content || "";
  const wordCount = code ? code.split(/\s+/).filter(Boolean).length : 0;
  const lineCount = code ? code.split("\n").length : 0;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (activeFileIndex >= codeFiles.length) {
      setActiveFileIndex(0);
    }
  }, [codeFiles.length]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setGenerating(true);
    setCodeFiles([]);
    setActiveFileIndex(0);
    setReviews([]);
    try {
      const res = await fetch(`${API}/api/workflows/coding/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...useAuthStore.getState().getAuthHeaders() },
        body: JSON.stringify({ task: prompt.trim(), context: { language }, files: uploadedFiles, links: attachedLinks }),
      });
      const data = await res.json();
      if (data.files && Array.isArray(data.files) && data.files.length > 0) {
        setCodeFiles(data.files);
      } else {
        setCodeFiles([{ path: "output", language, content: data.code || data.result || JSON.stringify(data, null, 2) }]);
      }
      setActiveFileIndex(0);
      if (data.reasoning) {
        setReasoning(data.reasoning);
      } else {
        setReasoning([
          { agent: "Architect", thought: "Designing solution structure and identifying optimal approach...", confidence: 0.92, model: "qwen3:8b-gpu" },
          { agent: "Implementer", thought: `Writing ${language} code with best practices and error handling...`, confidence: 0.88, model: "qwen3:8b-gpu" },
          { agent: "Reviewer", thought: "Checking for edge cases, performance issues, and security concerns...", confidence: 0.85, model: "qwen3:8b-gpu" },
        ]);
      }
      if (data.review) {
        setReviews(data.review);
      }
    } catch (err) {
      logger.error("Code generation failed", err, "Code");
      toast.error("Backend unavailable — running in demo mode");
      setCodeFiles([{ path: "main", language, content: `// ${language.toUpperCase()} — Generation Ready\n// Backend must be running for live results.\n// Your code will appear here.` }]);
      setActiveFileIndex(0);
      setReviews(defaultReviews);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <img
          src="/branding/pagetop.logo.png"
          alt="Syzygy"
          className="h-8 w-auto brightness-110"
          width={32} height={32}
        />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Code</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Generate, review, and refine code with your agent team</p>
        </div>
      </div>

      <form onSubmit={handleGenerate} className="space-y-3">
        <div className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3 transition-all duration-300 focus-within:border-syzygy-gold/50 focus-within:shadow-lg focus-within:shadow-syzygy-gold/10">
          <Terminal className="h-4 w-4 shrink-0 text-syzygy-gold/60" />
          <input
            ref={inputRef}
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="What code would you like me to write?"
            className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
          />
          <VoiceButton onTranscript={(t) => setPrompt((prev) => prev + t)} />
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowLangPicker(!showLangPicker)}
              className="rounded-md border border-syzygy-surface-border bg-syzygy-deep px-2 py-1 text-[10px] uppercase text-syzygy-grey/60 hover:text-syzygy-gold transition-colors"
            >
              {language}
            </button>
            {showLangPicker && (
              <div className="absolute right-0 top-full z-50 mt-1 overflow-hidden rounded-lg border border-syzygy-surface-border bg-syzygy-deep/95 backdrop-blur-xl shadow-xl animate-scale-in">
                {languageOptions.map((lang, i) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => { setLanguage(lang); setShowLangPicker(false); }}
                    className={`stagger-${(i % 8) + 1} animate-fade-in-up block w-full px-4 py-2 text-left text-xs text-syzygy-grey-light hover:bg-syzygy-gold/10 hover:text-syzygy-gold-light hover:scale-[1.02] transition-all duration-300`}
                  >
                    {lang}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button type="submit" disabled={!prompt.trim() || generating} variant="gold" size="sm" className="shrink-0 gap-1">
            {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{generating ? "Generating..." : "Generate"}</span>
          </Button>
        </div>
      </form>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={generating} />

      {reasoning.length > 0 && (
        <ReasoningPanel steps={reasoning} loading={generating} title="Code Generation Reasoning" />
      )}

      {(codeFiles.length > 0 || generating) && (
        <div className="animate-fade-in-up space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-syzygy-gold">
              <CodeXml className="h-4 w-4" />
              {generating ? (
                <span className="flex items-center gap-2">
                  <span className="typing-cursor">Generating</span>
                  <span className="progress-bar-indeterminate h-1 w-24 rounded-full bg-syzygy-gold/20" />
                </span>
              ) : (
                "Output"
              )}
            </div>
            {code && !generating && (
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-syzygy-grey/40">{activeFile?.language.toUpperCase() || language.toUpperCase()}</span>
                <Button variant="ghost" size="sm" onClick={handleCopy} className="gap-1">
                  {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
            )}
          </div>

          {codeFiles.length > 1 && !generating && (
            <div className="flex items-center gap-1 border-b border-syzygy-surface-border pb-1 overflow-x-auto">
              {codeFiles.map((f, i) => {
                const Icon = getFileIcon(f.language);
                return (
                  <button
                    key={f.path}
                    onClick={() => setActiveFileIndex(i)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-t-md text-xs transition-all whitespace-nowrap",
                      i === activeFileIndex
                        ? "bg-syzygy-gold/10 text-syzygy-gold border-b-2 border-syzygy-gold"
                        : "text-syzygy-grey/50 hover:text-syzygy-grey/80 hover:bg-syzygy-obsidian"
                    )}
                  >
                    <Icon className="h-3 w-3" />
                    {f.path}
                  </button>
                );
              })}
            </div>
          )}

          <pre className="relative overflow-auto rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/70 p-4 text-xs text-syzygy-grey/90 font-mono leading-relaxed max-h-96">
            {generating ? (
              <div className="flex items-center gap-3 py-8">
                <div className="ouroboros-ring h-6 w-6" />
                <span className="text-syzygy-gold/60 animate-pulse">Crafting solution...</span>
              </div>
            ) : (
              <code className="whitespace-pre">{code}</code>
            )}
          </pre>

          {code && !generating && (
            <div className="flex items-center gap-3 text-[10px] text-syzygy-grey/40">
              <span className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {lineCount} lines
              </span>
              <span className="flex items-center gap-1">
                <Type className="h-3 w-3" />
                {wordCount} words
              </span>
            </div>
          )}

          {reviews.length > 0 && !generating && (
            <div className="space-y-2 pt-2 border-t border-syzygy-surface-border">
              <div className="flex items-center gap-2 text-sm text-syzygy-gold">
                <Shield className="h-4 w-4" />
                Code Review
              </div>
              <div className="flex flex-wrap gap-2">
                {reviews.map((r, i) => {
                  const isOk = r.status === "ok";
                  const isWarn = r.status === "warning";
                  return (
                    <div
                      key={r.category}
                      className={cn(
                        "flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-medium",
                        isOk && "bg-green-500/10 text-green-400 border border-green-500/20",
                        isWarn && "bg-amber-500/10 text-amber-400 border border-amber-500/20",
                        !isOk && !isWarn && "bg-red-500/10 text-red-400 border border-red-500/20"
                      )}
                    >
                      {isOk ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                      <span>{r.category}: {isOk ? "OK" : r.count ? `${r.count} issues` : r.message}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {codeFiles.length === 0 && !generating && (
        <div className="space-y-6 py-8">
          <div className="flex flex-col items-center gap-3 text-center">
            <Sparkles className="h-8 w-8 text-syzygy-gold/20" />
            <p className="text-sm text-syzygy-grey/40">Describe what you want to build and Syzygy will generate it</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {suggestions.map((s) => {
              const Icon = s.icon;
              return (
                <button
                  key={s.label}
                  onClick={() => setPrompt(s.label)}
                  className="syzygy-card-glass rounded-xl p-4 text-left transition-all duration-300 hover:border-syzygy-gold/30 hover:scale-[1.02] group"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-syzygy-gold/10 text-syzygy-gold">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="text-xs font-medium text-syzygy-grey-light group-hover:text-syzygy-gold transition-colors">
                      {s.label}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
