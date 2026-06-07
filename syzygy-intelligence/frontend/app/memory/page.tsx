"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Library, Search, Clock, Loader2 } from "lucide-react";
import { logger } from "@/lib/logger";
import { toast } from "sonner";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

interface MemoryItem {
  id: string;
  content: string;
  memory_type?: string;
  agent_id?: string;
  polarity?: string;
  created_at?: string;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const fetchRecent = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/memory/recent?limit=20`);
      const data = await res.json();
      setMemories(data.memories || data.results || []);
    } catch (err) {
      logger.error("Failed to fetch recent memories", err, "Memory");
      toast.error("Could not load memories");
      setMemories([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRecent(); }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) { fetchRecent(); return; }
    setSearching(true);
    try {
      const res = await fetch(`${API}/api/memory/recall?query=${encodeURIComponent(query.trim())}&limit=20`);
      const data = await res.json();
      setMemories(data.memories || data.results || []);
    } catch (err) {
      logger.error("Memory search failed", err, "Memory");
      toast.error("Search failed");
      setMemories([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <img
          src="/branding/pagetop.logo.png"
          alt="Syzygy"
          className="h-8 w-auto brightness-110"
          width={32} height={32}
        />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Memory</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Browse short-term, long-term, vector, graph, and team memory</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex items-center gap-2 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
        <Search className="h-4 w-4 shrink-0 text-syzygy-grey/40" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search memories..."
          className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
        />
        <Button type="submit" disabled={searching} variant="ghost" size="sm">
          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </Button>
      </form>

      {loading ? (
        <div className="flex h-[40vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-syzygy-gold" />
        </div>
      ) : memories.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-20">
          <Library className="h-12 w-12 text-syzygy-grey/30" />
          <p className="text-syzygy-grey/50">No memories found.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {memories.map((mem) => (
            <div key={mem.id} className="syzygy-card-glass rounded-xl p-4 transition-all hover:border-syzygy-gold/30">
              <div className="flex items-start justify-between gap-2">
                <p className="flex-1 text-sm text-syzygy-grey leading-relaxed">{mem.content}</p>
                <div className="flex shrink-0 gap-2">
                  {mem.polarity && (
                    <span className="rounded bg-syzygy-shadow/50 px-1.5 py-0.5 text-[10px] text-syzygy-grey/60">
                      {mem.polarity}
                    </span>
                  )}
                  {mem.memory_type && (
                    <span className="rounded bg-syzygy-shadow/50 px-1.5 py-0.5 text-[10px] text-syzygy-gold/60">
                      {mem.memory_type}
                    </span>
                  )}
                </div>
              </div>
              {mem.created_at && (
                <p className="mt-1 flex items-center gap-1 text-[10px] text-syzygy-grey/40">
                  <Clock className="h-3 w-3" />
                  {new Date(mem.created_at).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
