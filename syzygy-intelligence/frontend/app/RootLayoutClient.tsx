"use client";

import { useEffect, useRef } from "react";
import { useUnhandledRejection } from "@/hooks/useUnhandledRejection";
import { MotionConfig, AnimatePresence } from "framer-motion";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { Toaster } from "sonner";
import { ScrollToTop } from "@/components/ScrollToTop";
import { AetherBackground } from "@/components/AetherBackground";
import { AuthInitializer } from "@/components/AuthInitializer";
import { RouteGuard } from "@/components/RouteGuard";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ReactNode } from "react";
import { initObservability, trackPageView } from "@/lib/observability";
import { API_URL } from "@/lib/config";
import { logger } from "@/lib/logger";
import { usePathname } from "next/navigation";

export function RootLayoutClient({ children }: { children: ReactNode }) {
  useUnhandledRejection();
  const pathname = usePathname();
  const prevPath = useRef(pathname);
  const initialized = useRef(false);

  useEffect(() => {
    if (!initialized.current) {
      initObservability(API_URL);
      initialized.current = true;
    }
  }, []);

  // Track page views on route change
  useEffect(() => {
    if (prevPath.current !== pathname) {
      trackPageView(pathname);
      prevPath.current = pathname;
    }
  }, [pathname]);

  // Subscribe logger errors to telemetry with proper cleanup
  useEffect(() => {
    const unsub = logger.subscribe((entry) => {
      if (entry.level === "error") {
        // Load observability dynamically and track error
        import("@/lib/observability")
          .then((obs) => {
            obs.trackError(new Error(entry.message), entry.source);
          })
          .catch((err) => {
            // Silently fail if observability import fails
            console.error("Failed to load observability:", err);
          });
      }
    });
    // Ensure unsub is a function before calling it
    return () => {
      if (typeof unsub === "function") {
        unsub();
      }
    };
  }, []);

  return (
    <MotionConfig
      reducedMotion="user"
      transition={{ ease: [0.25, 0.1, 0.25, 1], duration: 0.3 }}
    >
      <AuthInitializer>
        <div className="relative flex h-dvh overflow-hidden">
          <AetherBackground />
          <Sidebar />
          <ErrorBoundary source="Layout">
            <ScrollToTop>
              <RouteGuard>
                <AnimatePresence mode="wait">{children}</AnimatePresence>
              </RouteGuard>
            </ScrollToTop>
          </ErrorBoundary>
        </div>
      </AuthInitializer>
    </MotionConfig>
  );
}
