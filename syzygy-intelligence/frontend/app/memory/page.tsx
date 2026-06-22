"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Library, Search, Clock, Loader2, Filter, Trash2, ChevronDown, ChevronRight, Tags, BarChart3 } from "lucide-react";
import { logger } from "@/lib/logger";
import { toast } from "sonner";
import { cn, formatDate } from "@/lib/utils";
import { API_URL as API } from "@/lib/config";

const MEMORY_TYPES = ["all", "short_term", "long_term", "team", "vector", "graph"] as const;
const POLARITIES = ["all", "masculine", "feminine", "unified"] as const;

const TYPE_BADGE: Record<string, string> = {
  short_term: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  long_term: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
  team: "bg-purple-500/15 text-purple-300 border-purple-500/30",
  vector: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  graph: "bg-orange-500/15 text-orange-300 border-orange-500/30",
};

interface MemoryItem {
  id: string;
  content: string;
  memory_type?: string;
  agent_id?: string;
  polarity?: string;
  tags?: string[];
  importance_score?: number;
  created_at?: string;
  updated_at?: string;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [memoryType, setMemoryType] = useState("all");
  const [polarity, setPolarity] = useState("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);

  const buildUrl = useCallback((base: string, params: Record<string, string>) => {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v && v !== "all") sp.set(k, v); });
    return `${base}?${sp.toString()}`;
  }, []);

  const fetchRecent = useCallback(async () => {
    setLoading(true);
    try {
      const url = buildUrl(`${API}/api/memory/recent`, { limit: "20", memory_type: memoryType, polarity });
      const res = await fetch(url);
      const data = await res.json();
      setMemories(data.memories || data.results || []);
    } catch (err) {
      logger.error("Failed to fetch recent memories", err, "Memory");
      toast.error("Could not load memories");
      setMemories([]);
    } finally {
      setLoading(false);
    }
  }, [memoryType, polarity, buildUrl]);

  useEffect(() => { fetchRecent(); }, [fetchRecent]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) { fetchRecent(); return; }
    setSearching(true);
    try {
      const url = buildUrl(`${API}/api/memory/recall`, { query: query.trim(), limit: "20", memory_type: memoryType, polarity });
      const res = await fetch(url);
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

  const handleDelete = async (id: string) => {
    setMemories((prev) => prev.filter((m) => m.id !== id));
    try {
      const res = await fetch(`${API}/api/memory/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      toast.success("Memory deleted");
    } catch (err) {
      logger.error("Failed to delete memory", err, "Memory");
      toast.error("Failed to delete memory");
      fetchRecent();
    }
  };

  const toggleExpand = (id: string) => setExpandedId((prev) => (prev === id ? null : id));

  const typeCount = new Set(memories.map((m) => m.memory_type).filter(Boolean)).size;
  const sorted = [...memories].sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
  const lastStored = sorted[0]?.created_at;

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

      <div className="flex items-center gap-4 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-4 py-2.5 text-[11px] text-syzygy-grey/60">
        <span className="flex items-center gap-1.5">
          <BarChart3 className="h-3.5 w-3.5" />
          {memories.length} item{memories.length !== 1 ? "s" : ""}
        </span>
        <span className="h-3 w-px bg-syzygy-surface-border/50" />
        <span>{typeCount} type{typeCount !== 1 ? "s" : ""}</span>
        {lastStored && (
          <>
            <span className="h-3 w-px bg-syzygy-surface-border/50" />
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              Last stored: {formatDate(lastStored)}
            </span>
          </>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 shrink-0 text-syzygy-grey/40" />
        <div className="flex flex-wrap items-center gap-1.5">
          {MEMORY_TYPES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setMemoryType(t)}
              className={cn(
                "rounded-md px-2.5 py-1 text-[11px] font-medium transition-all",
                memoryType === t
                  ? "bg-syzygy-gold/20 text-syzygy-gold-light border border-syzygy-gold/30"
                  : "text-syzygy-grey/50 hover:text-syzygy-grey-light border border-transparent hover:border-syzygy-surface-border"
              )}
            >
              {t === "all" ? "All" : t.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            </button>
          ))}
        </div>
        <span className="h-4 w-px bg-syzygy-surface-border/50" />
        <div className="flex flex-wrap items-center gap-1.5">
          {POLARITIES.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPolarity(p)}
              className={cn(
                "rounded-md px-2.5 py-1 text-[11px] font-medium transition-all",
                polarity === p
                  ? "bg-syzygy-gold/20 text-syzygy-gold-light border border-syzygy-gold/30"
                  : "text-syzygy-grey/50 hover:text-syzygy-grey-light border border-transparent hover:border-syzygy-surface-border"
              )}
            >
              {p === "all" ? "All" : p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
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
        <VoiceButton onTranscript={(t) => setQuery((prev) => prev + t)} />
        <Button type="submit" disabled={searching} variant="ghost" size="sm">
          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </Button>
      </form>

      <FileLinkUpload files={uploadedFiles} links={attachedLinks} onChange={(f, l) => { setUploadedFiles(f); setAttachedLinks(l); }} disabled={searching} />

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
          {memories.map((mem) => {
            const isExpanded = expandedId === mem.id;
            const badge = mem.memory_type ? TYPE_BADGE[mem.memory_type] : "";
            return (
              <div key={mem.id} className="syzygy-card-glass rounded-xl transition-all hover:border-syzygy-gold/30 overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleExpand(mem.id)}
                  className="flex w-full items-start gap-2 p-4 text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {mem.memory_type && (
                        <span className={cn("rounded-md border px-1.5 py-0.5 text-[10px] font-medium", badge)}>
                          {mem.memory_type.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                        </span>
                      )}
                      {mem.polarity && (
                        <span className="rounded-md bg-syzygy-shadow/50 px-1.5 py-0.5 text-[10px] text-syzygy-grey/60">
                          {mem.polarity}
                        </span>
                      )}
                    </div>
                    <p className={cn("text-sm text-syzygy-grey leading-relaxed", !isExpanded && "line-clamp-2")}>
                      {mem.content}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleDelete(mem.id); }}
                      className="rounded p-1.5 text-syzygy-grey/30 transition-colors hover:bg-red-500/10 hover:text-red-400"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                    <div className="text-syzygy-grey/30">
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </div>
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-syzygy-surface-border/50 px-4 pb-4 pt-3 space-y-2.5 animate-fade-in">
                    {mem.content && (
                      <p className="text-sm text-foreground/80 leading-relaxed">{mem.content}</p>
                    )}
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      {mem.agent_id && (
                        <div className="flex items-center gap-1.5 text-syzygy-grey/50">
                          <span className="font-medium text-syzygy-grey/60">Agent:</span>
                          <span className="text-syzygy-grey-light truncate">{mem.agent_id}</span>
                        </div>
                      )}
                      {mem.memory_type && (
                        <div className="flex items-center gap-1.5 text-syzygy-grey/50">
                          <span className="font-medium text-syzygy-grey/60">Type:</span>
                          <span className="text-syzygy-grey-light">{mem.memory_type}</span>
                        </div>
                      )}
                      {mem.polarity && (
                        <div className="flex items-center gap-1.5 text-syzygy-grey/50">
                          <span className="font-medium text-syzygy-grey/60">Polarity:</span>
                          <span className="text-syzygy-grey-light">{mem.polarity}</span>
                        </div>
                      )}
                      {mem.importance_score !== undefined && (
                        <div className="flex items-center gap-1.5 text-syzygy-grey/50">
                          <span className="font-medium text-syzygy-grey/60">Importance:</span>
                          <span className="text-syzygy-grey-light">{mem.importance_score}</span>
                        </div>
                      )}
                      {mem.tags && mem.tags.length > 0 && (
                        <div className="col-span-2 flex items-center gap-1.5 text-syzygy-grey/50">
                          <Tags className="h-3 w-3" />
                          <span className="font-medium text-syzygy-grey/60">Tags:</span>
                          <div className="flex flex-wrap gap-1">
                            {mem.tags.map((tag) => (
                              <span key={tag} className="rounded bg-syzygy-shadow/40 px-1.5 py-0.5 text-[10px] text-syzygy-grey/60">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    {mem.created_at && (
                      <div className="flex items-center gap-1 text-[10px] text-syzygy-grey/40">
                        <Clock className="h-3 w-3" />
                        {formatDate(mem.created_at)}
                        {mem.updated_at && mem.updated_at !== mem.created_at && (
                          <span className="text-syzygy-grey/30">(updated {formatDate(mem.updated_at)})</span>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
