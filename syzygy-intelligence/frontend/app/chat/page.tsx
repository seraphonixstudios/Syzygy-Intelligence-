"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send, MessageSquare, Loader2, Bot, User } from "lucide-react";

const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Greetings, seeker. I am Syzygy Intelligence, the Rebis of aligned opposites. How may I assist you in your Great Work?" },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);

    try {
      const res = await fetch(`${API}/api/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          model: "syzygy",
        }),
      });
      const data = await res.json();
      const reply = data.response || "No response.";
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Consensus engine ready. (Ollama must be running for live responses.)" },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col space-y-4">
      <div className="flex items-center gap-3 shrink-0">
        <img
          src="/branding/pagetop.logo.png"
          alt="Syzygy"
          className="h-8 w-auto brightness-110"
        />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Chat</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Natural language interface to Syzygy Intelligence</p>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-4 min-h-0">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
            {msg.role === "assistant" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-syzygy-gold/20">
                <Bot className="h-4 w-4 text-syzygy-gold" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-syzygy-gold/20 text-syzygy-gold-light"
                  : "bg-syzygy-obsidian/50 text-syzygy-grey"
              }`}
            >
              {msg.content}
            </div>
            {msg.role === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-syzygy-gold/20">
                <User className="h-4 w-4 text-syzygy-gold" />
              </div>
            )}
          </div>
        ))}
        {sending && (
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

      <form onSubmit={handleSend} className="flex items-center gap-2 rounded-2xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/40 outline-none"
          disabled={sending}
        />
        <Button type="submit" disabled={!input.trim() || sending} variant="gold" size="sm" className="shrink-0 gap-1">
          <Send className="h-3.5 w-3.5" />
          Send
        </Button>
      </form>
    </div>
  );
}
