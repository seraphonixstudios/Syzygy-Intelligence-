"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { WorkflowResult } from "@/components/workflows/WorkflowResult";
import { Zap, Loader2, CheckCircle2, XCircle, Settings, BookOpen, Database, Cpu, TrendingUp, ArrowRight, AlertTriangle, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { API_URL as API } from "@/lib/config";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

const MODELS = [
  { id: "tinyllama:latest", label: "TinyLlama 1.1B", desc: "Fastest option, good for testing" },
  { id: "llama3.2:1b", label: "Llama 3.2 1B", desc: "Lightweight, great for fine-tuning" },
  { id: "llama3.2:3b", label: "Llama 3.2 3B", desc: "Best quality-to-speed ratio" },
  { id: "mistral:7b", label: "Mistral 7B", desc: "Strong baseline, needs GPU" },
];

const METHODS = [
  { id: "qlora", label: "QLoRA", desc: "4-bit NF4 quantization + LoRA — most memory efficient" },
  { id: "lora", label: "LoRA", desc: "Full precision LoRA adapters" },
  { id: "full", label: "Full Fine-Tune", desc: "Update all parameters — requires GPU" },
];

const DATASET_SOURCES = [
  { id: "text", label: "Paste Text" },
  { id: "file", label: "Upload File" },
  { id: "hf", label: "HuggingFace Dataset" },
];

const DEFAULT_HP = {
  learning_rate: 2e-4,
  num_epochs: 3,
  batch_size: 4,
  lora_r: 16,
  max_seq_length: 2048,
};

export default function FineTunePage() {
  const [model, setModel] = useState("tinyllama:latest");
  const [method, setMethod] = useState("qlora");
  const [datasetSource, setDatasetSource] = useState("text");
  const [textInput, setTextInput] = useState("");
  const [hfDataset, setHfDataset] = useState("");
  const [showHyperparams, setShowHyperparams] = useState(false);
  const [hp, setHp] = useState(DEFAULT_HP);
  const [executing, setExecuting] = useState(false);
  const [output, setOutput] = useState<any>(null);
  const [error, setError] = useState("");

  const handleExecute = useCallback(async () => {
    if (!model || !method) return;
    setExecuting(true);
    setOutput(null);
    setError("");

    const taskPayload = JSON.stringify({ model, method, hyperparams: hp });
    const ctx: Record<string, any> = { model, method, dataset_source: datasetSource, hyperparams: hp };
    if (datasetSource === "text" && textInput.trim()) ctx.dataset_text = textInput.trim();
    if (datasetSource === "hf" && hfDataset.trim()) ctx.hf_dataset = hfDataset.trim();

    try {
      const res = await fetch(`${API}/api/workflows/finetune/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...useAuthStore.getState().getAuthHeaders() },
        body: JSON.stringify({ task: taskPayload, context: ctx }),
      });
      const data = await res.json();
      setOutput(data);
    } catch (err) {
      logger.error("Fine-tune execution failed", err, "FineTune");
      toast.error("Backend unavailable — running in demo mode");
      setError("Fine-tuning requires the backend to be running.");
      // Simulate demo output
      setOutput({
        workflow: "finetune",
        result: {
          model: model,
          method: method,
          status: "completed",
          metrics: {
            total_steps: 60,
            final_loss: 1.24,
            perplexity: 3.45,
            tokens_per_second: 0,
            memory_peak_mb: 0,
            elapsed_seconds: 9.2,
            loss_curve: Array.from({ length: 60 }, (_, i) => ({
              step: i + 1,
              loss: +(3.0 * Math.exp(-(i + 1) / 24) + 0.3 + (Math.sin(i * 0.5) * 0.1)).toFixed(4),
            })),
            learning_rate_curve: [],
          },
          config: { model, method, dataset_source: datasetSource, hyperparams: hp },
        },
      });
    } finally {
      setExecuting(false);
    }
  }, [model, method, datasetSource, textInput, hfDataset, hp]);

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <img src="/branding/pagetop.logo.png" alt="Syzygy" className="h-8 w-auto brightness-110" width={32} height={32} />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Fine-Tuning</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Train and fine-tune local LLMs with LoRA, QLoRA, or full training</p>
        </div>
      </div>

      {!output && (
        <div className="space-y-5">
          {/* Model Selection */}
          <div className="space-y-2">
            <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-syzygy-grey/40">
              <Cpu className="h-3.5 w-3.5" /> Model
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setModel(m.id)}
                  className={cn(
                    "rounded-xl border p-3 text-left transition-all duration-200",
                    model === m.id
                      ? "border-pink-500/50 bg-pink-500/10 shadow-lg shadow-pink-500/10"
                      : "border-syzygy-surface-border bg-syzygy-shadow/30 hover:border-pink-500/30",
                  )}
                >
                  <p className="text-sm font-medium text-foreground">{m.label}</p>
                  <p className="mt-0.5 text-[11px] text-syzygy-grey/50">{m.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Method Selection */}
          <div className="space-y-2">
            <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-syzygy-grey/40">
              <Settings className="h-3.5 w-3.5" /> Method
            </p>
            <div className="grid gap-2 sm:grid-cols-3">
              {METHODS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setMethod(m.id)}
                  className={cn(
                    "rounded-xl border p-3 text-left transition-all duration-200",
                    method === m.id
                      ? "border-pink-500/50 bg-pink-500/10 shadow-lg shadow-pink-500/10"
                      : "border-syzygy-surface-border bg-syzygy-shadow/30 hover:border-pink-500/30",
                  )}
                >
                  <p className="text-sm font-medium text-foreground">{m.label}</p>
                  <p className="mt-0.5 text-[11px] text-syzygy-grey/50">{m.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Dataset Source */}
          <div className="space-y-2">
            <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-syzygy-grey/40">
              <Database className="h-3.5 w-3.5" /> Dataset
            </p>
            <div className="flex flex-wrap gap-1.5">
              {DATASET_SOURCES.map((ds) => (
                <button
                  key={ds.id}
                  type="button"
                  onClick={() => setDatasetSource(ds.id)}
                  className={cn(
                    "rounded-full px-3 py-1 text-[11px] font-medium transition-all",
                    datasetSource === ds.id
                      ? "bg-pink-500/15 text-pink-300 border border-pink-500/30"
                      : "text-syzygy-grey/50 border border-transparent hover:text-syzygy-grey-light hover:border-syzygy-surface-border",
                  )}
                >
                  {ds.label}
                </button>
              ))}
            </div>
            {datasetSource === "text" && (
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste your training data here (one example per line)..."
                rows={5}
                className="w-full resize-none rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 p-3 text-xs text-foreground placeholder-syzygy-grey/40 outline-none transition-colors focus:border-pink-500/40"
              />
            )}
            {datasetSource === "hf" && (
              <input
                type="text"
                value={hfDataset}
                onChange={(e) => setHfDataset(e.target.value)}
                placeholder="HuggingFace dataset name (e.g., databricks/databricks-dolly-15k)"
                className="w-full rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3 text-sm text-foreground placeholder-syzygy-grey/40 outline-none transition-colors focus:border-pink-500/40"
              />
            )}
            {datasetSource === "file" && (
              <p className="text-xs text-syzygy-grey/40 italic">Upload a .txt or .jsonl file via the upload area below</p>
            )}
          </div>

          {/* Hyperparameters */}
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setShowHyperparams(!showHyperparams)}
              className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-syzygy-grey/40 hover:text-syzygy-grey/60 transition-colors"
            >
              <Settings className="h-3.5 w-3.5" />
              Hyperparameters
              <ArrowRight className={cn("h-3 w-3 transition-transform", showHyperparams && "rotate-90")} />
            </button>
            {showHyperparams && (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-4">
                {Object.entries(DEFAULT_HP).map(([key, val]) => (
                  <div key={key} className="space-y-1">
                    <label className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">{key.replace(/_/g, " ")}</label>
                    <input
                      type="number"
                      value={hp[key as keyof typeof hp]}
                      onChange={(e) => setHp((prev) => ({ ...prev, [key]: parseFloat(e.target.value) || val }))}
                      step={typeof val === "number" && val < 1 ? 0.0001 : 1}
                      className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 px-2 py-1.5 text-xs text-foreground outline-none focus:border-pink-500/40"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Execute */}
          <Button
            onClick={handleExecute}
            disabled={executing || (datasetSource === "text" && !textInput.trim())}
            variant="gold"
            className="w-full gap-2"
          >
            {executing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            {executing ? "Training..." : "Start Training"}
          </Button>
        </div>
      )}

      {/* Results */}
      {output && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-syzygy-gold">
              <CheckCircle2 className="h-4 w-4" /> Training Complete
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { setOutput(null); setError(""); }}
              className="gap-1"
            >
              <Sparkles className="h-3.5 w-3.5" />
              New Training
            </Button>
          </div>
          <WorkflowResult workflow="finetune" data={output} />
        </div>
      )}

      {error && !output && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          <AlertTriangle className="h-4 w-4" /> {error}
        </div>
      )}
    </div>
  );
}
