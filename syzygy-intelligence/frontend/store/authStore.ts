"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { StateStorage } from "zustand/middleware";
import { logger } from "@/lib/logger";

import { API_URL } from "@/lib/config";

export interface UserInfo {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  verified_at: string | null;
  trial_ends_at: string | null;
  subscription_tier: string;
  message_count: number;
  monthly_message_limit: number;
  settings: Record<string, unknown>;
  created_at: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
  isAuthenticated: boolean;
  isVerifying: boolean;
  rememberMe: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  fetchMe: () => Promise<void>;
  updateProfile: (data: { display_name?: string }) => Promise<void>;
  getAuthHeaders: () => Record<string, string>;
  setRememberMe: (value: boolean) => void;
}

const sessionAwareStorage: StateStorage = {
  getItem: (name: string) => {
    return sessionStorage.getItem(name) || localStorage.getItem(name);
  },
  setItem: (name: string, value: string) => {
    const parsed = JSON.parse(value);
    const remember = parsed?.state?.rememberMe;
    if (remember !== false) {
      localStorage.setItem(name, value);
      sessionStorage.removeItem(name);
    } else {
      sessionStorage.setItem(name, value);
      localStorage.removeItem(name);
    }
  },
  removeItem: (name: string) => {
    localStorage.removeItem(name);
    sessionStorage.removeItem(name);
  },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isVerifying: true,
      rememberMe: true,

      login: async (email: string, password: string, remember = true) => {
        const res = await fetch(`${API_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({ detail: "Login failed" }));
          throw new Error(body.detail || "Login failed");
        }
        const data = await res.json();
        set({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          isAuthenticated: true,
          rememberMe: remember,
        });
        await get().fetchMe();
      },

      register: async (email: string, password: string, displayName?: string) => {
        const res = await fetch(`${API_URL}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, display_name: displayName }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({ detail: "Registration failed" }));
          throw new Error(body.detail || "Registration failed");
        }
        const data = await res.json();
        set({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          isAuthenticated: true,
        });
        await get().fetchMe();
      },

      logout: () => {
        set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
      },

      refreshAuth: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return;
        try {
          const res = await fetch(`${API_URL}/api/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (!res.ok) throw new Error("Refresh failed");
          const data = await res.json();
          set({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
          });
        } catch {
          set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
        }
      },

      fetchMe: async () => {
        const { accessToken } = get();
        if (!accessToken) return;
        try {
          const res = await fetch(`${API_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });
          if (!res.ok) {
            if (res.status === 401) {
              await get().refreshAuth();
              return;
            }
            throw new Error("Failed to fetch user");
          }
          const user = await res.json();
          set({ user, isAuthenticated: true });
        } catch {
          set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
        }
      },

      updateProfile: async (data: { display_name?: string }) => {
        const { accessToken, user } = get();
        if (!accessToken || !user) throw new Error("Not authenticated");
        const res = await fetch(`${API_URL}/api/auth/me/settings`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            ...user.settings,
            display_name: data.display_name || user.display_name,
          }),
        });
        if (!res.ok) throw new Error("Failed to update profile");
        set({
          user: { ...user, display_name: data.display_name || user.display_name },
        });
      },

      getAuthHeaders: () => {
        const { accessToken } = get();
        return accessToken ? { Authorization: `Bearer ${accessToken}` } : ({} as Record<string, string>);
      },

      setRememberMe: (value: boolean) => {
        set({ rememberMe: value });
      },
    }),
    {
      name: "syzygy-auth",
      storage: createJSONStorage(() => sessionAwareStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        rememberMe: state.rememberMe,
      } as AuthState),
      version: 0,
    },
  )
);
