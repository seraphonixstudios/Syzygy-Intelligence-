"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";

const API_URL = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export function AuthInitializer({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    const stored = localStorage.getItem("syzygy-auth");
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored);
      const token = parsed?.state?.accessToken || parsed?.accessToken;
      if (!token) return;

      // Restore state optimistically so the UI works even if backend is unreachable
      const current = useAuthStore.getState();
      useAuthStore.setState({
        ...current,
        accessToken: token,
        refreshToken: parsed?.state?.refreshToken || parsed?.refreshToken || null,
        isAuthenticated: true,
      });

      fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: AbortSignal.timeout(3000),
      })
        .then((res) => {
          if (!res.ok) {
            if (res.status === 401) {
              localStorage.removeItem("syzygy-auth");
              useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
            }
            return;
          }
          return res.json();
        })
        .then((user) => {
          if (user) {
            useAuthStore.setState({ user, isAuthenticated: true });
          }
        })
        .catch(() => {
          // Backend unreachable — keep optimistic state
        });
    } catch {
      localStorage.removeItem("syzygy-auth");
    }
  }, []);

  return <>{children}</>;
}
