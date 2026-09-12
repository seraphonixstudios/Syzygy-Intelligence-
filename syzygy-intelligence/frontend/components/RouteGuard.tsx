"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const publicPaths = [
  "/cloud",
  "/contact",
  "/privacy",
  "/terms",
  "/auth/login",
  "/auth/register",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
  "/auth/oauth-callback",
];

// Failsafe timeouts so the UI can never stick on "Verifying..." forever
// (e.g. stalled persist hydration or a verify request that never settles).
const HYDRATION_TIMEOUT_MS = 8000;
// Must exceed AuthInitializer's worst case (5s timeout x 2 attempts).
const VERIFY_TIMEOUT_MS = 15000;

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isVerifying = useAuthStore((s) => s.isVerifying);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (useAuthStore.persist.hasHydrated()) {
      setReady(true);
      return;
    }
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      setReady(true);
    });
    const timeoutId = setTimeout(() => setReady(true), HYDRATION_TIMEOUT_MS);
    return () => {
      clearTimeout(timeoutId);
      unsub();
    };
  }, []);

  useEffect(() => {
    if (!isVerifying) return;
    const timeoutId = setTimeout(() => {
      useAuthStore.setState({ isVerifying: false });
    }, VERIFY_TIMEOUT_MS);
    return () => clearTimeout(timeoutId);
  }, [isVerifying]);

  useEffect(() => {
    if (ready && !isVerifying && !publicPaths.includes(pathname) && !isAuthenticated) {
      window.location.href = "/auth/login";
    }
  }, [pathname, isAuthenticated, isVerifying, ready]);

  if (!ready || isVerifying) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-gray-950 via-purple-950 to-gray-950">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-purple-500 border-t-transparent" />
          <p className="text-sm text-gray-400">Verifying...</p>
        </div>
      </div>
    );
  }

  if (publicPaths.includes(pathname) || isAuthenticated) {
    return <>{children}</>;
  }

  return null;
}
