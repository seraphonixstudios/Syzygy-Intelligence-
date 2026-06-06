"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Settings as SettingsIcon, Save, RefreshCw, Loader2 } from "lucide-react";
import { logger } from "@/lib/logger";
import { toast } from "sonner";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

const MODEL_OPTIONS = [
  { value: "qwen3.5:8b", label: "Qwen3.5 8B" },
  { value: "qwen3:8b-gpu", label: "Qwen3 8B (GPU)" },
  { value: "deepseek-r1:7b", label: "DeepSeek R1 7B" },
  { value: "dolphin-llama3:8b", label: "Dolphin Llama3 8B" },
  { value: "dolphin-llama3:8b-gpu", label: "Dolphin Llama3 8B (GPU)" },
  { value: "llava:13b-gpu", label: "LLaVA 13B Vision (GPU)" },
  { value: "qwen-coder:7b", label: "Qwen Coder 7B" },
  { value: "llama3.2:3b", label: "Llama 3.2 3B" },
];

const POLARITY_PRESETS = [
  { value: "balanced", label: "Balanced (3 masc, 3 fem, 2 unified)" },
  { value: "masculine-lean", label: "Masculine-lean (4 masc, 2 fem, 1 unified)" },
  { value: "feminine-lean", label: "Feminine-lean (2 masc, 4 fem, 1 unified)" },
  { value: "rebis-heavy", label: "Rebis-heavy (2 masc, 2 fem, 4 unified)" },
];

export default function SettingsPage() {
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [defaultModel, setDefaultModel] = useState("qwen3.5:8b");
  const [polarityPreset, setPolarityPreset] = useState("balanced");
  const [maxRounds, setMaxRounds] = useState(4);
  const [consensusThreshold, setConsensusThreshold] = useState(0.85);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

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
      } catch {}
    }
  }, []);

  const handleSave = () => {
    setSaving(true);
    try {
      const settings = { ollamaUrl, defaultModel, polarityPreset, maxRounds, consensusThreshold };
      localStorage.setItem("syzygy-settings", JSON.stringify(settings));
      logger.info("Settings saved", settings, "Settings");
      setTimeout(() => { setSaving(false); setSaved(true); setTimeout(() => setSaved(false), 2000); }, 500);
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
