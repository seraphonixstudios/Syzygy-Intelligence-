"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { VoiceButton } from "@/components/VoiceButton";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { FileLinkUpload, UploadedFile, LinkMeta } from "@/components/FileLinkUpload";
import { Send, Loader2, Bot, User, Brain, Layers, ChevronDown, ChevronRight, StopCircle, Database, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { useSSE } from "@/hooks/useSSE";
import { API_URL as API } from "@/lib/config";

const SUGGESTIONS = [
  "What is Syzygy?",
  "Explain polarity fusion",
  "Compare consensus models",
  "How does the Rebis archetype work?",
  "Explain the individuation process",
  "Help me configure my agent team",
];

interface Message {
  id: string;  // Unique ID to prevent key collisions
  role: "user" | "assistant";
  content: string;
  multiModel?: Record<string, string>;
  modelName?: string;
}

interface ModelInfo {
  configured: Record<string, string>;
  available: string[];
  all_models: string[];
}

function MultiModelDisplay({ responses }: { responses: Record<string, string> }) {
  const modelKeys = Object.keys(responses);
  const [activeModel, setActiveModel] = useState(modelKeys[0] || "");
  const [expanded, setExpanded] = useState(false);

  if (modelKeys.length === 0) return <span>No responses</span>;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1">
        {modelKeys.map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setActiveModel(m)}
            className={`rounded px-2 py-0.5 text-[10px] font-mono transition-colors ${
              activeModel === m
                ? "bg-syzygy-gold/30 text-syzygy-gold-light"
                : "bg-syzygy-surface-border/20 text-syzygy-grey/50 hover:text-syzygy-grey"
            }`}
          >
            {m.includes(":") ? m.split(":")[0] : m.slice(0, 12)}
          </button>
        ))}
      </div>
      <div className="text-xs leading-relaxed text-syzygy-grey whitespace-pre-wrap">
        {responses[activeModel]?.startsWith("[Error") ? (
          <span className="text-red-400/70 italic">{responses[activeModel]}</span>
        ) : (
          responses[activeModel]
        )}
      </div>
      {modelKeys.length > 1 && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-[10px] text-syzygy-gold/50 hover:text-syzygy-gold transition-colors"
        >
          {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          {expanded ? "Hide all" : `Show all ${modelKeys.length} responses`}
        </button>
      )}
      {expanded && (
        <div className="space-y-3 border-t border-syzygy-surface-border/30 pt-2 mt-1">
          {modelKeys.map((m) => (
            <div key={m} className="space-y-0.5">
              <div className="text-[10px] font-mono text-syzygy-gold/60">{m}</div>
              <div className="text-xs text-syzygy-grey/80 whitespace-pre-wrap pl-2 border-l border-syzygy-surface-border/30">
                {responses[m]?.startsWith("[Error") ? (
                  <span className="text-red-400/70 italic">{responses[m]}</span>
                ) : (
                  responses[m]
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const MODEL_OPTIONS = [
  { value: "syzygy", label: "Auto (Syzygy Consensus)" },
  { value: "__all__", label: "All Models" },
];

// Error boundary component to catch rendering errors
class ChatErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error("Chat page error", error, "Chat");
    console.error("Chat Error Boundary:", errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
          <div className="space-y-3 text-center">
            <h2 className="text-lg font-semibold text-red-400">Something went wrong</h2>
            <p className="text-sm text-syzygy-grey/70">{this.state.error?.message || "An unexpected error occurred"}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-lg bg-syzygy-gold/20 px-4 py-2 text-sm text-syzygy-gold hover:bg-syzygy-gold/30 transition-colors"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial_msg",
      role: "assistant",
      content: "Greetings, seeker. I am Syzygy Intelligence, the Rebis of aligned opposites. How may I assist you in your Great Work?",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [reasoning, setReasoning] = useState<{ agent: string; thought: string; confidence?: number; model?: string }[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [attachedLinks, setAttachedLinks] = useState<LinkMeta[]>([]);
  const [selectedModel, setSelectedModel] = useState("qwen3:8b-gpu");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [useRag, setUseRag] = useState(false);
  const [ragActive, setRagActive] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { isStreaming, stream: sseStream, cancel: cancelStream } = useSSE();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // Fetch available models on mount with proper error handling
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API}/api/chat/models`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = (await response.json()) as ModelInfo;
        setAvailableModels(data.available);
        logger.info("Loaded available models", data.available, "Chat");
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        logger.warn("Could not fetch model list — using defaults", errorMsg, "Chat");
        toast.error("Could not load models");
        setAvailableModels(["qwen3:8b-gpu", "dolphin-llama3:8b-gpu", "llava:13b-gpu"]);
      }
    };

    fetchModels();
  }, []);

  // Helper function to generate unique message IDs
  const generateMessageId = (): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  // Validate model selection
  const isValidModel = (model: string): boolean => {
    return (
      model === "syzygy" ||
      model === "__all__" ||
      availableModels.includes(model)
    );
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    // Validate model selection
    if (!isValidModel(selectedModel)) {
      toast.error("Invalid model selected");
      logger.error("Invalid model", selectedModel, "Chat");
      return;
    }

    const userMsg = input.trim();
    setInput("");

    // Add user message with unique ID
    const userMsgId = generateMessageId();
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: userMsg },
    ]);
    setSending(true);
    setStreamingContent("");

    try {
      if (selectedModel === "__all__") {
        // Multi-model query
        const models = availableModels.length > 0 ? availableModels : ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu", "llava:13b-gpu"];
        const res = await fetch(`${API}/api/chat/multi-model`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userMsg, models }),
        });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        const responses: Record<string, string> = data.responses || {};
        setMessages((prev) => [
          ...prev,
          {
            id: generateMessageId(),
            role: "assistant",
            content: Object.values(responses).find((v) => v && !v.startsWith("[Error")) || "No valid response.",
            multiModel: responses,
            modelName: "All Models",
          },
        ]);
        setReasoning([{ agent: "Multi-Model", thought: `Queried ${models.length} models in parallel.`, model: models.join(", ") }]);
      } else if (selectedModel !== "syzygy" && selectedModel !== "__all__") {
        // SSE streaming for direct model queries with optional RAG
        setStreamingContent("");
        setRagActive(false);

        await sseStream(
          `${API}/api/chat/stream`,
          { message: userMsg, model: selectedModel, use_rag: useRag },
          {
            onRagContext: () => setRagActive(true),
            onToken: (token) => {
              setStreamingContent((prev) => prev + token);
            },
            onDone: (full) => {
              setMessages((prev) => [
                ...prev,
                {
                  id: generateMessageId(),
                  role: "assistant",
                  content: full,
                  modelName: selectedModel,
                },
              ]);
              setStreamingContent("");
              setReasoning([
                {
                  agent: selectedModel,
                  thought: "Streaming complete. Response generated.",
                  model: selectedModel,
                },
              ]);
            },
            onError: (errMsg) => {
              toast.error(errMsg);
              setMessages((prev) => [
                ...prev,
                {
                  id: generateMessageId(),
                  role: "assistant",
                  content: `Error: ${errMsg}`,
                  modelName: selectedModel,
                },
              ]);
              setStreamingContent("");
            },
          }
        );
      } else {
        // syzygy consensus
        const res = await fetch(`${API}/api/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMsg,
            model: selectedModel,
            use_rag: useRag,
            files: uploadedFiles,
            links: attachedLinks,
          }),
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          const detail = errData.detail || {};
          throw new Error(detail.message || `HTTP ${res.status}`);
        }
        const data = await res.json();
        const reply = data.response || "No response.";
        if (data.rag_context_used) setRagActive(true);
        if (data.reasoning) {
          setReasoning(data.reasoning);
        } else {
          setReasoning([
            {
              agent: "Syzygy",
              thought: "Consensus complete. Response generated.",
              model: selectedModel,
            },
          ]);
        }
        setMessages((prev) => [
          ...prev,
          {
            id: generateMessageId(),
            role: "assistant",
            content: reply,
            modelName: selectedModel,
          },
        ]);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      logger.error("Chat send failed", err, "Chat");
      toast.error("Backend unavailable — check that Ollama and the backend are running");
      setMessages((prev) => [
        ...prev,
        {
          id: generateMessageId(),
          role: "assistant",
          content: "Error: Could not reach the backend. Ensure Docker containers are running.",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <ChatErrorBoundary>
      <div className="flex min-h-0 flex-1 flex-col space-y-4">
        <div className="flex items-center gap-3 shrink-0">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-8 w-auto brightness-110"
            width={32}
            height={32}
          />
          <div>
            <h1 className="syzygy-title text-2xl font-bold tracking-wider">Chat</h1>
            <p className="mt-0.5 text-xs text-syzygy-grey/60">Natural language interface to Syzygy Intelligence</p>
          </div>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-4 min-h-0">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-syzygy-gold/20">
                  <Bot className="h-4 w-4 text-syzygy-gold" />
                </div>
              )}
              <div className="max-w-[80%] space-y-1">
                {msg.modelName && msg.modelName !== "All Models" && (
                  <div className="text-xs text-syzygy-gold/60 font-mono">{msg.modelName}</div>
                )}
                <div
                  className={`rounded-2xl px-4 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-syzygy-gold/20 text-syzygy-gold-light"
                      : "bg-syzygy-obsidian/50 text-syzygy-grey"
                  }`}
                >
                  {msg.multiModel ? (
                    <MultiModelDisplay responses={msg.multiModel} />
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
              {msg.role === "user" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-syzygy-gold/20">
                  <User className="h-4 w-4 text-syzygy-gold" />
                </div>
              )}
            </div>
          ))}
          {streamingContent && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-syzygy-gold/20">
                <Bot className="h-4 w-4 text-syzygy-gold" />
              </div>
              <div className="max-w-[80%] space-y-1">
                {selectedModel !== "syzygy" && (
                  <div className="text-xs text-syzygy-gold/60 font-mono">{selectedModel}</div>
                )}
                <div className="rounded-2xl bg-syzygy-obsidian/50 px-4 py-2 text-sm text-syzygy-grey">
                  {streamingContent}
                  <span className="inline-block w-0.5 h-4 ml-0.5 bg-syzygy-gold/60 animate-pulse align-middle" />
                </div>
              </div>
            </div>
          )}
          {sending && !streamingContent && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-syzygy-gold/20">
                <Loader2 className="h-4 w-4 animate-spin text-syzygy-gold" />
              </div>
              <div className="max-w-[80%] rounded-2xl bg-syzygy-obsidian/30 px-4 py-2 text-sm text-syzygy-grey/60">
                Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length === 1 && (
          <div className="animate-fade-in-up space-y-4 py-4">
            <div className="grid grid-cols-2 gap-3">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setInput(s)}
                  className="group flex items-center justify-between rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/20 px-4 py-3 text-left text-xs text-syzygy-grey/60 transition-all duration-200 hover:border-syzygy-gold/30 hover:bg-syzygy-gold/5 hover:text-syzygy-grey-light"
                >
                  <span className="leading-relaxed">{s}</span>
                  <ArrowRight className="h-3.5 w-3.5 shrink-0 text-syzygy-grey/30 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-syzygy-gold/60" />
                </button>
              ))}
            </div>
          </div>
        )}

        {reasoning.length > 0 && (
          <ReasoningPanel steps={reasoning} loading={sending} title="Agent Reasoning" />
        )}

        <form onSubmit={handleSend} className="space-y-2">
          <div className="flex items-center gap-2 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
            {/* RAG toggle */}
            <button
              type="button"
              onClick={() => setUseRag(!useRag)}
              className={`flex items-center gap-1 rounded-lg border px-2 py-1.5 text-xs transition-colors ${
                useRag
                  ? "border-syzygy-gold/50 bg-syzygy-gold/10 text-syzygy-gold"
                  : "border-syzygy-surface-border text-syzygy-grey/50 hover:border-syzygy-gold/30 hover:text-syzygy-grey"
              }`}
              title="Use Knowledge Base for context"
            >
              <Database className="h-3 w-3" />
              KB
            </button>
            {ragActive && useRag && (
              <span className="text-[10px] text-syzygy-gold/50">RAG active</span>
            )}
            {/* Model selector */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowModelPicker(!showModelPicker)}
                className="flex items-center gap-1 rounded-lg border border-syzygy-surface-border px-2 py-1.5 text-xs text-syzygy-grey/70 hover:border-syzygy-gold/40 hover:text-syzygy-gold transition-colors"
              >
                <Layers className="h-3 w-3" />
                {selectedModel === "syzygy" ? "Auto" : selectedModel === "__all__" ? "All Models" : selectedModel}
              </button>
              {showModelPicker && (
                <div className="absolute bottom-full left-0 mb-2 z-50 w-56 rounded-xl border border-syzygy-surface-border bg-syzygy-obsidian p-2 shadow-2xl">
                  {MODEL_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => {
                        setSelectedModel(opt.value);
                        setShowModelPicker(false);
                      }}
                      className={`w-full rounded-lg px-3 py-2 text-left text-xs transition-colors ${
                        selectedModel === opt.value
                          ? "bg-syzygy-gold/20 text-syzygy-gold"
                          : "text-syzygy-grey/70 hover:bg-syzygy-surface-border/30 hover:text-foreground"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                  <div className="my-1 border-t border-syzygy-surface-border" />
                  <div className="px-3 py-1 text-[10px] text-syzygy-grey/50 uppercase tracking-wider">Models</div>
                  {availableModels.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => {
                        setSelectedModel(m);
                        setShowModelPicker(false);
                      }}
                      className={`w-full rounded-lg px-3 py-2 text-left text-xs transition-colors ${
                        selectedModel === m
                          ? "bg-syzygy-gold/20 text-syzygy-gold"
                          : "text-syzygy-grey/70 hover:bg-syzygy-surface-border/30 hover:text-foreground"
                      }`}
                    >
                      <span className="font-mono">{m}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
              disabled={sending}
            />
            <VoiceButton onTranscript={(t) => setInput((prev) => prev + t)} />
            {isStreaming ? (
              <Button type="button" onClick={cancelStream} variant="destructive" size="sm" className="shrink-0 gap-1">
                <StopCircle className="h-3.5 w-3.5" />
                Stop
              </Button>
            ) : (
              <Button type="submit" disabled={!input.trim() || sending} variant="gold" size="sm" className="shrink-0 gap-1">
                <Send className="h-3.5 w-3.5" />
                Send
              </Button>
            )}
          </div>
          <FileLinkUpload
            files={uploadedFiles}
            links={attachedLinks}
            onChange={(f, l) => {
              setUploadedFiles(f);
              setAttachedLinks(l);
            }}
            disabled={sending}
          />
        </form>
      </div>
    </ChatErrorBoundary>
  );
}
