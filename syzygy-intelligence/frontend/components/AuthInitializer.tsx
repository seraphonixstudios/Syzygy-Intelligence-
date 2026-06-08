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
      fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Unauthorized");
          return res.json();
        })
        .then((user) => {
          const current = useAuthStore.getState();
          useAuthStore.setState({
            ...current,
            accessToken: token,
            user,
            isAuthenticated: true,
          });
        })
        .catch(() => {
          localStorage.removeItem("syzygy-auth");
        });
    } catch {
      localStorage.removeItem("syzygy-auth");
    }
  }, []);

  return <>{children}</>;
}
