"use client";

import { useCallback, useRef, useState } from "react";
import { logger } from "@/lib/logger";
import { useAuthStore } from "@/store/authStore";

import { API_URL } from "@/lib/config";
let refreshPromise: Promise<void> | null = null;

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchApi = useCallback(async (path: string, options?: RequestInit, _retried = false) => {
    setLoading(true);
    setError(null);
    logger.debug(`API ${options?.method || "GET"} ${path}`, undefined, "API");
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

      if (res.status === 401 && !_retried) {
        if (!refreshPromise) {
          refreshPromise = useAuthStore.getState().refreshAuth().finally(() => {
            refreshPromise = null;
          });
        }
        await refreshPromise;
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
