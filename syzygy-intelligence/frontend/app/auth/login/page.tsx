"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

interface Ember {
  id: number;
  x: number;
  delay: number;
  size: number;
  duration: number;
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [focusField, setFocusField] = useState<"email" | "password" | null>(null);
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [embers, setEmbers] = useState<Ember[]>([]);
  useEffect(() => {
    setEmbers(
      Array.from({ length: 12 }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        delay: Math.random() * 8,
        size: 2 + Math.random() * 3,
        duration: 6 + Math.random() * 6,
      }))
    );
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-gradient-to-br from-syzygy-obsidian via-syzygy-shadow to-syzygy-obsidian px-4">
      {/* Background embers */}
      {embers.map((ember) => (
        <div
          key={ember.id}
          className="aether-particle"
          style={{
            left: `${ember.x}%`,
            bottom: "-10px",
            width: `${ember.size}px`,
            height: `${ember.size}px`,
            animationDelay: `${ember.delay}s`,
            animationDuration: `${ember.duration}s`,
          }}
        />
      ))}

      {/* Background sigil */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.03]">
        <div className="animate-sigil-pulse h-[600px] w-[600px] rounded-full border border-syzygy-gold/20" />
      </div>

      {/* Expanding rings */}
      <div className="pointer-events-none absolute flex items-center justify-center">
        <div className="animate-ring-expand absolute h-64 w-64 rounded-full border border-syzygy-gold/30" style={{ animationDelay: "0s" }} />
        <div className="animate-ring-expand absolute h-64 w-64 rounded-full border border-syzygy-gold/20" style={{ animationDelay: "1s" }} />
        <div className="animate-ring-expand absolute h-64 w-64 rounded-full border border-syzygy-gold/10" style={{ animationDelay: "2s" }} />
      </div>

      {/* ─── Triangle wrapper: card sits at the centroid ─── */}
      <div className="relative w-full max-w-lg py-28">
        {/* SVG connecting lines */}
        <svg
          className="pointer-events-none absolute inset-0 h-full w-full"
          viewBox="0 0 512 480"
          preserveAspectRatio="xMidYMid meet"
        >
          <line x1="256" y1="30" x2="100" y2="400" stroke="url(#goldDash1)" strokeWidth="1" strokeDasharray="4 5" className="opacity-40" />
          <line x1="256" y1="30" x2="412" y2="400" stroke="url(#goldDash2)" strokeWidth="1" strokeDasharray="4 5" className="opacity-40" />
          <line x1="100" y1="400" x2="412" y2="400" stroke="url(#goldDash3)" strokeWidth="1" strokeDasharray="2 6" className="opacity-20" />
          <defs>
            <linearGradient id="goldDash1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#d4a843" stopOpacity="0.2" />
              <stop offset="50%" stopColor="#d4a843" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#d4a843" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="goldDash2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#d4a843" stopOpacity="0.2" />
              <stop offset="50%" stopColor="#d4a843" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#d4a843" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="goldDash3" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#d4a843" stopOpacity="0" />
              <stop offset="50%" stopColor="#d4a843" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#d4a843" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        {/* Rebis — top vertex */}
        <div className="absolute left-1/2 top-[5px] -translate-x-1/2">
          <div className="rebis-fusion">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-syzygy-gold/10 to-syzygy-bone/5 ring-1 ring-syzygy-gold/30 shadow-lg shadow-syzygy-gold/10">
              <img src="/branding/rebis.logo.png" alt="Rebis" className="h-12 w-auto brightness-110 drop-shadow-[0_0_8px_#d4a84340]" />
            </div>
          </div>
        </div>

        {/* Sol — left vertex */}
        <div className="absolute bottom-[38px] left-[calc(50%-156px)] -translate-x-1/2">
          <div className="polarity-sun">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-syzygy-gold/10 to-amber-900/10 ring-1 ring-syzygy-gold/20 shadow-sm">
              <img src="/branding/sol.logo.png" alt="Sol" className="h-10 w-auto brightness-110" />
            </div>
          </div>
        </div>

        {/* Luna — right vertex */}
        <div className="absolute bottom-[38px] right-[calc(50%-156px)] translate-x-1/2">
          <div className="polarity-moon">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-syzygy-grey/10 to-syzygy-bone/10 ring-1 ring-syzygy-grey/20 shadow-sm">
              <img src="/branding/luna.logo.png" alt="Luna" className="h-9 w-auto brightness-110" />
            </div>
          </div>
        </div>

        {/* Card — at the centroid of the triangle */}
        <div className="gradient-border-gold relative z-10 mx-auto w-full max-w-md animate-fade-in-up rounded-2xl">
          <div className="relative bg-syzygy-shadow/90 px-8 pb-8 pt-8 backdrop-blur-xl rounded-2xl">
            {/* Title */}
            <div className="mb-8 text-center">
              <p className="syzygy-title text-2xl font-bold tracking-wider">SYZYGY</p>
              <p className="animate-flicker-gold mt-1.5 text-xs text-syzygy-grey/40 tracking-[0.15em] uppercase">
                Aligning opposites into unified intelligence
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="mb-1.5 block text-xs font-medium tracking-wide text-syzygy-grey/70">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setFocusField("email")}
                  onBlur={() => setFocusField(null)}
                  placeholder="you@example.com"
                  required
                  className={cn(
                    "w-full rounded-lg border bg-syzygy-obsidian/50 px-3 py-2.5 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-all duration-300",
                    focusField === "email"
                      ? "border-syzygy-gold/60 shadow-[0_0_12px_#d4a84320]"
                      : "border-syzygy-surface-border"
                  )}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium tracking-wide text-syzygy-grey/70">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusField("password")}
                    onBlur={() => setFocusField(null)}
                    placeholder="Enter your password"
                    required
                    minLength={8}
                    className={cn(
                      "w-full rounded-lg border bg-syzygy-obsidian/50 px-3 py-2.5 pr-10 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-all duration-300",
                      focusField === "password"
                        ? "border-syzygy-gold/60 shadow-[0_0_12px_#d4a84320]"
                        : "border-syzygy-surface-border"
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-syzygy-grey/50 transition-colors hover:text-syzygy-grey"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              {error && (
                <div className="animate-fade-in-up rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                  {error}
                </div>
              )}
              <button
                type="submit"
                disabled={loading}
                className="group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-lg bg-syzygy-gold/20 px-4 py-2.5 text-sm font-medium text-syzygy-gold-light transition-all duration-300 hover:bg-syzygy-gold/30 hover:shadow-[0_0_20px_#d4a84320] disabled:opacity-50"
              >
                <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  <div className="animate-border-rotate absolute inset-0 rounded-lg" style={{ padding: "1px", WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)", WebkitMaskComposite: "xor", maskComposite: "exclude" }} />
                </div>
                {loading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-syzygy-gold/30 border-t-syzygy-gold" />
                ) : (
                  <LogIn className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
                )}
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="sigil-divider my-6" />
            <p className="text-center text-xs text-syzygy-grey/50">
              Don&apos;t have an account?{" "}
              <Link
                href="/auth/register"
                className="text-syzygy-gold transition-all duration-300 hover:text-syzygy-gold-light hover:drop-shadow-[0_0_8px_#d4a84340]"
              >
                Create one
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
