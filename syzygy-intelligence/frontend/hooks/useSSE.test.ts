import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSSE } from "@/hooks/useSSE";

function createMockResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  return {
    ok: true,
    body: {
      getReader: () => {
        let i = 0;
        return {
          read: () => {
            if (i < chunks.length) {
              return Promise.resolve({ done: false, value: encoder.encode(chunks[i++]) });
            }
            return Promise.resolve({ done: true, value: undefined });
          },
        };
      },
    },
  };
}

describe("useSSE", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("streams tokens and calls onToken", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      createMockResponse(["data: " + JSON.stringify({ token: "Hello" }) + "\n", "data: " + JSON.stringify({ token: " World" }) + "\n"]) as unknown as Response,
    );

    const { result } = renderHook(() => useSSE());
    const onToken = vi.fn();
    const onDone = vi.fn();

    await act(async () => {
      await result.current.stream("/api/stream", { prompt: "hi" }, {
        onToken,
        onDone,
        onError: vi.fn(),
      });
    });

    expect(onToken).toHaveBeenCalledTimes(2);
    expect(onToken).toHaveBeenNthCalledWith(1, "Hello");
    expect(onToken).toHaveBeenNthCalledWith(2, " World");
  });

  it("calls onDone with full text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      createMockResponse(["data: " + JSON.stringify({ token: "Hi", done: true, full: "Hi" }) + "\n"]) as unknown as Response,
    );

    const { result } = renderHook(() => useSSE());
    const onDone = vi.fn();

    await act(async () => {
      await result.current.stream("/api/stream", {}, {
        onToken: vi.fn(),
        onDone,
        onError: vi.fn(),
      });
    });

    expect(onDone).toHaveBeenCalledWith("Hi");
  });

  it("calls onRagContext for rag_context events", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      createMockResponse(["data: " + JSON.stringify({ rag_context: true }) + "\n", "data: " + JSON.stringify({ token: "result" }) + "\n"]) as unknown as Response,
    );

    const { result } = renderHook(() => useSSE());
    const onRagContext = vi.fn();

    await act(async () => {
      await result.current.stream("/api/stream", {}, {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
        onRagContext,
      });
    });

    expect(onRagContext).toHaveBeenCalledTimes(1);
  });

  it("calls onError on HTTP error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: { message: "Server error" } }),
    } as Response);

    const { result } = renderHook(() => useSSE());
    const onError = vi.fn();

    await act(async () => {
      await result.current.stream("/api/stream", {}, {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError,
      });
    });

    expect(onError).toHaveBeenCalledWith("Server error");
  });

  it("calls onError for generic HTTP error without detail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 403,
      json: () => Promise.reject(new Error("parse error")),
    } as Response);

    const { result } = renderHook(() => useSSE());
    const onError = vi.fn();

    await act(async () => {
      await result.current.stream("/api/stream", {}, {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError,
      });
    });

    expect(onError).toHaveBeenCalledWith("HTTP 403");
  });

  it("cancel sets isStreaming to false", async () => {
    const abortSpy = vi.fn();
    vi.spyOn(globalThis, "fetch").mockImplementation(() => {
      const controller = new AbortController();
      controller.signal.addEventListener("abort", abortSpy);
      return new Promise(() => {}); // never resolves
    });

    const { result } = renderHook(() => useSSE());

    // Start the stream (async, don't await)
    result.current.stream("/api/stream", {}, {
      onToken: vi.fn(),
      onDone: vi.fn(),
      onError: vi.fn(),
    });

    // Cancel synchronously
    act(() => {
      result.current.cancel();
    });

    expect(result.current.isStreaming).toBe(false);
  });

  it("tracks isStreaming state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      createMockResponse(["data: " + JSON.stringify({ token: "ok" }) + "\n"]) as unknown as Response,
    );

    const { result } = renderHook(() => useSSE());

    expect(result.current.isStreaming).toBe(false);

    await act(async () => {
      await result.current.stream("/api/stream", {}, {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      });
    });

    expect(result.current.isStreaming).toBe(false);
  });
});
