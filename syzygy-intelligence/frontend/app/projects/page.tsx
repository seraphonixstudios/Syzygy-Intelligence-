"use client";

import { FolderKanban, GitBranch, Clock, Sparkles, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const recentProjects = [
  { name: "REST API in Python", language: "python", date: "2 hours ago", status: "completed", files: 3 },
  { name: "CLI tool in Go", language: "go", date: "1 day ago", status: "completed", files: 2 },
  { name: "Data viz in JS", language: "javascript", date: "3 days ago", status: "completed", files: 4 },
];

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-8 w-auto brightness-110"
            width={32} height={32}
          />
          <div>
            <h1 className="syzygy-title text-2xl font-bold tracking-wider">Projects</h1>
            <p className="mt-0.5 text-xs text-syzygy-grey/60">Manage and revisit your coding projects</p>
          </div>
        </div>
        <Link href="/code">
          <Button variant="gold" size="sm" className="gap-1.5">
            <Plus className="h-3.5 w-3.5" />
            New Project
          </Button>
        </Link>
      </div>

      {recentProjects.length > 0 ? (
        <div className="grid gap-3">
          {recentProjects.map((p) => (
            <div
              key={p.name}
              className="group flex items-center gap-4 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-5 py-4 transition-all duration-300 hover:border-syzygy-gold/30 hover:bg-syzygy-shadow/80 cursor-pointer"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-syzygy-gold/10 text-syzygy-gold">
                <FolderKanban className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-syzygy-grey-light truncate">{p.name}</h3>
                <div className="flex items-center gap-3 mt-1 text-[10px] text-syzygy-grey/40">
                  <span className="flex items-center gap-1 uppercase">{p.language}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {p.date}
                  </span>
                  <span className="flex items-center gap-1">
                    <GitBranch className="h-3 w-3" />
                    {p.files} files
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-[10px] text-green-400 border border-green-500/20">
                  {p.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <Sparkles className="h-10 w-10 text-syzygy-gold/20" />
          <p className="text-sm text-syzygy-grey/40">No projects yet — generate some code to get started</p>
          <Link href="/code">
            <Button variant="gold" size="sm" className="gap-1.5 mt-2">
              <Plus className="h-3.5 w-3.5" />
              Create your first project
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
