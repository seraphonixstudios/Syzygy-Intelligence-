type TelemetryEvent = {
  type: "page_view" | "api_call" | "error" | "web_vital" | "custom";
  name: string;
  duration?: number;
  status?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
};

const queue: TelemetryEvent[] = [];
const FLUSH_INTERVAL = 30_000;
let flushTimer: ReturnType<typeof setInterval> | null = null;
let apiUrl = "";

export function initObservability(backendUrl: string) {
  apiUrl = backendUrl;
  if (typeof window === "undefined") return;
  initPerformanceObserver();
  flushTimer = setInterval(flush, FLUSH_INTERVAL);
  window.addEventListener("beforeunload", flushSync);
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushSync();
  });
  queueMicrotask(() => trackNavigationTiming());
}

function push(event: TelemetryEvent) {
  queue.push(event);
  if (queue.length >= 20) flush();
}

export function trackPageView(path: string, duration?: number) {
  push({ type: "page_view", name: path, duration, timestamp: new Date().toISOString() });
}

export function trackApiCall(method: string, path: string, status: number, duration: number) {
  push({
    type: "api_call",
    name: `${method} ${path}`,
    duration,
    status: String(status),
    timestamp: new Date().toISOString(),
  });
}

export function trackError(error: Error, context?: string) {
  push({
    type: "error",
    name: context ? `${context}: ${error.message}` : error.message,
    metadata: { stack: error.stack?.slice(0, 500) },
    timestamp: new Date().toISOString(),
  });
}

export function trackEvent(name: string, metadata?: Record<string, unknown>) {
  push({ type: "custom", name, metadata, timestamp: new Date().toISOString() });
}

function trackNavigationTiming() {
  if (typeof window === "undefined") return;
  const nav = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
  if (!nav) return;
  push({
    type: "page_view",
    name: window.location.pathname,
    duration: nav.duration,
    metadata: {
      domContentLoaded: nav.domContentLoadedEventEnd,
      domComplete: nav.domComplete,
      loadEvent: nav.loadEventEnd,
      redirectCount: nav.redirectCount,
      transferSize: nav.transferSize,
    },
    timestamp: new Date().toISOString(),
  });
}

function initPerformanceObserver() {
  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === "largest-contentful-paint") {
          push({
            type: "web_vital",
            name: "LCP",
            duration: entry.startTime,
            timestamp: new Date().toISOString(),
          });
        }
        if (entry.entryType === "first-contentful-paint") {
          push({
            type: "web_vital",
            name: "FCP",
            duration: entry.startTime,
            timestamp: new Date().toISOString(),
          });
        }
      }
    });
    observer.observe({ entryTypes: ["largest-contentful-paint", "first-contentful-paint"] });
  } catch {
    // PerformanceObserver not supported
  }

  try {
    const clsObserver = new PerformanceObserver((list) => {
      let cumulativeShift = 0;
      for (const entry of list.getEntries()) {
        if (entry.entryType === "layout-shift" && !(entry as any).hadRecentInput) {
          cumulativeShift += (entry as any).value;
        }
      }
      if (cumulativeShift > 0) {
        push({
          type: "web_vital",
          name: "CLS",
          duration: cumulativeShift,
          timestamp: new Date().toISOString(),
        });
      }
    });
    clsObserver.observe({ entryTypes: ["layout-shift"] });
  } catch {
    // LayoutShift not supported
  }
}

async function flush() {
  if (queue.length === 0 || !apiUrl) return;
  const batch = queue.splice(0, queue.length);
  try {
    await fetch(`${apiUrl}/api/telemetry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: batch }),
    });
  } catch {
    // Telemetry delivery failure is non-critical
  }
}

function flushSync() {
  if (queue.length === 0 || !apiUrl) return;
  const batch = queue.splice(0, queue.length);
  try {
    navigator.sendBeacon(`${apiUrl}/api/telemetry`, JSON.stringify({ events: batch }));
  } catch {
    // Best-effort
  }
}
