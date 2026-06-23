"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";

import { API_URL } from "@/lib/config";

const AUTH_VERIFY_TIMEOUT_MS = 5000;
const AUTH_VERIFY_MAX_RETRIES = 1;

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

      // Fetch with retry logic and explicit timeout
      const verifyUser = async (retryCount = 0): Promise<void> => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), AUTH_VERIFY_TIMEOUT_MS);

        try {
          const res = await fetch(`${API_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          });

          if (!res.ok) {
            if (res.status === 401) {
              // Token is invalid — clear auth state
              localStorage.removeItem("syzygy-auth");
              useAuthStore.setState({
                accessToken: null,
                refreshToken: null,
                user: null,
                isAuthenticated: false,
                isVerifying: false,
              });
            } else if (retryCount < AUTH_VERIFY_MAX_RETRIES) {
              // Retry on other errors (5xx, network, etc.)
              await verifyUser(retryCount + 1);
              return;
            }
            // Non-401 error and retries exhausted — keep optimistic state
            useAuthStore.setState({ isVerifying: false });
            return;
          }

          const user = await res.json();
          useAuthStore.setState({
            user,
            isAuthenticated: true,
            isVerifying: false,
          });
        } catch (err) {
          const isAborted = err instanceof Error && err.name === "AbortError";
          if (isAborted && retryCount < AUTH_VERIFY_MAX_RETRIES) {
            // Timeout or abort — retry once
            await verifyUser(retryCount + 1);
            return;
          }
          // Network error or final retry exhausted — keep optimistic state
          useAuthStore.setState({ isVerifying: false });
        } finally {
          clearTimeout(timeoutId);
        }
      };

      verifyUser();
    } catch {
      localStorage.removeItem("syzygy-auth");
      useAuthStore.setState({ isVerifying: false });
    }
  }, []);

  return <>{children}</>;
}
