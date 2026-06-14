"use client";

import { useEffect } from "react";
import { logger } from "@/lib/logger";

/**
 * Hook to catch unhandled promise rejections and async errors
 * that ErrorBoundary cannot catch
 */
export function useUnhandledRejection() {
  useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      logger.error(
        "Unhandled Promise rejection",
        { reason: event.reason?.message || String(event.reason) },
        "UnhandledRejection",
      );
      // Note: Returning nothing from this handler means the error is not suppressed
      // The rejection will still be logged and may cause the app to show an error UI
    };

    window.addEventListener("unhandledrejection", handleUnhandledRejection);
    return () => {
      window.removeEventListener("unhandledrejection", handleUnhandledRejection);
    };
  }, []);
}
