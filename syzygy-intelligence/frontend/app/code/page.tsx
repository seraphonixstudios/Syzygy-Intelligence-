"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { CodeXml, Play, Loader2, Copy, CheckCircle2, Terminal, Sparkles } from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

const languageOptions = ["python", "javascript", "typescript", "go", "rust", "bash"];

export default function CodePage() {
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState("python");
  const inputRef = useRef<HTMLInputElement>(null);
  const [showLangPicker, setShowLangPicker] = useState(false);

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

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setGenerating(true);
    setCode("");
    try {
      const res = await fetch(`${API}/api/workflows/code/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: prompt.trim(), context: { language } }),
      });
      const data = await res.json();
      setCode(data.code || data.result || JSON.stringify(data, null, 2));
    } catch {
      setCode(`// ${language.toUpperCase()} — Generation Ready\n// Backend must be running for live results.\n// Your code will appear here.`);
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
                {languageOptions.map((lang) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => { setLanguage(lang); setShowLangPicker(false); }}
                    className="block w-full px-4 py-2 text-left text-xs text-syzygy-grey-light hover:bg-syzygy-gold/10 hover:text-syzygy-gold-light transition-colors"
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

      {(code || generating) && (
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
                <span className="text-[10px] text-syzygy-grey/40">{language.toUpperCase()}</span>
                <Button variant="ghost" size="sm" onClick={handleCopy} className="gap-1">
                  {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
            )}
          </div>
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
        </div>
      )}

      {!code && !generating && (
        <div className="flex flex-col items-center gap-3 py-12 text-center">
          <Sparkles className="h-8 w-8 text-syzygy-gold/20" />
          <p className="text-sm text-syzygy-grey/40">Describe what you want to build and Syzygy will generate it</p>
        </div>
      )}
    </div>
  );
}
