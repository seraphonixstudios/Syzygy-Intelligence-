"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, CheckCircle2, XCircle, ShieldCheck } from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided.");
      return;
    }

    fetch(`${API}/api/auth/verify-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then(async (res) => {
        const body = await res.json();
        if (res.ok) {
          setStatus("success");
          setMessage("Your email has been verified!");
          setTimeout(() => router.push("/settings"), 2500);
        } else {
          setStatus("error");
          setMessage(body.detail || "Verification failed");
        }
      })
      .catch(() => {
        setStatus("error");
        setMessage("Network error. Please try again.");
      });
  }, [searchParams, router]);

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-gradient-to-br from-syzygy-obsidian via-syzygy-shadow to-syzygy-obsidian px-4">
      <div className="w-full max-w-sm animate-fade-in-up">
        <div className="gradient-border-gold relative rounded-2xl">
          <div className="relative bg-syzygy-shadow/90 px-6 py-8 backdrop-blur-xl rounded-2xl">
            <div className="flex flex-col items-center gap-4 text-center">
              {status === "verifying" && (
                <>
                  <Loader2 className="h-8 w-8 animate-spin text-syzygy-gold" />
                  <p className="text-sm text-syzygy-grey/70">Verifying your email...</p>
                </>
              )}
              {status === "success" && (
                <>
                  <CheckCircle2 className="h-8 w-8 text-syzygy-gold" />
                  <p className="text-sm text-syzygy-gold">{message}</p>
                  <p className="text-xs text-syzygy-grey/50">Redirecting to settings...</p>
                </>
              )}
              {status === "error" && (
                <>
                  <XCircle className="h-8 w-8 text-red-400" />
                  <p className="text-sm text-red-400">{message}</p>
                  <Link
                    href="/auth/login"
                    className="mt-2 text-xs text-syzygy-gold transition-colors hover:text-syzygy-gold-light"
                  >
                    Back to login
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
