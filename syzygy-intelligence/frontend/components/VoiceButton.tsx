"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  compact?: boolean;
}

export function VoiceButton({ onTranscript, disabled, compact }: VoiceButtonProps) {
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

  return (
    <div className="relative">
      <button
        type="button"
        onClick={voice.toggleListening}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        disabled={disabled}
        className={`relative flex items-center justify-center rounded-full transition-all duration-300 ${
          compact ? "h-8 w-8" : "h-9 w-9"
        } ${
          voice.isListening
            ? "bg-syzygy-gold/20 text-syzygy-gold shadow-lg shadow-syzygy-gold/20 animate-radiant-burst"
            : "text-syzygy-grey/50 hover:text-syzygy-gold hover:bg-syzygy-gold/10"
        } disabled:opacity-30 disabled:cursor-not-allowed`}
      >
        {voice.isProcessing ? (
          <Loader2 className={`${compact ? "h-3.5 w-3.5" : "h-4 w-4"} animate-spin`} />
        ) : voice.isListening ? (
          <Mic className={`${compact ? "h-3.5 w-3.5" : "h-4 w-4"} animate-pulse`} />
        ) : (
          <MicOff className={`${compact ? "h-3.5 w-3.5" : "h-4 w-4"}`} />
        )}
        {voice.isListening && (
          <span className="absolute inset-0 animate-ring-expand rounded-full border border-syzygy-gold/40" />
        )}
      </button>

      {voice.isListening && fullText && (
        <div className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-syzygy-gold/30 bg-syzygy-deep/95 px-3 py-2 text-xs text-syzygy-gold-light backdrop-blur-xl shadow-2xl max-w-[60vw] truncate">
          {fullText}
        </div>
      )}

      {showTooltip && !voice.isListening && !voice.error && (
        <div className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-syzygy-surface-border bg-syzygy-deep/95 px-3 py-1.5 text-[10px] text-syzygy-grey/60 backdrop-blur-xl shadow-2xl">
          Push to talk
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
