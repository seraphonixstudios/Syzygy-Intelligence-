"use client";

import { cn } from "@/lib/utils";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { Send, Sparkles, Code2, Search, FileText, Brain, Zap, ArrowRight } from "lucide-react";

interface CommandBarProps {
  onSubmit: (task: string) => void;
  placeholder?: string;
  compact?: boolean;
}

const suggestions = [
  { icon: Code2, label: "Generate a Python web scraper", category: "code" },
  { icon: Search, label: "Research the latest AI breakthroughs", category: "research" },
  { icon: FileText, label: "Write a blog post about agentic AI", category: "content" },
  { icon: Brain, label: "Run consensus on our Q2 strategy", category: "consensus" },
  { icon: Zap, label: "Debug my React component", category: "code" },
];

export function CommandBar({ onSubmit, placeholder, compact }: CommandBarProps) {
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === "Escape") setShowSuggestions(false);
    };
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input.trim());
      setInput("");
      setShowSuggestions(false);
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      <form
        onSubmit={handleSubmit}
        className="group relative syzygy-card-glass rounded-2xl border-syzygy-gold/20 transition-all duration-300 focus-within:border-syzygy-gold/50 focus-within:shadow-lg focus-within:shadow-syzygy-gold/10"
      >
        <div className="flex items-center gap-3 px-4 py-3">
          <Sparkles className={cn(
            "h-5 w-5 shrink-0 transition-all duration-300",
            input ? "text-syzygy-gold" : "text-syzygy-gold/40"
          )} />
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            placeholder={placeholder || "Command Syzygy — e.g., 'Build a REST API with FastAPI'"}
            className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
          />
          <kbd className="hidden shrink-0 rounded border border-syzygy-surface-border bg-syzygy-shadow/50 px-2 py-0.5 text-[10px] text-syzygy-grey/40 md:inline-block">
            ⌘K
          </kbd>
          <VoiceButton onTranscript={(t) => setInput((prev) => prev + t)} compact />
          <Button
            type="submit"
            variant="gold"
            size={compact ? "icon" : "sm"}
            className={cn("shrink-0", !compact && "gap-1.5")}
            disabled={!input.trim()}
          >
            <Send className="h-3.5 w-3.5" />
            {!compact && <span className="hidden sm:inline">Send</span>}
          </Button>
        </div>
      </form>

      {showSuggestions && !input && (
        <div className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-syzygy-surface-border bg-syzygy-deep/95 backdrop-blur-xl shadow-2xl shadow-black/50 animate-scale-in">
          <div className="p-2">
            <p className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-syzygy-grey/40">
              Quick Commands
            </p>
            {suggestions.map((s, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setInput(s.label);
                  inputRef.current?.focus();
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-syzygy-grey-light transition-all hover:bg-syzygy-gold/10 hover:text-syzygy-gold-light group"
              >
                <s.icon className="h-4 w-4 shrink-0 text-syzygy-grey/40 group-hover:text-syzygy-gold" />
                <span className="flex-1 text-left">{s.label}</span>
                <ArrowRight className="h-3 w-3 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
