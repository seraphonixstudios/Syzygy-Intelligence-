"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Settings as SettingsIcon, Save, RefreshCw, Loader2, User, Shield, MessageSquare, Calendar, ShieldCheck, AlertTriangle, Key, Copy, Trash2, Plus, CheckCircle2, XCircle, ExternalLink, Monitor, Download } from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/store/authStore";
import { logger } from "@/lib/logger";
import { API_URL as API } from "@/lib/config";

const MODEL_OPTIONS = [
  { value: "qwen3:8b-gpu", label: "Qwen3 8B (GPU)" },
  { value: "dolphin-llama3:8b-gpu", label: "Dolphin Llama3 8B (GPU)" },
  { value: "llava:13b-gpu", label: "LLaVA 13B Vision (GPU)" },
];

const POLARITY_PRESETS = [
  { value: "balanced", label: "Balanced (3 masc, 3 fem, 2 unified)" },
  { value: "masculine-lean", label: "Masculine-lean (4 masc, 2 fem, 1 unified)" },
  { value: "feminine-lean", label: "Feminine-lean (2 masc, 4 fem, 1 unified)" },
  { value: "rebis-heavy", label: "Rebis-heavy (2 masc, 2 fem, 4 unified)" },
];

export default function SettingsPage() {
  const { user, updateProfile } = useAuthStore();
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [profileSaving, setProfileSaving] = useState(false);
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [defaultModel, setDefaultModel] = useState("qwen3:8b-gpu");
  const [polarityPreset, setPolarityPreset] = useState("balanced");
  const [maxRounds, setMaxRounds] = useState(4);
  const [consensusThreshold, setConsensusThreshold] = useState(0.85);
  const [preferDesktopApp, setPreferDesktopApp] = useState(false);
  const [desktopDownloading, setDesktopDownloading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  // API Key management
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [showNewKey, setShowNewKey] = useState<string | null>(null);
  const [revokingKey, setRevokingKey] = useState<string | null>(null);

  interface ApiKeyItem {
    id: string;
    name: string;
    key_prefix: string;
    last_used_at: string | null;
    is_active: boolean;
    created_at: string;
  }

  useEffect(() => {
    if (user?.display_name) setDisplayName(user.display_name);
  }, [user?.display_name]);

  useEffect(() => {
    const saved = localStorage.getItem("syzygy-settings");
    if (saved) {
      try {
        const s = JSON.parse(saved);
        setOllamaUrl(s.ollamaUrl || ollamaUrl);
        setDefaultModel(s.defaultModel || defaultModel);
        setPolarityPreset(s.polarityPreset || polarityPreset);
        setMaxRounds(s.maxRounds || maxRounds);
        setConsensusThreshold(s.consensusThreshold ?? consensusThreshold);
        setPreferDesktopApp(s.preferDesktopApp ?? false);
      } catch { console.debug("Failed to load saved settings"); }
    }
  }, []);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    setApiKeysLoading(true);
    try {
      const headers = useAuthStore.getState().getAuthHeaders();
      const res = await fetch(`${API}/api/auth/api-keys`, { headers });
      if (res.ok) {
        const data = await res.json();
        setApiKeys(data.keys || []);
      }
    } catch {
      // Silent fail — backend may not support API keys yet
    } finally {
      setApiKeysLoading(false);
    }
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;
    setCreatingKey(true);
    try {
      const headers = useAuthStore.getState().getAuthHeaders();
      const res = await fetch(`${API}/api/auth/api-keys`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ name: newKeyName.trim() }),
      });
      if (!res.ok) throw new Error("Failed to create API key");
      const key = await res.json();
      setShowNewKey(key.raw_key);
      setNewKeyName("");
      toast.success("API key created");
      await fetchApiKeys();
    } catch {
      toast.error("Failed to create API key");
    } finally {
      setCreatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    setRevokingKey(keyId);
    try {
      const headers = useAuthStore.getState().getAuthHeaders();
      const res = await fetch(`${API}/api/auth/api-keys/${keyId}`, {
        method: "DELETE",
        headers,
      });
      if (!res.ok) throw new Error("Failed to revoke API key");
      toast.success("API key revoked");
      await fetchApiKeys();
    } catch {
      toast.error("Failed to revoke API key");
    } finally {
      setRevokingKey(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard?.writeText(text);
    toast.success("Copied to clipboard");
  };

  const [verifying, setVerifying] = useState(false);

  const handleSaveProfile = async () => {
    setProfileSaving(true);
    try {
      await updateProfile({ display_name: displayName });
      toast.success("Profile updated");
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleVerifyEmail = async () => {
    if (!user) return;
    setVerifying(true);
    try {
      const res = await fetch(`${API}/api/auth/send-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email }),
      });
      const data = await res.json();
      if (data.verification_token) {
        navigator.clipboard?.writeText(data.verification_token);
        toast.success("Verification link copied to clipboard (dev mode)");
      } else {
        toast.success("Verification email sent (if configured)");
      }
    } catch {
      toast.error("Failed to send verification");
    } finally {
      setVerifying(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const settings = { ollamaUrl, defaultModel, polarityPreset, maxRounds, consensusThreshold, preferDesktopApp };
      localStorage.setItem("syzygy-settings", JSON.stringify(settings));
      const headers = useAuthStore.getState().getAuthHeaders();
      await fetch(`${API}/api/auth/me/settings`, {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ settings }),
      });
      logger.info("Settings saved", settings, "Settings");
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      logger.error("Failed to save settings", err, "Settings");
      toast.error("Failed to save settings");
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`${API}/health`);
      if (res.ok) {
        setTestResult("✅ Backend connection successful");
      } else {
        setTestResult("❌ Backend returned an error");
      }
    } catch (err) {
      logger.error("Backend connection test failed", err, "Settings");
      setTestResult("❌ Cannot reach backend");
    } finally {
      setTesting(false);
    }
  };

  const SettingRow = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-4 py-3">
      <label className="text-sm text-syzygy-grey">{label}</label>
      <div className="w-64">{children}</div>
    </div>
  );

  return (
    <div className="space-y-6 max-w-2xl animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-8 w-auto brightness-110"
            width={32} height={32}
          />
          <div>
            <h1 className="syzygy-title text-2xl font-bold tracking-wider">Settings</h1>
            <p className="mt-0.5 text-xs text-syzygy-grey/60">Configure models, polarity preferences, and theme</p>
          </div>
        </div>
        <Button variant="gold" size="sm" onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Save className="mr-1 h-4 w-4" />}
          {saved ? "Saved!" : "Save Settings"}
        </Button>
      </div>

      {user && (
        <>
          <div className="space-y-3">
            <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
              <User className="h-4 w-4" />
              Profile
            </h2>

            {user && !user.verified_at && (
              <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                  <p className="text-xs text-amber-400/80">Email not verified</p>
                </div>
                <Button variant="ghost" size="sm" onClick={handleVerifyEmail} disabled={verifying}>
                  {verifying ? <Loader2 className="h-3 w-3 animate-spin" /> : "Verify"}
                </Button>
              </div>
            )}

            <SettingRow label="Display Name">
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-1.5 text-sm text-foreground outline-none focus:border-syzygy-gold/50"
              />
            </SettingRow>

            <SettingRow label="Email">
              <span className="text-sm text-syzygy-grey/80">{user.email}</span>
            </SettingRow>

            <div className="flex justify-end">
              <Button variant="gold" size="sm" onClick={handleSaveProfile} disabled={profileSaving}>
                {profileSaving ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Save className="mr-1 h-4 w-4" />}
                Save Profile
              </Button>
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
              <Shield className="h-4 w-4" />
              Subscription
            </h2>

            <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-4 py-3 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-syzygy-grey">Tier</span>
                <span className="text-sm font-medium text-syzygy-gold uppercase tracking-wider">
                  {user.subscription_tier}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-syzygy-grey">Messages Used</span>
                <span className="text-sm text-foreground">
                  {user.message_count} / {user.monthly_message_limit}
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-syzygy-surface-border overflow-hidden">
                <div
                  className="h-full rounded-full bg-syzygy-gold transition-all"
                  style={{ width: `${Math.min((user.message_count / user.monthly_message_limit) * 100, 100)}%` }}
                />
              </div>
              {user.trial_ends_at && (
                <div className="flex items-center justify-between pt-2 border-t border-syzygy-surface-border">
                  <span className="flex items-center gap-1 text-sm text-syzygy-grey">
                    <Calendar className="h-3 w-3" />
                    Trial ends
                  </span>
                  <span className="text-sm text-foreground">
                    {new Date(user.trial_ends_at).toLocaleDateString()}
                  </span>
                </div>
              )}
              {user.subscription_tier === "free" ? (
                <Button
                  variant="gold"
                  size="sm"
                  className="w-full"
                  onClick={() => window.location.href = "/cloud"}
                >
                  Upgrade Plan
                </Button>
              ) : (
                <Button
                  variant="occult"
                  size="sm"
                  className="w-full gap-2"
                  onClick={async () => {
                    try {
                      const headers = useAuthStore.getState().getAuthHeaders();
                      const res = await fetch(
                        `${API}/api/payments/customer-portal`,
                        { method: "POST", headers },
                      );
                      if (res.ok) {
                        const data = await res.json();
                        window.location.href = data.url;
                      } else {
                        toast.error("Manage subscription unavailable");
                      }
                    } catch {
                      toast.error("Failed to open billing portal");
                    }
                  }}
                >
                  <ExternalLink className="h-3 w-3" />
                  Manage Subscription
                </Button>
              )}
            </div>
          </div>
        </>
      )}

      {/* ─── API Keys ──────────────────────────────────── */}
      <div className="space-y-3">
        <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
          <Key className="h-4 w-4" />
          API Keys
        </h2>
        <p className="text-xs text-syzygy-grey/50 mb-3">
          Use API keys for programmatic access. Store them securely — they won&apos;t be shown again.
        </p>

        {showNewKey && (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 mb-1.5">
                  <CheckCircle2 className="h-3 w-3" />
                  New API Key created — copy it now
                </p>
                <code className="block break-all rounded bg-syzygy-obsidian px-3 py-2 text-xs font-mono text-syzygy-gold-light select-all">
                  {showNewKey}
                </code>
              </div>
              <div className="flex gap-1.5 shrink-0">
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(showNewKey)}>
                  <Copy className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowNewKey(null)}>
                  <XCircle className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name (e.g. CI pipeline)"
            className="flex-1 rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-2 text-sm text-foreground placeholder-syzygy-grey/40 outline-none focus:border-syzygy-gold/50"
            onKeyDown={(e) => e.key === "Enter" && handleCreateKey()}
          />
          <Button variant="gold" size="sm" onClick={handleCreateKey} disabled={creatingKey || !newKeyName.trim()}>
            {creatingKey ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
            Create
          </Button>
        </div>

        {apiKeysLoading ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-4 w-4 animate-spin text-syzygy-grey/50" />
          </div>
        ) : apiKeys.length === 0 ? (
          <p className="text-xs text-syzygy-grey/40 py-4 text-center">No API keys yet</p>
        ) : (
          <div className="space-y-2">
            {apiKeys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 px-4 py-2.5"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-foreground">{key.name}</span>
                    {!key.is_active && (
                      <span className="text-[10px] uppercase tracking-wider text-red-400/70">Revoked</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <code className="text-xs font-mono text-syzygy-grey/50">{key.key_prefix}...</code>
                    {key.last_used_at ? (
                      <span className="text-[10px] text-syzygy-grey/40">
                        Last used {new Date(key.last_used_at).toLocaleDateString()}
                      </span>
                    ) : (
                      <span className="text-[10px] text-syzygy-grey/30">Never used</span>
                    )}
                  </div>
                </div>
                {key.is_active && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRevokeKey(key.id)}
                    disabled={revokingKey === key.id}
                    className="text-red-400/60 hover:text-red-400"
                  >
                    {revokingKey === key.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── Desktop Application ─────────────────────── */}
      <div className="space-y-3">
        <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
          <Monitor className="h-4 w-4" />
          Desktop Application
        </h2>
        <p className="text-xs text-syzygy-grey/50 mb-3">
          Download the Syzygy desktop client for a native experience with offline support and system tray integration.
        </p>

        <SettingRow label="Prefer desktop application">
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              className={`relative h-5 w-9 rounded-full transition-colors ${preferDesktopApp ? "bg-syzygy-gold" : "bg-syzygy-surface-border"}`}
              onClick={() => setPreferDesktopApp(!preferDesktopApp)}
            >
              <div
                className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-syzygy-obsidian transition-transform ${preferDesktopApp ? "translate-x-4" : "translate-x-0"}`}
              />
            </div>
            <span className="text-sm text-syzygy-grey">
              {preferDesktopApp ? "Desktop mode preferred" : "Web app preferred"}
            </span>
          </label>
        </SettingRow>

        <div className="flex justify-end">
          <Button
            variant="gold"
            size="sm"
            className="gap-2"
            disabled={desktopDownloading}
            onClick={async () => {
              setDesktopDownloading(true);
              // Placeholder: actual download URL when desktop build is published
              toast.success("Desktop download starting...");
              await new Promise((r) => setTimeout(r, 1000));
              setDesktopDownloading(false);
            }}
          >
            {desktopDownloading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Download for Windows
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
          <SettingsIcon className="h-4 w-4" />
          Connection
        </h2>

        <SettingRow label="Ollama URL">
          <input
            type="text"
            value={ollamaUrl}
            onChange={(e) => setOllamaUrl(e.target.value)}
            className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-1.5 text-sm text-foreground outline-none focus:border-syzygy-gold/50"
          />
        </SettingRow>

        <div className="flex justify-end">
          <Button variant="ghost" size="sm" onClick={handleTestConnection} disabled={testing}>
            {testing ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-1 h-4 w-4" />}
            Test Connection
          </Button>
        </div>

        {testResult && (
          <div className="rounded-lg border border-syzygy-gold/20 bg-syzygy-gold/5 px-4 py-2 text-sm text-syzygy-gold">
            {testResult}
          </div>
        )}

        <h2 className="mt-6 flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
          <SettingsIcon className="h-4 w-4" />
          Agent Defaults
        </h2>

        <SettingRow label="Default Model">
          <select
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-1.5 text-sm text-foreground outline-none focus:border-syzygy-gold/50"
          >
            {MODEL_OPTIONS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </SettingRow>

        <SettingRow label="Polarity Preset">
          <select
            value={polarityPreset}
            onChange={(e) => setPolarityPreset(e.target.value)}
            className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-1.5 text-sm text-foreground outline-none focus:border-syzygy-gold/50"
          >
            {POLARITY_PRESETS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </SettingRow>

        <h2 className="mt-6 flex items-center gap-2 font-alchemical text-lg tracking-wider text-syzygy-gold">
          <SettingsIcon className="h-4 w-4" />
          Consensus
        </h2>

        <SettingRow label="Max Rounds">
          <input
            type="number"
            min={1}
            max={10}
            value={maxRounds}
            onChange={(e) => setMaxRounds(Number(e.target.value))}
            className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-1.5 text-sm text-foreground outline-none focus:border-syzygy-gold/50"
          />
        </SettingRow>

        <SettingRow label="Convergence Threshold">
          <input
            type="number"
            min={0.5}
            max={1}
            step={0.05}
            value={consensusThreshold}
            onChange={(e) => setConsensusThreshold(Number(e.target.value))}
            className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-3 py-1.5 text-sm text-foreground outline-none focus:border-syzygy-gold/50"
          />
        </SettingRow>
      </div>
    </div>
  );
}
