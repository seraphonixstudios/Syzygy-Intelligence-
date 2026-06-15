"use client";

import { useCallback, useRef, useState } from "react";
import { logger } from "@/lib/logger";
import { trackApiCall } from "@/lib/observability";
import { useAuthStore } from "@/store/authStore";

import { API_URL } from "@/lib/config";

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const refreshPromiseRef = useRef<Promise<void> | null>(null);

  const fetchApi = useCallback(async (path: string, options?: RequestInit, _retried = false) => {
    setLoading(true);
    setError(null);
    const method = options?.method || "GET";
    const startTime = performance.now();
    logger.debug(`API ${method} ${path}`, undefined, "API");
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options?.headers as Record<string, string> | undefined),
      };
      const authHeaders = useAuthStore.getState().getAuthHeaders();
      if (authHeaders.Authorization) {
        headers.Authorization = authHeaders.Authorization;
      }

      const res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
      });

      trackApiCall(method, path, res.status, performance.now() - startTime);

      if (res.status === 401 && !_retried) {
        if (!refreshPromiseRef.current) {
          refreshPromiseRef.current = useAuthStore.getState().refreshAuth().finally(() => {
            refreshPromiseRef.current = null;
          });
        }
        await refreshPromiseRef.current;
        if (useAuthStore.getState().isAuthenticated) {
          return fetchApi(path, options, true);
        }
        throw new Error("Session expired. Please sign in again.");
      }

      if (!res.ok) {
        const body = await res.text().catch(() => "");
        const msg = `API error: ${res.status} ${res.statusText} — ${body.slice(0, 200)}`;
        logger.error(msg, { path, status: res.status }, "API");
        if (mountedRef.current) setError(msg);
        throw new Error(msg);
      }
      const data = await res.json();
      logger.debug(`API ${path} succeeded`, undefined, "API");
      return data;
    } catch (err: unknown) {
      if (err instanceof Error && err.message.startsWith("API error:")) throw err;
      const msg = err instanceof Error ? err.message : "Unknown API error";
      logger.error(`Fetch failed: ${msg}`, { path }, "API");
      if (mountedRef.current && !(err instanceof Error && err.message.includes("Session expired"))) setError(msg);
      throw err;
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  const get = useCallback((path: string) => fetchApi(path), [fetchApi]);
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
