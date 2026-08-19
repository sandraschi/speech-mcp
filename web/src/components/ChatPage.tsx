import {
  Download,
  Eraser,
  Loader2,
  MessageSquare,
  Send,
  Sparkles,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";

import { BACKEND, chatMessage, fetchPersonas, type Persona } from "../api";

const STORAGE_KEY = "speech_chat_history";
const MAX_MSGS = 100;

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  ts: string;
}

const EXAMPLE_PROMPTS = [
  "Summarize the FunASR setup in one paragraph.",
  "How do I enable streaming STT with barge-in?",
  "Explain the voice command bus to fleet-agent.",
  "What does the voice bank do and how do I register a voice?",
  "Give me the quickest way to translate speech to Japanese.",
  "What analytics does the server record, and how do I read them?",
];

function loadHistory(): ChatMsg[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.slice(-MAX_MSGS) : [];
  } catch {
    return [];
  }
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMsg[]>(loadHistory);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personality, setPersonality] = useState("custom");
  const [skill, setSkill] = useState<string | null>(null);
  const [skills, setSkills] = useState<{ name: string; description: string }[]>(
    [],
  );
  const [provider, setProvider] = useState("ollama");
  const [providerOnline, setProviderOnline] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPersonas().then((ps) => {
      if (ps.length > 0) setPersonas(ps);
    });
    fetch(`${BACKEND}/api/skills`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success) setSkills(data.skills ?? []);
      })
      .catch(() => {});
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll on message/busy change, ref access only
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const persist = (next: ChatMsg[]) => {
    const capped = next.slice(-MAX_MSGS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(capped));
    } catch {
      /* storage full - ignore */
    }
    setMessages(capped);
  };

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setInput("");
    setError(null);
    const userMsg: ChatMsg = {
      role: "user",
      content: trimmed,
      ts: new Date().toISOString(),
    };
    const next = [...messages, userMsg];
    persist(next);
    setBusy(true);
    try {
      const res = await chatMessage({
        message: trimmed,
        personality,
        skill,
        provider,
      });
      if (!res.success) {
        setError(res.reply || "Chat request failed");
      } else {
        const assistantMsg: ChatMsg = {
          role: "assistant",
          content: res.reply,
          ts: new Date().toISOString(),
        };
        persist([...next, assistantMsg]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const probeProvider = async () => {
    setProviderOnline(null);
    try {
      const res = await fetch(
        `${BACKEND}/api/v1/local/models?provider=${provider}`,
        { headers: { "Content-Type": "application/json" } },
      );
      const data = await res.json();
      setProviderOnline(Boolean(data.success && data.models?.length > 0));
    } catch {
      setProviderOnline(false);
    }
  };

  // biome-ignore lint/correctness/useExhaustiveDependencies: probe once per provider change
  useEffect(() => {
    probeProvider();
  }, [provider]);

  const exportTxt = () => {
    const body = messages
      .map(
        (m) =>
          `[${m.ts.slice(0, 16).replace("T", " ")}] ${m.role}: ${m.content}`,
      )
      .join("\n\n");
    const blob = new Blob([body], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "speech-chat.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    localStorage.removeItem(STORAGE_KEY);
    setMessages([]);
    setError(null);
  };

  return (
    <div className="space-y-6" data-testid="chat-page">
      <header>
        <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
          Chat
        </h1>
        <p className="text-sm text-white/50 uppercase tracking-widest mt-1">
          Skill-first local LLM chat
        </p>
      </header>

      <div
        className="glass-card p-4 flex flex-wrap items-center gap-4"
        data-testid="chat-controls"
      >
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-accent-purple" />
          <label
            htmlFor="chat-personality"
            className="text-xs font-bold uppercase tracking-wider text-text-secondary"
          >
            Persona
          </label>
          <select
            id="chat-personality"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            data-testid="personality-select"
            className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-1.5 text-sm"
          >
            {personas.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label
            htmlFor="chat-skill"
            className="text-xs font-bold uppercase tracking-wider text-text-secondary"
          >
            Skill
          </label>
          <select
            id="chat-skill"
            value={skill ?? ""}
            onChange={(e) => setSkill(e.target.value || null)}
            className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">None</option>
            {skills.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label
            htmlFor="chat-provider"
            className="text-xs font-bold uppercase tracking-wider text-text-secondary"
          >
            Provider
          </label>
          <select
            id="chat-provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="ollama">Ollama</option>
            <option value="lmstudio">LM Studio</option>
          </select>
          <span
            className={`w-2 h-2 rounded-full ${
              providerOnline === null
                ? "bg-white/20"
                : providerOnline
                  ? "bg-emerald-500"
                  : "bg-rose-500"
            }`}
            title={
              providerOnline === null
                ? "probing"
                : providerOnline
                  ? "online"
                  : "offline"
            }
          />
          <span className="text-xs text-text-secondary">
            {providerOnline === null
              ? "probing…"
              : providerOnline
                ? "online"
                : "offline"}
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={exportTxt}
            disabled={messages.length === 0}
            data-testid="chat-export"
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg disabled:opacity-40"
          >
            <Download size={13} /> Export
          </button>
          <button
            type="button"
            onClick={clearChat}
            disabled={messages.length === 0}
            data-testid="chat-clear"
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg disabled:opacity-40"
          >
            <Eraser size={13} /> Clear
          </button>
        </div>
      </div>

      {error && (
        <div
          className="text-sm text-rose-400 font-bold"
          data-testid="chat-error"
        >
          {error}
        </div>
      )}

      <div
        className="glass-card p-6 min-h-[320px] max-h-[60vh] overflow-y-auto space-y-4"
        data-testid="chat-messages"
      >
        {messages.length === 0 && !busy ? (
          <div className="h-full flex flex-col items-center justify-center text-center py-16 space-y-6">
            <MessageSquare size={40} className="text-white/10" />
            <p className="text-white/40 font-bold uppercase tracking-widest text-sm">
              Start a conversation
            </p>
            <div
              className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full"
              data-testid="example-prompts"
            >
              {EXAMPLE_PROMPTS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => send(p)}
                  className="text-left text-xs text-text-secondary bg-white/[0.03] hover:bg-white/[0.07] border border-white/5 hover:border-accent-purple/30 p-3 rounded-xl transition-all"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.ts}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-accent-purple/20 border border-accent-purple/30 text-white"
                    : "bg-white/[0.04] border border-white/10 text-white/90"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))
        )}
        {busy && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 text-xs text-white/40 px-2">
              <Loader2 size={14} className="animate-spin" /> thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex items-center gap-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything… (skill + persona are injected automatically)"
          data-testid="chat-input"
          className="flex-1 bg-zinc-800 text-zinc-100 border border-zinc-600 focus:border-accent-purple/60 rounded-xl px-4 py-3 text-sm outline-none transition-colors"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          data-testid="chat-send"
          className="flex items-center gap-2 text-sm font-bold text-white bg-accent-purple/80 hover:bg-accent-purple px-4 py-3 rounded-xl disabled:opacity-40 transition-colors"
        >
          {busy ? (
            <Loader2 size={15} className="animate-spin" />
          ) : (
            <Send size={15} />
          )}
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatPage;
