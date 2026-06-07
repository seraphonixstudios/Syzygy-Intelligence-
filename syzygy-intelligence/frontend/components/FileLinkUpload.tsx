"use client";

import { useState, useRef, useCallback } from "react";
import { Image, Link, X, FileText, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export interface UploadedFile {
  url: string;
  filename: string;
  size: number;
  content_type?: string;
}

export interface LinkMeta {
  url: string;
  title: string;
  description: string;
  favicon: string;
}

interface FileLinkUploadProps {
  files: UploadedFile[];
  links: LinkMeta[];
  onChange: (files: UploadedFile[], links: LinkMeta[]) => void;
  disabled?: boolean;
}

export function FileLinkUpload({ files, links, onChange, disabled }: FileLinkUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [linkInput, setLinkInput] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (fileList: FileList) => {
    setUploading(true);
    try {
      for (const file of Array.from(fileList)) {
        if (!file.type.startsWith("image/")) {
          toast.error(`Skipped ${file.name} — only images supported`);
          continue;
        }
        if (file.size > 10 * 1024 * 1024) {
          toast.error(`${file.name} exceeds 10MB limit`);
          continue;
        }
        const form = new FormData();
        form.append("file", file);
        const res = await fetch(`${API}/api/uploads/file`, { method: "POST", body: form });
        if (!res.ok) throw new Error(await res.text());
        const data: UploadedFile = await res.json();
        onChange([...files, data], links);
      }
    } catch (err) {
      logger.error("Upload failed", err, "FileLinkUpload");
      toast.error("Upload failed — check backend connection");
    } finally {
      setUploading(false);
    }
  }, [files, links, onChange]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) handleFiles(e.target.files);
    e.target.value = "";
  };

  const addLink = async () => {
    const url = linkInput.trim();
    if (!url) return;
    setLinkInput("");
    if (links.find((l) => l.url === url)) {
      toast.error("Link already added");
      return;
    }
    try {
      const res = await fetch(`${API}/api/uploads/link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (!res.ok) throw new Error(await res.text());
      const meta: LinkMeta = await res.json();
      onChange(files, [...links, meta]);
    } catch (err) {
      logger.error("Link fetch failed", err, "FileLinkUpload");
      toast.error("Could not fetch link preview");
      onChange(files, [...links, { url, title: url, description: "", favicon: "" }]);
    }
  };

  const removeFile = (idx: number) => {
    const next = [...files];
    next.splice(idx, 1);
    onChange(next, links);
  };

  const removeLink = (idx: number) => {
    const next = [...links];
    next.splice(idx, 1);
    onChange(files, next);
  };

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={`flex cursor-pointer items-center gap-2 rounded-lg border border-dashed px-3 py-2 text-xs transition-colors ${
          dragOver
            ? "border-syzygy-gold bg-syzygy-gold/10"
            : "border-syzygy-surface-border hover:border-syzygy-gold/40"
        } ${disabled ? "opacity-50 pointer-events-none" : ""}`}
      >
        {uploading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-syzygy-gold" />
        ) : (
          <Image className="h-3.5 w-3.5 text-syzygy-grey/60" />
        )}
        <span className="text-syzygy-grey/60">{uploading ? "Uploading..." : "Drop image or click to upload"}</span>
        <input ref={fileRef} type="file" accept="image/*" multiple className="hidden" onChange={handleFileInput} disabled={disabled} />
      </div>

      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((f, i) => (
            <div key={i} className="group relative flex items-center gap-1.5 rounded-md border border-syzygy-surface-border bg-syzygy-shadow/50 px-2 py-1">
              <img src={f.url} alt={f.filename} className="h-6 w-6 rounded object-cover" />
              <span className="max-w-[100px] truncate text-[10px] text-syzygy-grey/60">{f.filename}</span>
              <button type="button" onClick={() => removeFile(i)} className="ml-0.5 text-syzygy-grey/40 hover:text-red-400">
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-lg border border-syzygy-surface-border bg-transparent px-3 py-1.5">
          <Link className="h-3.5 w-3.5 shrink-0 text-syzygy-grey/40" />
          <input
            type="text"
            value={linkInput}
            onChange={(e) => setLinkInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addLink())}
            placeholder="Paste a URL..."
            className="flex-1 bg-transparent text-xs text-foreground placeholder-syzygy-grey/40 outline-none"
            disabled={disabled}
          />
        </div>
        <button
          type="button"
          onClick={addLink}
          disabled={!linkInput.trim() || disabled}
          className="flex shrink-0 items-center gap-1 rounded-lg border border-syzygy-surface-border px-2.5 py-1.5 text-xs text-syzygy-grey/60 hover:text-syzygy-gold hover:border-syzygy-gold/30 disabled:opacity-30"
        >
          <Plus className="h-3 w-3" />
          Add
        </button>
      </div>

      {links.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {links.map((l, i) => (
            <div key={i} className="group flex items-center gap-1.5 rounded-md border border-syzygy-surface-border bg-syzygy-shadow/50 px-2 py-1">
              {l.favicon ? (
                <img src={l.favicon} alt="" className="h-3.5 w-3.5" />
              ) : (
                <Link className="h-3 w-3 text-syzygy-grey/40" />
              )}
              <a href={l.url} target="_blank" rel="noopener noreferrer" className="max-w-[160px] truncate text-[10px] text-syzygy-gold-light hover:underline">{l.title}</a>
              <button type="button" onClick={() => removeLink(i)} className="ml-0.5 text-syzygy-grey/40 hover:text-red-400">
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
