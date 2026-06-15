"use client";

import { useEffect } from "react";
import { trackError } from "@/lib/observability";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    trackError(error, "app/error");
  }, [error]);

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold text-red-400">Something went wrong</h1>
      <p className="text-sm text-zinc-400">{error.message}</p>
      <button
        onClick={reset}
        className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-700"
      >
        Try again
      </button>
    </div>
  );
}
