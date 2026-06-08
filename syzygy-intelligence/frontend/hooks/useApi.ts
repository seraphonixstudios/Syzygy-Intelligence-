"use client";

import { useCallback, useState } from "react";
import { logger } from "@/lib/logger";
import { useAuthStore } from "@/store/authStore";

const API_URL = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchApi = useCallback(async (path: string, options?: RequestInit) => {
    setLoading(true);
    setError(null);
    logger.debug(`API ${options?.method || "GET"} ${path}`, undefined, "API");
    try {
      const res = await fetch(`${API_URL}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
          ...options?.headers,
        },
        ...options,
      });
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        const msg = `API error: ${res.status} ${res.statusText} — ${body.slice(0, 200)}`;
        logger.error(msg, { path, status: res.status }, "API");
        setError(msg);
        throw new Error(msg);
      }
      const data = await res.json();
      logger.debug(`API ${path} succeeded`, undefined, "API");
      return data;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown API error";
      if (!(err instanceof Error && err.message.startsWith("API error:"))) {
        logger.error(`Fetch failed: ${msg}`, { path }, "API");
        setError(msg);
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const get = useCallback(
    (path: string) => fetchApi(path),
    [fetchApi]
  );

  const post = useCallback(
    (path: string, data?: unknown) =>
      fetchApi(path, {
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
      }),
    [fetchApi]
  );

  return { get, post, loading, error, clearError: () => setError(null) };
}
