"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, Loader2, CheckCircle2, KeyRound } from "lucide-react";
import { cn } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState(searchParams.get("token") || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to reset password");
      }
      setDone(true);
      setTimeout(() => router.push("/auth/login"), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset password");
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
              <p className="syzygy-title text-2xl font-bold tracking-wider">Set New Password</p>
              <p className="mt-1.5 text-xs text-syzygy-grey/40 tracking-[0.15em] uppercase">
                Enter your new password below
              </p>
            </div>

            {done ? (
              <div className="flex flex-col items-center gap-3 rounded-xl border border-syzygy-gold/20 bg-syzygy-gold/5 px-4 py-6 text-center">
                <CheckCircle2 className="h-8 w-8 text-syzygy-gold" />
                <p className="text-sm text-syzygy-grey/70">Password has been reset successfully!</p>
                <p className="text-xs text-syzygy-grey/50">Redirecting to login...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="mb-1.5 block text-xs font-medium tracking-wide text-syzygy-grey/70">Reset Token</label>
                  <div className="relative">
                    <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-syzygy-grey/40" />
                    <input
                      type="text"
                      value={token}
                      onChange={(e) => setToken(e.target.value)}
                      placeholder="Paste your reset token here"
                      required
                      className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 py-2.5 pl-10 pr-3 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-all duration-300 focus:border-syzygy-gold/60 focus:shadow-[0_0_12px_#d4a84320]"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-medium tracking-wide text-syzygy-grey/70">New Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 8 characters"
                      required
                      minLength={8}
                      className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 py-2.5 pl-3 pr-10 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-all duration-300 focus:border-syzygy-gold/60 focus:shadow-[0_0_12px_#d4a84320]"
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

                <div>
                  <label className="mb-1.5 block text-xs font-medium tracking-wide text-syzygy-grey/70">Confirm Password</label>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter your password"
                    required
                    minLength={8}
                    className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 py-2.5 pl-3 pr-3 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-all duration-300 focus:border-syzygy-gold/60 focus:shadow-[0_0_12px_#d4a84320]"
                  />
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
                    <KeyRound className="h-4 w-4" />
                  )}
                  {loading ? "Resetting..." : "Reset Password"}
                </button>

                <Link
                  href="/auth/login"
                  className="flex items-center justify-center gap-2 text-xs text-syzygy-grey/50 transition-colors hover:text-syzygy-grey"
                >
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
