"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, Square, Loader2 } from "lucide-react";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function VoiceButton({ onTranscript, disabled }: VoiceButtonProps) {
  const voice = useVoiceRecorder();
  const [showTooltip, setShowTooltip] = useState(false);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    if (!voice.isListening && voice.transcript) {
      onTranscript(voice.transcript);
      voice.reset();
    }
  }, [voice.isListening, voice.transcript]);

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  const fullText = voice.isListening
    ? `${voice.transcript}${voice.interimTranscript ? " " + voice.interimTranscript : ""}`
    : "";

  if (!voice.isSupported) return null;

  const isActive = voice.isListening || voice.isProcessing;

  return (
    <div className="relative shrink-0">
      <button
        type="button"
        onClick={voice.toggleListening}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        disabled={disabled || voice.isProcessing}
        className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium tracking-wide transition-all duration-300 ${
          isActive
            ? "bg-red-500/20 text-red-400 shadow-lg shadow-red-500/20 animate-radiant-burst border border-red-400/30"
            : "text-syzygy-grey/60 hover:text-syzygy-gold hover:bg-syzygy-gold/10 border border-syzygy-surface-border/50 hover:border-syzygy-gold/30"
        } disabled:opacity-30 disabled:cursor-not-allowed`}
      >
        {voice.isProcessing ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : voice.isListening ? (
          <Mic className="h-3.5 w-3.5 animate-pulse" />
        ) : (
          <Mic className="h-3.5 w-3.5" />
        )}
        <span>
          {voice.isProcessing ? "Processing" : voice.isListening ? "Stop" : "Voice"}
        </span>
      </button>

      {voice.isListening && fullText && (
        <div className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-syzygy-gold/30 bg-syzygy-deep/95 px-3 py-2 text-xs text-syzygy-gold-light backdrop-blur-xl shadow-2xl max-w-[60vw] truncate">
          {fullText}
        </div>
      )}

      {showTooltip && !isActive && !voice.error && (
        <div className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-syzygy-surface-border bg-syzygy-deep/95 px-3 py-1.5 text-[10px] text-syzygy-grey/60 backdrop-blur-xl shadow-2xl">
          Click to start speaking
        </div>
      )}

      {voice.error && (
        <div className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-[10px] text-red-400 backdrop-blur-xl shadow-2xl">
          {voice.error}
        </div>
      )}
    </div>
  );
}
