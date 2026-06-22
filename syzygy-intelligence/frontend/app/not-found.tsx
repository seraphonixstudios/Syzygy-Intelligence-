import Link from "next/link";
import { Home, MessageSquare, Workflow, Code, Settings, Library } from "lucide-react";

const PAGES = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/code", label: "Code", icon: Code },
  { href: "/rag", label: "Knowledge Base", icon: Library },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 px-4">
      <div className="flex flex-col items-center gap-2">
        <h1 className="text-7xl font-bold text-syzygy-grey/20">404</h1>
        <p className="text-lg text-syzygy-grey/50">This page does not exist</p>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {PAGES.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-4 py-3 text-sm text-syzygy-grey/60 transition-all hover:border-syzygy-gold/30 hover:text-syzygy-gold hover:bg-syzygy-gold/5"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}
