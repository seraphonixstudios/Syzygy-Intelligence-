"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Search, FileText, Trash2, Loader2, Database, CheckCircle, XCircle, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { API_URL as API } from "@/lib/config";
import { VoiceButton } from "@/components/VoiceButton";

interface DocEntry {
  source: string;
  chunk_count: number;
}

interface ResultEntry {
  content: string;
  score: number;
  metadata: Record<string, string>;
}

interface BatchResult {
  file: string;
  chunks: number;
  status: string;
}

interface BatchError {
  file: string;
  error: string;
}

const SUGGESTIONS = [
  "Find documents about consensus engine",
  "Search for polarity archetypes",
  "Show me all memory entries about fusion",
  "Find research on agent individuation",
];

export default function RAGPage() {
  const [documents, setDocuments] = useState<DocEntry[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ResultEntry[]>([]);
  const [searching, setSearching] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [batchResults, setBatchResults] = useState<{ results: BatchResult[]; errors: BatchError[] } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/rag/documents`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDocuments(data.documents || data || []);
    } catch (err) {
      logger.error("Failed to load documents", err, "RAG");
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const validExt = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase();
    return ["txt", "md", "pdf"].includes(ext || "");
  };

  const handleFiles = async (files: FileList | File[]) => {
    const valid = Array.from(files).filter((f) => validExt(f.name));
    if (valid.length === 0) {
      toast.error("No valid files (.txt, .md, .pdf)");
      return;
    }
    if (valid.length !== files.length) {
      toast.warning(`${files.length - valid.length} file(s) skipped (unsupported type)`);
    }
    if (valid.length === 1) {
      await handleSingleUpload(valid[0]);
    } else {
      await handleBatchUpload(valid);
    }
  };

  const handleSingleUpload = async (file: File) => {
    setIngesting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API}/api/rag/ingest`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`Ingested "${file.name}"`);
      loadDocuments();
    } catch (err) {
      logger.error("File ingest failed", err, "RAG");
      toast.error(`Failed to ingest "${file.name}"`);
    } finally {
      setIngesting(false);
    }
  };

  const handleBatchUpload = async (files: File[]) => {
    setIngesting(true);
    setBatchResults(null);
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));
      const res = await fetch(`${API}/api/rag/ingest/batch`, { method: "POST", body: formData });
      const data = await res.json();
      setBatchResults(data);
      if (data.results?.length) toast.success(`Ingested ${data.results.length} file(s)`);
      if (data.errors?.length) toast.error(`${data.errors.length} file(s) failed`);
      loadDocuments();
    } catch (err) {
      logger.error("Batch ingest failed", err, "RAG");
      toast.error("Batch ingest request failed");
    } finally {
      setIngesting(false);
      setSelectedFiles([]);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) handleFiles(e.target.files);
    e.target.value = "";
  };

  const handleTextIngest = async () => {
    if (!textInput.trim()) return;
    setIngesting(true);
    try {
      const res = await fetch(`${API}/api/rag/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textInput.trim(), source: "text_input" }),
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success("Text ingested");
      setTextInput("");
      loadDocuments();
    } catch (err) {
      logger.error("Text ingest failed", err, "RAG");
      toast.error("Text ingestion failed");
    } finally {
      setIngesting(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API}/api/rag/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), top_k: 10 }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      logger.error("Search failed", err, "RAG");
      toast.error("Search failed");
    } finally {
      setSearching(false);
    }
  };

  const handleDelete = async (source: string) => {
    try {
      const res = await fetch(`${API}/api/rag/documents`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`Deleted "${source}"`);
      loadDocuments();
    } catch (err) {
      logger.error("Delete failed", err, "RAG");
      toast.error("Delete failed");
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col space-y-4">
      <div className="flex items-center gap-3 shrink-0">
        <img src="/branding/pagetop.logo.png" alt="Syzygy" className="h-8 w-auto brightness-110" width={32} height={32} />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Knowledge Base</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Document ingestion and semantic search</p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row flex-1 gap-4 min-h-0">
        {/* Left panel: Upload + Ingest */}
        <div className="flex w-full md:w-96 shrink-0 flex-col gap-4 overflow-y-auto">
          {/* Drag-drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
              dragOver
                ? "border-syzygy-gold bg-syzygy-gold/10"
                : "border-syzygy-surface-border hover:border-syzygy-gold/40"
            } ${ingesting ? "opacity-50 pointer-events-none" : ""}`}
          >
            {ingesting ? (
              <Loader2 className="h-8 w-8 animate-spin text-syzygy-gold" />
            ) : (
              <Upload className="h-8 w-8 text-syzygy-grey/40" />
            )}
            <div>
              <p className="text-sm text-syzygy-grey/60">
                {ingesting ? "Ingesting..." : "Drop files or click to upload"}
              </p>
              <p className="mt-1 text-[10px] text-syzygy-grey/40">.txt .md .pdf (multi-file supported)</p>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md,.pdf"
              multiple
              className="hidden"
              onChange={handleFileInputChange}
              disabled={ingesting}
            />
          </div>

          {/* Batch results */}
          {batchResults && (
            <div className="space-y-1.5 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-syzygy-grey/50">Batch Results</h3>
              {batchResults.results?.map((r, i) => (
                <div key={r.file} className="flex items-center gap-2 text-xs text-syzygy-grey/70">
                  <CheckCircle className="h-3 w-3 shrink-0 text-green-500" />
                  <span className="truncate">{r.file}</span>
                  <span className="ml-auto text-syzygy-gold/60">{r.chunks} chunks</span>
                </div>
              ))}
              {batchResults.errors?.map((e, i) => (
                <div key={e.file} className="flex items-center gap-2 text-xs text-red-400/70">
                  <XCircle className="h-3 w-3 shrink-0" />
                  <span className="truncate">{e.file}</span>
                  <span className="ml-auto">{e.error}</span>
                </div>
              ))}
            </div>
          )}

          {/* Text ingest */}
          <div className="space-y-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-syzygy-grey/50">Or paste text</h3>
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Paste raw text content to ingest..."
              rows={4}
              className="w-full resize-none rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 p-3 text-xs text-foreground placeholder-syzygy-grey/40 outline-none transition-colors focus:border-syzygy-gold/40"
              disabled={ingesting}
            />
            <Button
              onClick={handleTextIngest}
              disabled={!textInput.trim() || ingesting}
              variant="occult"
              size="sm"
              className="w-full gap-1.5"
            >
              {ingesting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Database className="h-3.5 w-3.5" />}
              {ingesting ? "Ingesting..." : "Ingest"}
            </Button>
          </div>
        </div>

        {/* Right panel: Query + Results + Document list */}
        <div className="flex flex-1 flex-col gap-4 min-h-0">
          {/* Search */}
          <div className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
            <Search className="h-4 w-4 shrink-0 text-syzygy-grey/40" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search the knowledge base..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
              disabled={searching}
            />
            <VoiceButton onTranscript={(t) => setQuery((prev) => prev + t)} />
            <Button
              onClick={handleSearch}
              disabled={!query.trim() || searching}
              variant="gold"
              size="sm"
              className="shrink-0 gap-1"
            >
              {searching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
              Search
            </Button>
          </div>

          {/* Suggestions */}
          {!searching && results.length === 0 && (
            <div className="space-y-3">
              <p className="text-xs text-syzygy-grey/40">Try searching for:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setQuery(s)}
                    className="rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/30 px-3 py-1.5 text-xs text-syzygy-grey/60 transition-all hover:border-syzygy-gold/30 hover:text-syzygy-gold hover:bg-syzygy-gold/5"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {results.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-syzygy-grey/50">
                Results ({results.length})
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {results.map((r, i) => (
                  <div
                    key={r.metadata?.source ?? r.content.slice(0, 40)}
                    className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-4 transition-colors hover:border-syzygy-gold/20"
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-medium uppercase tracking-wider text-syzygy-grey/40">
                            Relevance
                          </span>
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-syzygy-surface-border/30">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-syzygy-gold/60 to-syzygy-gold"
                              style={{ width: `${Math.round(r.score * 100)}%` }}
                            />
                          </div>
                          <span className="text-[10px] font-mono text-syzygy-gold">
                            {Math.round(r.score * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <p className="mb-2 text-xs leading-relaxed text-syzygy-grey">{r.content}</p>
                    {r.metadata?.source && (
                      <div className="flex items-center gap-1.5 text-[10px] text-syzygy-grey/40">
                        <FileText className="h-3 w-3" />
                        <span className="truncate">{r.metadata.source}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Document list */}
          <div className="flex-1 space-y-2 overflow-y-auto">
            <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-syzygy-grey/50">
              <Database className="h-3 w-3" />
              Documents ({documents.length})
            </h3>
            {documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FileText className="mb-2 h-8 w-8 text-syzygy-grey/20" />
                <p className="text-xs text-syzygy-grey/40">No documents ingested yet</p>
              </div>
            ) : (
              <div className="space-y-1">
                {documents.map((doc, i) => (
                  <div
                    key={doc.source}
                    className="flex items-center gap-3 rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/20 px-3 py-2 transition-colors hover:bg-syzygy-shadow/40"
                  >
                    <FileText className="h-4 w-4 shrink-0 text-syzygy-grey/40" />
                    <span className="flex-1 truncate text-xs text-syzygy-grey">{doc.source}</span>
                    <span className="shrink-0 rounded-md bg-syzygy-gold/10 px-1.5 py-0.5 text-[10px] font-mono text-syzygy-gold">
                      {doc.chunk_count} chunks
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDelete(doc.source)}
                      className="shrink-0 text-syzygy-grey/30 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
