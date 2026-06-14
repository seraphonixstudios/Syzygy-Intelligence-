"use client";

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

export function RootLayoutClient({ children }: { children: ReactNode }) {
  // Setup unhandled rejection handler
  useUnhandledRejection();

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
