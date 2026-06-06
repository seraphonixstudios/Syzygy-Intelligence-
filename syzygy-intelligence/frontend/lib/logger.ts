type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  message: string;
  data?: unknown;
  timestamp: string;
  source?: string;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const currentLevel: LogLevel =
  (process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel) ||
  (process.env.NODE_ENV === "production" ? "warn" : "debug");

const listeners: Array<(entry: LogEntry) => void> = [];

const SYMBOLS: Record<LogLevel, string> = {
  debug: "🐛",
  info: "ℹ️",
  warn: "⚠️",
  error: "❌",
};

function log(level: LogLevel, message: string, data?: unknown, source?: string) {
  if (LOG_LEVELS[level] < LOG_LEVELS[currentLevel]) return;

  const entry: LogEntry = {
    level,
    message,
    data,
    timestamp: new Date().toISOString(),
    source,
  };

  const prefix = `[${SYMBOLS[level]} Syzygy${source ? ` | ${source}` : ""}]`;

  switch (level) {
    case "debug":
      console.debug(prefix, message, data ?? "");
      break;
    case "info":
      console.info(prefix, message, data ?? "");
      break;
    case "warn":
      console.warn(prefix, message, data ?? "");
      break;
    case "error":
      console.error(prefix, message, data ?? "");
      break;
  }

  listeners.forEach((fn) => fn(entry));
}

export const logger = {
  debug: (message: string, data?: unknown, source?: string) =>
    log("debug", message, data, source),
  info: (message: string, data?: unknown, source?: string) =>
    log("info", message, data, source),
  warn: (message: string, data?: unknown, source?: string) =>
    log("warn", message, data, source),
  error: (message: string, data?: unknown, source?: string) =>
    log("error", message, data, source),

  subscribe: (fn: (entry: LogEntry) => void) => {
    listeners.push(fn);
    return () => {
      const idx = listeners.indexOf(fn);
      if (idx >= 0) listeners.splice(idx, 1);
    };
  },
};
