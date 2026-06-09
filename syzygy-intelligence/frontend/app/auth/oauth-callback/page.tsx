"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const [message, setMessage] = useState("Completing sign in...");

  useEffect(() => {
    const hash = window.location.hash.slice(1);
    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (!accessToken || !refreshToken) {
      setMessage("Invalid OAuth response. Redirecting to login...");
      setTimeout(() => router.push("/auth/login"), 2000);
      return;
    }

    const store = useAuthStore.getState();
    useAuthStore.setState({
      accessToken,
      refreshToken,
      isAuthenticated: true,
      rememberMe: true,
    });

    store.fetchMe().catch(() => {
      setMessage("Session expired. Redirecting to login...");
      setTimeout(() => router.push("/auth/login"), 2000);
    });

    router.push("/");
  }, [router]);

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-gradient-to-br from-syzygy-obsidian via-syzygy-shadow to-syzygy-obsidian px-4">
      <div className="flex flex-col items-center gap-3 text-center">
        <Loader2 className="h-6 w-6 animate-spin text-syzygy-gold" />
        <p className="text-sm text-syzygy-grey/70">{message}</p>
      </div>
    </div>
  );
}
