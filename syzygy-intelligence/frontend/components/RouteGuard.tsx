"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const publicPaths = [
  "/cloud",
  "/auth/login",
  "/auth/register",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
  "/auth/oauth-callback",
];

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore.persist.hasHydrated();
  const [ready, setReady] = useState(hasHydrated);

  useEffect(() => {
    if (!hasHydrated) {
      const unsub = useAuthStore.persist.onFinishHydration(() => setReady(true));
      return unsub;
    }
    setReady(true);
  }, [hasHydrated]);

  useEffect(() => {
    if (ready && !publicPaths.includes(pathname) && !isAuthenticated) {
      window.location.href = "/auth/login";
    }
  }, [pathname, isAuthenticated, ready]);

  if (!ready) return null;

  if (publicPaths.includes(pathname) || isAuthenticated) {
    return <>{children}</>;
  }

  return null;
}
