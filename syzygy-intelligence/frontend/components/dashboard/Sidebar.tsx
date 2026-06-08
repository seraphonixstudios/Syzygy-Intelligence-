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
  Cloud,
  Database,
  LogIn,
  LogOut,
  User,
  Gauge,
  Shield,
} from "lucide-react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";

const navItems = [
  { icon: Cloud, label: "Cloud", href: "/cloud" },
  { icon: FlaskConical, label: "Dashboard", href: "/" },
  { icon: Users, label: "Agents", href: "/agents" },
  { icon: Brain, label: "Consensus", href: "/consensus" },
  { icon: MessageSquare, label: "Chat", href: "/chat" },
  { icon: Database, label: "Knowledge", href: "/rag" },
  { icon: Workflow, label: "Workflows", href: "/workflows" },
  { icon: Search, label: "Research", href: "/research" },
  { icon: Code2, label: "Code", href: "/code" },
  { icon: FileText, label: "Content", href: "/content" },
  { icon: Library, label: "Memory", href: "/memory" },
  { icon: TrendingUp, label: "Improve", href: "/improve" },
  { icon: Palette, label: "Brand", href: "/brand" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

const authPaths = ["/auth/login", "/auth/register"];

export function Sidebar() {
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  useEffect(() => {
    if (isAuthenticated && !user) {
      fetchMe();
    }
  }, [isAuthenticated, user, fetchMe]);

  if (authPaths.includes(pathname)) return null;

  return (
    <aside className="syzygy-sidebar relative flex w-16 flex-col items-center py-4 transition-all duration-300 md:w-64">
      {/* Brand */}
      <Link href="/" className="mb-3 flex flex-col items-center gap-1 px-4">
        <div className="animate-brand-glow flex flex-col items-center gap-0.5">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-12 w-auto brightness-110"
            width={48} height={48}
          />
          <img
            src="/branding/syzygy.logo.png"
            alt="SYZYGY"
            className="hidden h-8 w-auto brightness-110 md:block"
            width={32} height={32}
          />
        </div>
        <span className="hidden text-[7px] uppercase tracking-[0.2em] text-syzygy-grey/40 md:block">
          Intelligence
        </span>
      </Link>

      <div className="mb-2 hidden items-center gap-2 md:flex">
        <img src="/branding/sol.logo.png" alt="Sol" className="h-[48px] w-auto brightness-110" />
        <div className="h-[1px] w-6 bg-gradient-to-r from-syzygy-gold/60 via-syzygy-bone to-syzygy-grey/60" />
        <img src="/branding/luna.logo.png" alt="Luna" className="h-[40px] w-auto brightness-110" />
      </div>

      <nav className="flex w-full flex-1 flex-col gap-0.5 overflow-y-auto px-2 scrollbar-thin">
        {navItems.map((item, i) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all duration-200",
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

      {/* Admin link */}
      {user?.is_superuser && (
        <div className="w-full px-2 pb-1">
          <Link
            href="/admin"
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-xs transition-all duration-200",
              pathname === "/admin"
                ? "bg-syzygy-gold/10 text-syzygy-gold-light"
                : "text-syzygy-grey/40 hover:bg-syzygy-obsidian hover:text-syzygy-gold"
            )}
          >
            <Shield className="h-3.5 w-3.5 shrink-0" />
            <span className="hidden md:block">Admin</span>
          </Link>
        </div>
      )}

      {/* Auth section */}
      <div className="w-full border-t border-syzygy-surface-border px-2 pt-3 mt-2">
        {isAuthenticated && user ? (
          <div className="space-y-2">
            {/* Usage bar */}
            {user.subscription_tier === "free" && (
              <div className="hidden md:block px-3 py-1.5">
                <div className="flex items-center justify-between text-[10px] text-syzygy-grey/50 mb-1">
                  <span className="flex items-center gap-1">
                    <Gauge className="h-3 w-3" />
                    Messages
                  </span>
                  <span>{user.message_count}/{user.monthly_message_limit}</span>
                </div>
                <div className="h-1 rounded-full bg-syzygy-surface-border overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      user.message_count / user.monthly_message_limit > 0.8
                        ? "bg-red-500"
                        : "bg-syzygy-gold/60"
                    )}
                    style={{
                      width: `${Math.min(100, (user.message_count / user.monthly_message_limit) * 100)}%`,
                    }}
                  />
                </div>
                {user.trial_ends_at && new Date(user.trial_ends_at) > new Date() ? (
                  <p className="text-[9px] text-syzygy-gold/40 mt-1">
                    Trial &middot; Unlimited
                  </p>
                ) : user.message_count >= user.monthly_message_limit ? (
                  <p className="text-[9px] text-red-400/60 mt-1">
                    Limit reached &middot; <Link href="/cloud" className="underline">Upgrade</Link>
                  </p>
                ) : null}
              </div>
            )}

            {/* User info + logout */}
            <button
              onClick={logout}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-syzygy-grey/50 transition-colors hover:bg-syzygy-obsidian hover:text-red-400"
            >
              <LogOut className="h-3.5 w-3.5 hidden md:block" />
              <User className="h-3.5 w-3.5 md:hidden" />
              <span className="hidden md:block truncate">{user.display_name || user.email}</span>
            </button>
          </div>
        ) : (
          <Link
            href="/auth/login"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-syzygy-grey/50 transition-colors hover:bg-syzygy-obsidian hover:text-syzygy-gold"
          >
            <LogIn className="h-3.5 w-3.5" />
            <span className="hidden md:block">Sign In</span>
          </Link>
        )}
      </div>
    </aside>
  );
}
