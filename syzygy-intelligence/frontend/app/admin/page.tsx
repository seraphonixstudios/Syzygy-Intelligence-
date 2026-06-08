"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { cn } from "@/lib/utils";
import {
  Shield,
  Users,
  Mail,
  BarChart3,
  Loader2,
  RefreshCw,
  Search,
  Check,
  X,
  Crown,
  Activity,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Gauge,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

interface UserInfo {
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
  created_at: string;
  last_active_at: string | null;
}

interface SystemStats {
  total_users: number;
  active_users: number;
  superusers: number;
  free_users: number;
  premium_users: number;
  enterprise_users: number;
  total_messages: number;
  users_on_trial: number;
  users_over_limit: number;
}

function StatCard({ icon: Icon, label, value, sub }: { icon: any; label: string; value: number | string; sub?: string }) {
  return (
    <Card className="border-syzygy-surface-border bg-syzygy-card">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-syzygy-gold/10">
            <Icon className="h-5 w-5 text-syzygy-gold" />
          </div>
          <div>
            <p className="text-xs text-syzygy-grey/50">{label}</p>
            <p className="text-xl font-bold text-foreground">{value}</p>
            {sub && <p className="text-[10px] text-syzygy-grey/40">{sub}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AdminPage() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const [users, setUsers] = useState<UserInfo[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const [usersRes, statsRes] = await Promise.all([
        fetch(`${API}/api/admin/users`, { headers }),
        fetch(`${API}/api/admin/stats`, { headers }),
      ]);
      if (!usersRes.ok) throw new Error(usersRes.status === 403 ? "Admin access required" : "Failed to fetch users");
      if (!statsRes.ok) throw new Error("Failed to fetch stats");
      setUsers(await usersRes.json());
      setStats(await statsRes.json());
    } catch (err: any) {
      setError(err.message);
      logger.error("Admin fetch failed", err, "Admin");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    if (isAuthenticated && user?.is_superuser) {
      fetchData();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, user, fetchData]);

  const handleToggleActive = async (userId: string, current: boolean) => {
    setActionLoading(userId);
    try {
      const res = await fetch(`${API}/api/admin/users/${userId}`, {
        method: "PUT",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !current }),
      });
      if (!res.ok) throw new Error("Failed to update user");
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_active: !current } : u)));
      toast.success(current ? "User disabled" : "User enabled");
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleAdmin = async (userId: string, current: boolean) => {
    setActionLoading(userId);
    try {
      const res = await fetch(`${API}/api/admin/users/${userId}`, {
        method: "PUT",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ is_superuser: !current }),
      });
      if (!res.ok) throw new Error("Failed to update user");
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_superuser: !current } : u)));
      toast.success(current ? "Admin removed" : "Admin granted");
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (userId: string) => {
    if (!confirm("Disable this user? They can be re-enabled later.")) return;
    setActionLoading(userId);
    try {
      const res = await fetch(`${API}/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error("Failed to disable user");
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, is_active: false } : u)));
      toast.success("User disabled");
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-syzygy-grey/50">Sign in to access admin panel.</p>
      </div>
    );
  }

  if (user && !user.is_superuser) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-syzygy-grey/50">You do not have admin access.</p>
      </div>
    );
  }

  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.display_name && u.display_name.toLowerCase().includes(search.toLowerCase()))
  );

  const tierBadge = (tier: string) => {
    switch (tier) {
      case "premium": return <Badge variant="masculine" className="text-[9px] px-1.5 py-0">Premium</Badge>;
      case "enterprise": return <Badge variant="unified" className="text-[9px] px-1.5 py-0">Enterprise</Badge>;
      default: return <Badge variant="feminine" className="text-[9px] px-1.5 py-0">Free</Badge>;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-syzygy-gold/10">
            <Shield className="h-5 w-5 text-syzygy-gold" />
          </div>
          <div>
            <h1 className="syzygy-title text-2xl font-bold tracking-wider">Admin</h1>
            <p className="mt-0.5 text-xs text-syzygy-grey/60">User management & system overview</p>
          </div>
        </div>
        <Button variant="gold" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={cn("mr-1 h-4 w-4", loading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {loading && !stats ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-syzygy-gold/60" />
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      ) : (
        <>
          {/* Stats cards */}
          {stats && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard icon={Users} label="Total Users" value={stats.total_users} sub={`${stats.active_users} active`} />
              <StatCard icon={BarChart3} label="Total Messages" value={stats.total_messages} />
              <StatCard icon={Activity} label="On Trial" value={stats.users_on_trial} sub={`${stats.users_over_limit} over limit`} />
              <StatCard icon={Crown} label="Premium" value={stats.premium_users + stats.enterprise_users} sub={`${stats.superusers} admins`} />
            </div>
          )}

          {/* Users table */}
          <Card className="border-syzygy-surface-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4" />
                  Users
                </CardTitle>
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-syzygy-grey/40" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search users..."
                    className="w-48 rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 py-1.5 pl-8 pr-3 text-xs text-foreground outline-none focus:border-syzygy-gold/50"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-syzygy-surface-border/50 text-left text-[10px] uppercase tracking-wider text-syzygy-grey/40">
                      <th className="px-4 py-2.5 font-medium">User</th>
                      <th className="px-4 py-2.5 font-medium">Tier</th>
                      <th className="px-4 py-2.5 font-medium">Messages</th>
                      <th className="px-4 py-2.5 font-medium">Status</th>
                      <th className="px-4 py-2.5 font-medium">Admin</th>
                      <th className="px-4 py-2.5 font-medium">Joined</th>
                      <th className="px-4 py-2.5 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-syzygy-surface-border/30">
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-xs text-syzygy-grey/40">
                          No users found.
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => (
                        <tr key={u.id} className="group text-xs transition-colors hover:bg-syzygy-obsidian/50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-syzygy-gold/10">
                                <Mail className="h-3.5 w-3.5 text-syzygy-gold/60" />
                              </div>
                              <div>
                                <p className="text-sm font-medium text-foreground">{u.display_name || u.email}</p>
                                <p className="text-[10px] text-syzygy-grey/40">{u.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">{tierBadge(u.subscription_tier)}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <Gauge className="h-3 w-3 text-syzygy-grey/40" />
                              <span className={u.message_count >= u.monthly_message_limit ? "text-red-400" : "text-foreground"}>
                                {u.message_count}/{u.monthly_message_limit}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {u.is_active ? (
                              <span className="flex items-center gap-1 text-green-400">
                                <Check className="h-3 w-3" /> Active
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-red-400">
                                <X className="h-3 w-3" /> Disabled
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {u.is_superuser ? (
                              <Badge variant="masculine" className="text-[9px] px-1.5 py-0">Admin</Badge>
                            ) : (
                              <span className="text-syzygy-grey/40">—</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-syzygy-grey/50">{new Date(u.created_at).toLocaleDateString()}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                              <button
                                onClick={() => handleToggleActive(u.id, u.is_active)}
                                disabled={actionLoading === u.id}
                                className="rounded p-1 text-syzygy-grey/40 transition-colors hover:bg-syzygy-surface-border hover:text-foreground"
                                title={u.is_active ? "Disable" : "Enable"}
                              >
                                {actionLoading === u.id ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : u.is_active ? (
                                  <ToggleRight className="h-3.5 w-3.5" />
                                ) : (
                                  <ToggleLeft className="h-3.5 w-3.5" />
                                )}
                              </button>
                              <button
                                onClick={() => handleToggleAdmin(u.id, u.is_superuser)}
                                disabled={actionLoading === u.id}
                                className="rounded p-1 text-syzygy-grey/40 transition-colors hover:bg-syzygy-surface-border hover:text-syzygy-gold"
                                title={u.is_superuser ? "Remove admin" : "Grant admin"}
                              >
                                <Crown className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => handleDelete(u.id)}
                                disabled={actionLoading === u.id}
                                className="rounded p-1 text-syzygy-grey/40 transition-colors hover:bg-red-500/10 hover:text-red-400"
                                title="Disable user"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
