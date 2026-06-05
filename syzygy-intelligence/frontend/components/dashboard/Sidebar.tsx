"use client";

import { cn } from "@/lib/utils";
import {
  FlaskConical,
  Users,
  Brain,
  FileText,
  Code2,
  Search,
  Settings,
  Workflow,
  Library,
  MessageSquare,
  TrendingUp,
  Palette,
} from "lucide-react";
import { usePathname } from "next/navigation";
import Link from "next/link";

const navItems = [
  { icon: FlaskConical, label: "Dashboard", href: "/" },
  { icon: Users, label: "Agents", href: "/agents" },
  { icon: Brain, label: "Consensus", href: "/consensus" },
  { icon: MessageSquare, label: "Chat", href: "/chat" },
  { icon: Workflow, label: "Workflows", href: "/workflows" },
  { icon: Search, label: "Research", href: "/research" },
  { icon: Code2, label: "Code", href: "/code" },
  { icon: FileText, label: "Content", href: "/content" },
  { icon: Library, label: "Memory", href: "/memory" },
  { icon: TrendingUp, label: "Improve", href: "/improve" },
  { icon: Palette, label: "Brand", href: "/brand" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="syzygy-sidebar relative flex w-16 flex-col items-center py-4 transition-all duration-300 md:w-64">
      {/* Brand */}
      <Link href="/" className="mb-6 flex flex-col items-center gap-2 px-4">
        <div className="animate-brand-glow flex flex-col items-center gap-1">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-16 w-auto brightness-110"
          />
          <img
            src="/branding/syzygy.logo.png"
            alt="SYZYGY"
            className="hidden h-12 w-auto brightness-110 md:block"
          />
        </div>
        <span className="hidden text-[8px] uppercase tracking-[0.3em] text-syzygy-grey/40 md:block">
          Intelligence
        </span>
      </Link>

      <div className="mb-4 hidden items-center gap-3 md:flex">
        <img src="/branding/sol.logo.png" alt="Sol" className="h-[72px] w-auto brightness-110" />
        <div className="h-[1px] w-8 bg-gradient-to-r from-syzygy-gold/60 via-syzygy-bone to-syzygy-grey/60" />
        <img src="/branding/luna.logo.png" alt="Luna" className="h-[60px] w-auto brightness-110" />
      </div>

      <nav className="flex w-full flex-1 flex-col gap-1 px-2">
        {navItems.map((item, i) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-200",
                isActive
                  ? "bg-syzygy-gold/10 text-syzygy-gold-light shadow-sm shadow-syzygy-gold/10"
                  : "text-syzygy-grey/60 hover:bg-syzygy-obsidian hover:text-syzygy-grey-light"
              )}
              style={{ animationDelay: `${0.3 + i * 0.05}s` }}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span className="hidden md:block">{item.label}</span>
              {isActive && (
                <div className="ml-auto hidden h-1.5 w-1.5 rounded-full bg-syzygy-gold md:block" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex items-center gap-2 px-4 py-3">
        <div className="flex items-center gap-1.5 rounded-full border border-syzygy-surface-border bg-syzygy-shadow/50 px-2 py-1">
          <img src="/branding/sol.logo.png" alt="Sol" className="h-14 w-auto brightness-110" />
          <div className="h-3 w-6 rounded-full bg-gradient-to-r from-syzygy-gold/40 to-syzygy-grey/40" />
          <img src="/branding/luna.logo.png" alt="Luna" className="h-12 w-auto brightness-110" />
        </div>
      </div>
    </aside>
  );
}
