"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { logger } from "@/lib/logger";

import { WS_URL } from "@/lib/config";

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: Record<string, unknown> | null;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  send: (data: Record<string, unknown>) => void;
}

const RATE_LIMIT_WINDOW = 1000; // milliseconds
const RATE_LIMIT_MAX_MESSAGES = 10; // max messages per window

export function useWebSocket(autoConnect = true): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // Rate limiting tracking
  const messageCountRef = useRef(0);
  const windowStartRef = useRef(Date.now());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (mountedRef.current) {
          setIsConnected(true);
          setError(null);
          messageCountRef.current = 0;
          windowStartRef.current = Date.now();
        }
      };

      ws.onclose = () => {
        if (mountedRef.current) {
          setIsConnected(false);
          // Auto-reconnect after 3s
          reconnectRef.current = setTimeout(() => {
            if (mountedRef.current) connect();
          }, 3000);
        }
      };

      ws.onerror = () => {
        if (mountedRef.current) {
          setError("WebSocket connection failed");
          setIsConnected(false);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Record<string, unknown>;
          if (mountedRef.current) setLastMessage(data);
        } catch {
          // ignore invalid JSON
        }
      };
    } catch (err) {
      logger.error("Failed to create WebSocket", err, "WS");
      setError("Failed to connect");
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    if (mountedRef.current) setIsConnected(false);
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Check rate limit
      const now = Date.now();
      const timeSinceWindowStart = now - windowStartRef.current;

      if (timeSinceWindowStart >= RATE_LIMIT_WINDOW) {
        // New window
        messageCountRef.current = 1;
        windowStartRef.current = now;
      } else if (messageCountRef.current >= RATE_LIMIT_MAX_MESSAGES) {
        // Rate limited
        logger.warn(
          `WebSocket rate limited: ${RATE_LIMIT_MAX_MESSAGES} messages per ${RATE_LIMIT_WINDOW}ms`,
          undefined,
          "WS"
        );
        return;
      } else {
        messageCountRef.current++;
      }

      wsRef.current.send(JSON.stringify(data));
    } else {
      logger.warn("WebSocket not connected, cannot send", undefined, "WS");
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (autoConnect) connect();
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return { isConnected, lastMessage, error, connect, disconnect, send };
}
