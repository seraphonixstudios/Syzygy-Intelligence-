import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVoiceRecorder } from "./useVoiceRecorder";

let mockRecognition: {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
  abort: ReturnType<typeof vi.fn>;
  onresult: ((event: unknown) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};

class MockSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = "";
  maxAlternatives = 1;
  start = vi.fn();
  stop = vi.fn();
  abort = vi.fn();
  onresult: ((event: unknown) => void) | null = null;
  onerror: ((event: { error: string }) => void) | null = null;
  onend: (() => void) | null = null;
}

beforeEach(() => {
  const inst = new MockSpeechRecognition();
  mockRecognition = inst as unknown as typeof mockRecognition;
  (window as any).SpeechRecognition = function() { return inst; };
  (window as any).webkitSpeechRecognition = undefined;
});

afterEach(() => {
  vi.restoreAllMocks();
  delete (window as any).SpeechRecognition;
});

describe("useVoiceRecorder", () => {
  it("detects supported browser", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    expect(result.current.isSupported).toBe(true);
  });

  it("detects unsupported browser", () => {
    delete (window as any).SpeechRecognition;
    const { result } = renderHook(() => useVoiceRecorder());
    expect(result.current.isSupported).toBe(false);
    expect(result.current.error).toContain("not supported");
  });

  it("starts listening", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    act(() => { result.current.startListening(); });
    expect(result.current.isListening).toBe(true);
  });

  it("stops listening and sets processing", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    act(() => { result.current.startListening(); });
    act(() => { result.current.stopListening(); });
    expect(result.current.isProcessing).toBe(true);
  });

  it("toggles between start and stop", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    act(() => { result.current.toggleListening(); });
    expect(result.current.isListening).toBe(true);
    act(() => { result.current.toggleListening(); });
    expect(result.current.isProcessing).toBe(true);
  });

  it("resets state", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    act(() => { result.current.startListening(); });
    act(() => { result.current.reset(); });
    expect(result.current.transcript).toBe("");
    expect(result.current.interimTranscript).toBe("");
    expect(result.current.error).toBeNull();
  });

  it("handles recognition result with final transcript", () => {
    renderHook(() => useVoiceRecorder());

    act(() => {
      mockRecognition.onresult?.({
        resultIndex: 0,
        results: [
          { 0: { transcript: "hello" }, isFinal: true },
        ],
        __length: 1,
      } as unknown as SpeechRecognitionEvent);
    });
  });

  it("handles recognition error", () => {
    const { result } = renderHook(() => useVoiceRecorder());

    act(() => {
      mockRecognition.onerror?.({ error: "not-allowed" });
    });

    expect(result.current.error).toContain("not-allowed");
    expect(result.current.isListening).toBe(false);
  });

  it("handles recognition end", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    act(() => { result.current.startListening(); });

    act(() => {
      mockRecognition.onend?.();
    });

    expect(result.current.isListening).toBe(false);
  });

  it("calls recognition.stop() on start error (already started)", () => {
    mockRecognition.start = vi.fn(() => { throw new Error("already started"); });
    mockRecognition.stop = vi.fn();

    const { result } = renderHook(() => useVoiceRecorder());
    act(() => { result.current.startListening(); });
    expect(mockRecognition.stop).toHaveBeenCalled();
  });
});
