"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { FileText, Send, Loader2, Eye, Edit3 } from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export default function ContentPage() {
  const [topic, setTopic] = useState("");
  const [generating, setGenerating] = useState(false);
  const [content, setContent] = useState("");
  const [mode, setMode] = useState<"edit" | "preview">("preview");

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setGenerating(true);
    setContent("");
    try {
      const res = await fetch(`${API}/api/workflows/content/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: topic.trim(), context: {} }),
      });
      const data = await res.json();
      setContent(data.content || data.result || JSON.stringify(data, null, 2));
    } catch {
      setContent(`# ${topic.trim()}\n\nContent pipeline ready. Connect backend and Ollama for live generation.\n\nThis would contain a full research → outline → draft → edit → polish pipeline output.`);
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
        <VoiceButton onTranscript={(t) => setTopic((prev) => prev + t)} compact />
        <Button type="submit" disabled={!topic.trim() || generating} variant="gold" size="sm" className="shrink-0 gap-1">
          {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
          {generating ? "Generating..." : "Generate"}
        </Button>
      </form>

      {content && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-syzygy-gold">
              <FileText className="h-4 w-4" />
              <span>Generated Content</span>
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
