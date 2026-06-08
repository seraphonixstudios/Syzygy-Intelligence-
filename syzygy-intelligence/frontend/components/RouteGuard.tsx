"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const publicPaths = ["/cloud", "/auth/login", "/auth/register"];

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (!publicPaths.includes(pathname) && !isAuthenticated) {
      // Small delay to let zustand v5's async hydration complete
      const timer = setTimeout(() => {
        window.location.href = "/auth/login";
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [pathname, isAuthenticated]);

  if (publicPaths.includes(pathname) || isAuthenticated) {
    return <>{children}</>;
  }

  return null;
}
