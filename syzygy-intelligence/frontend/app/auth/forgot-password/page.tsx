"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, ArrowLeft, Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_URL as API } from "@/lib/config";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Something went wrong");
      }
      const data = await res.json();
      setSent(true);
      // In dev, show the reset token so the user can copy it
      if (data.reset_token) {
        navigator.clipboard?.writeText(data.reset_token);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-gradient-to-br from-syzygy-obsidian via-syzygy-shadow to-syzygy-obsidian px-4">
      {/* Background sigil */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.03]">
        <div className="animate-sigil-pulse h-[600px] w-[600px] rounded-full border border-syzygy-gold/20" />
      </div>

      <div className="w-full max-w-sm animate-fade-in-up">
        <div className="gradient-border-gold relative rounded-2xl">
          <div className="relative bg-syzygy-shadow/90 px-6 py-8 backdrop-blur-xl rounded-2xl">
            <div className="mb-8 text-center">
              <p className="syzygy-title text-2xl font-bold tracking-wider">Reset Password</p>
              <p className="mt-1.5 text-xs text-syzygy-grey/40 tracking-[0.15em] uppercase">
                Enter your email to receive a reset link
              </p>
            </div>

            {sent ? (
              <div className="space-y-5">
                <div className="flex flex-col items-center gap-3 rounded-xl border border-syzygy-gold/20 bg-syzygy-gold/5 px-4 py-6 text-center">
                  <CheckCircle2 className="h-8 w-8 text-syzygy-gold" />
                  <p className="text-sm text-syzygy-grey/70">
                    If that email exists, a reset link has been sent. Please check your inbox.
                  </p>
                </div>
                <Link
                  href="/auth/login"
                  className="flex items-center justify-center gap-2 text-xs text-syzygy-gold transition-all hover:text-syzygy-gold-light"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Back to login
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="mb-1.5 block text-xs font-medium tracking-wide text-syzygy-grey/70">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-syzygy-grey/40" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                      className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 py-2.5 pl-10 pr-3 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-all duration-300 focus:border-syzygy-gold/60 focus:shadow-[0_0_12px_#d4a84320]"
                    />
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
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Mail className="h-4 w-4" />
                  )}
                  {loading ? "Sending..." : "Send Reset Link"}
                </button>

                <Link
                  href="/auth/login"
                  className="flex items-center justify-center gap-2 text-xs text-syzygy-grey/50 transition-colors hover:text-syzygy-grey"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Back to login
                </Link>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
