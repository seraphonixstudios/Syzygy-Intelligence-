"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";

import { API_URL } from "@/lib/config";

export function AuthInitializer({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const stored = localStorage.getItem("syzygy-auth");
    if (!stored) {
      useAuthStore.setState({ isVerifying: false });
      return;
    }
    try {
      const parsed = JSON.parse(stored);
      const token = parsed?.state?.accessToken || parsed?.accessToken;
      if (!token) {
        useAuthStore.setState({ isVerifying: false });
        return;
      }

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
              useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false, isVerifying: false });
            }
            return;
          }
          return res.json();
        })
        .then((user) => {
          if (user) {
            useAuthStore.setState({ user, isAuthenticated: true, isVerifying: false });
          }
        })
        .catch(() => {
          // Backend unreachable — keep optimistic state
          useAuthStore.setState({ isVerifying: false });
        });
    } catch {
      localStorage.removeItem("syzygy-auth");
      useAuthStore.setState({ isVerifying: false });
    }
  }, []);

  return <>{children}</>;
}
