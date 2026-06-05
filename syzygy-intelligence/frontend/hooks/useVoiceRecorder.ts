"use client";

import { useState, useRef, useCallback, useEffect } from "react";

interface VoiceRecorderState {
  isSupported: boolean;
  isListening: boolean;
  isProcessing: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
}

interface VoiceRecorderReturn extends VoiceRecorderState {
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  reset: () => void;
}

export function useVoiceRecorder(): VoiceRecorderReturn {
  const [state, setState] = useState<VoiceRecorderState>({
    isSupported: false,
    isListening: false,
    isProcessing: false,
    transcript: "",
    interimTranscript: "",
    error: null,
  });

  const recognitionRef = useRef<any>(null);
  const finalTranscriptRef = useRef("");

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setState((s) => ({ ...s, isSupported: false, error: "Speech recognition not supported in this browser." }));
      return;
    }

    setState((s) => ({ ...s, isSupported: true }));

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (final) {
        finalTranscriptRef.current += " " + final;
      }

      setState((s) => ({
        ...s,
        transcript: finalTranscriptRef.current.trim(),
        interimTranscript: interim,
      }));
    };

    recognition.onerror = (event: any) => {
      if (event.error === "no-speech") return;
      setState((s) => ({
        ...s,
        isListening: false,
        isProcessing: false,
        error: `Voice error: ${event.error}`,
      }));
    };

    recognition.onend = () => {
      setState((s) => ({
        ...s,
        isListening: false,
        isProcessing: false,
      }));
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.abort();
      } catch {}
    };
  }, []);

  const startListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    finalTranscriptRef.current = "";
    setState((s) => ({ ...s, isListening: true, isProcessing: false, error: null, transcript: "", interimTranscript: "" }));

    try {
      recognition.start();
    } catch {
      try {
        recognition.stop();
        setTimeout(() => recognition.start(), 100);
      } catch {}
    }
  }, []);

  const stopListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    setState((s) => ({ ...s, isProcessing: true }));

    try {
      recognition.stop();
    } catch {}
  }, []);

  const toggleListening = useCallback(() => {
    if (state.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [state.isListening, startListening, stopListening]);

  const reset = useCallback(() => {
    finalTranscriptRef.current = "";
    setState((s) => ({ ...s, transcript: "", interimTranscript: "", error: null }));
  }, []);

  return {
    ...state,
    startListening,
    stopListening,
    toggleListening,
    reset,
  };
}
