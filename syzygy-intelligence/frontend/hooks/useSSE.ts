"use client";

import { useState, useRef, useCallback } from "react";
import { logger } from "@/lib/logger";

interface SSEOptions {
  onToken: (token: string) => void;
  onDone: (full: string) => void;
  onError: (error: string) => void;
  onRagContext?: () => void;
}

export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(async (url: string, body: object, opts: SSEOptions) => {
    const { onToken, onDone, onError, onRagContext } = opts;
    setIsStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;
    let full = "";

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const detail = errData.detail || {};
        throw new Error(detail.message || `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.rag_context) {
              onRagContext?.();
              continue;
            }
            if (data.token) {
              full += data.token;
              onToken(data.token);
            }
            if (data.done) {
              onDone(data.full || full);
            }
            if (data.error) {
              onError(data.error);
            }
          } catch (parseErr) {
            // Log parse errors instead of silently failing
            logger.warn("Failed to parse SSE event data", { line, error: String(parseErr) }, "SSE");
          }
        }
      }

      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer.replace(/^data: /, ""));
          if (data.token) {
            full += data.token;
            onToken(data.token);
          }
          if (data.done || data.full) {
            onDone(data.full || full);
          }
        } catch (parseErr) {
          logger.warn("Failed to parse trailing SSE data", { buffer, error: String(parseErr) }, "SSE");
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name === "AbortError") {
        logger.info("Stream aborted", undefined, "SSE");
      } else {
        const msg = (err as Error).message || "Stream error";
        logger.error("Stream failed", msg, "SSE");
        onError(msg);
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  return { isStreaming, stream, cancel };
}
