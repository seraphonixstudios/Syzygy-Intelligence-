"use client";

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Switch from "@radix-ui/react-switch";
import { X, Loader2, Sparkles } from "lucide-react";
import { ArchetypePicker } from "./ArchetypePicker";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

import { API_URL as API } from "@/lib/config";

interface CreateAgentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

const ARCHETYPE_DISPLAY_NAMES: Record<string, string> = {
  hero: "Hero",
  sage: "Sage",
  ruler: "Ruler",
  magician: "Magician",
  explorer: "Explorer",
  great_mother: "Great Mother",
  lover: "Lover",
  innocent: "Innocent",
  creator: "Creator",
  anima: "Anima",
  self: "Self",
  hermes: "Hermes",
  trickster: "Trickster",
};

export function CreateAgentModal({ open, onOpenChange, onCreated }: CreateAgentModalProps) {
  const [archetype, setArchetype] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [model, setModel] = useState("qwen3:8b-gpu");
  const [shadowActive, setShadowActive] = useState(false);
  const [creating, setCreating] = useState(false);

  const handleArchetypeSelect = (id: string) => {
    setArchetype(id);
    if (!name || name === ARCHETYPE_DISPLAY_NAMES[archetype || ""]) {
      setName(ARCHETYPE_DISPLAY_NAMES[id] || id);
    }
  };

  const handleCreate = async () => {
    if (!archetype) {
      toast.error("Please select an archetype");
      return;
    }
    setCreating(true);
    try {
      const res = await fetch(`${API}/api/agents/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          archetype,
          name: name || undefined,
          model: model || undefined,
          shadow_active: shadowActive || undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Failed to create agent" }));
        throw new Error(err.detail || "Failed to create agent");
      }
      toast.success("Agent created");
      onCreated();
      onOpenChange(false);
      setArchetype(null);
      setName("");
      setModel("qwen3:8b-gpu");
      setShadowActive(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create agent");
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm data-[state=open]:animate-fade-in" />
        <Dialog.Content className="z-50 max-h-[85dvh] w-[90vw] max-w-4xl overflow-y-auto rounded-xl border border-syzygy-surface-border bg-syzygy-deep p-6 shadow-2xl data-[state=open]:animate-scale-in">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-semibold text-foreground">
              Create Agent
            </Dialog.Title>
            <Dialog.Close className="rounded p-1 text-syzygy-grey/40 hover:text-foreground transition-colors">
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>

          <div className="space-y-6">
            <div>
              <h4 className="text-xs font-medium text-syzygy-grey/60 mb-3 uppercase tracking-wider">
                Select Archetype
              </h4>
              <ArchetypePicker selected={archetype} onSelect={handleArchetypeSelect} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-syzygy-grey/60">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Agent name"
                  className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow px-3 py-2 text-sm text-foreground placeholder:text-syzygy-grey/40 focus:border-syzygy-gold/50 focus:outline-none focus:ring-1 focus:ring-syzygy-gold/30"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-syzygy-grey/60">Model</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="qwen3:8b-gpu"
                  className="w-full rounded-lg border border-syzygy-surface-border bg-syzygy-shadow px-3 py-2 text-sm text-foreground placeholder:text-syzygy-grey/40 focus:border-syzygy-gold/50 focus:outline-none focus:ring-1 focus:ring-syzygy-gold/30"
                />
              </div>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-foreground">Shadow Active</p>
                <p className="text-xs text-syzygy-grey/60">Enable shadow integration for this agent</p>
              </div>
              <Switch.Root
                checked={shadowActive}
                onCheckedChange={setShadowActive}
                className={cn(
                  "relative h-6 w-11 rounded-full border transition-colors",
                  shadowActive
                    ? "border-destructive/50 bg-destructive/30"
                    : "border-syzygy-surface-border bg-syzygy-shadow"
                )}
              >
                <Switch.Thumb
                  className={cn(
                    "block h-5 w-5 rounded-full transition-transform duration-200",
                    shadowActive ? "translate-x-5 bg-destructive" : "translate-x-0.5 bg-syzygy-grey"
                  )}
                />
              </Switch.Root>
            </div>

            <div className="flex justify-end gap-3">
              <Dialog.Close asChild>
                <Button variant="outline" size="sm">Cancel</Button>
              </Dialog.Close>
              <Button
                variant="gold"
                size="sm"
                onClick={handleCreate}
                disabled={!archetype || creating}
              >
                {creating ? (
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-1 h-4 w-4" />
                )}
                {creating ? "Creating..." : "Create Agent"}
              </Button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
