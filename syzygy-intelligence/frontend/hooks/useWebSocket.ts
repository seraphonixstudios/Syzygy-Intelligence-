"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { logger } from "@/lib/logger";

interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket(url?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const wsUrl =
      url || process.env.NEXT_PUBLIC_SYZYGY_WS_URL || "ws://localhost:8000/ws";

    logger.info(`WS connecting to ${wsUrl}`, undefined, "WS");
    setError(null);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      logger.info("WS connected", undefined, "WS");
      setIsConnected(true);
      setError(null);
    };

    ws.onclose = (event) => {
      logger.warn(`WS disconnected (code: ${event.code})`, undefined, "WS");
      setIsConnected(false);
    };

    ws.onerror = () => {
      const msg = "WebSocket connection failed";
      logger.error(msg, undefined, "WS");
      setError(msg);
      setIsConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        logger.debug("WS message received", { type: data.type }, "WS");
        setLastMessage(data);
      } catch {
        logger.debug("WS non-JSON message", { data: event.data }, "WS");
      }
    };
  }, [url]);

  const disconnect = useCallback(() => {
    logger.info("WS disconnecting", undefined, "WS");
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      logger.debug("WS send", { type: data.type }, "WS");
      wsRef.current.send(JSON.stringify(data));
    } else {
      logger.warn("WS not open, cannot send", undefined, "WS");
    }
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { isConnected, lastMessage, error, connect, disconnect, send };
}
