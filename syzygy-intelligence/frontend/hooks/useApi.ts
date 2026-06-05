"use client";

import { useCallback, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export function useApi() {
  const [loading, setLoading] = useState(false);

  const fetchApi = useCallback(async (path: string, options?: RequestInit) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return await res.json();
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

  return { get, post, loading };
}
