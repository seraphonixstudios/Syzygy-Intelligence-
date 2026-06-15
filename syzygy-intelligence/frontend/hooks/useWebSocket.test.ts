import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

type MockWs = {
  readyState: number;
  send: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;
  onopen: (() => void) | null;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  onmessage: ((event: { data: string }) => void) | null;
};

const mockWsInstances: MockWs[] = [];
let currentMockWs: MockWs | null = null;

class MockWebSocket {
  readyState = MockWebSocket.CONNECTING;
  send = vi.fn();
  close = vi.fn();
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(_url: string) {
    currentMockWs = this;
    mockWsInstances.push(this);
  }

  triggerOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  triggerClose() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;

import { useWebSocket } from "./useWebSocket";

describe("useWebSocket", () => {
  beforeEach(() => {
    currentMockWs = null;
    mockWsInstances.length = 0;
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("connects on mount when autoConnect is true", () => {
    renderHook(() => useWebSocket(true));
    expect(mockWsInstances.length).toBe(1);
  });

  it("does not connect on mount when autoConnect is false", () => {
    renderHook(() => useWebSocket(false));
    expect(mockWsInstances.length).toBe(0);
  });

  it("sets isConnected on open", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.triggerOpen();
    });

    expect(result.current.isConnected).toBe(true);
  });

  it("sets isConnected to false on close", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.triggerOpen();
    });

    act(() => {
      currentMockWs!.triggerClose();
    });

    expect(result.current.isConnected).toBe(false);
  });

  it("sends data when connected", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.triggerOpen();
    });

    act(() => {
      result.current.send({ type: "ping" });
    });

    expect(currentMockWs!.send).toHaveBeenCalledWith(JSON.stringify({ type: "ping" }));
  });

  it("does not send when not connected (closed)", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      result.current.send({ type: "ping" });
    });

    expect(currentMockWs!.send).not.toHaveBeenCalled();
  });

  it("sets lastMessage on incoming message", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.onmessage?.({ data: JSON.stringify({ type: "response" }) });
    });

    expect(result.current.lastMessage).toEqual({ type: "response" });
  });

  it("ignores invalid JSON messages", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.onmessage?.({ data: "not json" });
    });

    expect(result.current.lastMessage).toBeNull();
  });

  it("reconnects after 3s on close", () => {
    renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.triggerClose();
    });

    expect(mockWsInstances.length).toBe(1);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(mockWsInstances.length).toBe(2);
  });

  it("disconnect clears reconnect timer", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.triggerClose();
    });

    act(() => {
      result.current.disconnect();
    });

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(mockWsInstances.length).toBe(1);
  });

  it("sets error on WebSocket error", () => {
    const { result } = renderHook(() => useWebSocket(true));

    act(() => {
      currentMockWs!.onerror?.();
    });

    expect(result.current.error).toBe("WebSocket connection failed");
  });

  it("connect function creates a new WebSocket", () => {
    const { result } = renderHook(() => useWebSocket(false));

    act(() => {
      result.current.connect();
    });

    expect(mockWsInstances.length).toBe(1);
  });
});
