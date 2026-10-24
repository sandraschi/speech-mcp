import {
  Activity,
  Copy,
  HeartPulse,
  Mic,
  MicOff,
  Send,
  Settings2,
  ShieldCheck,
  StopCircle,
  Trash2,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { BACKEND, fetchEviSession } from "../api";
import { useBackend } from "../BackendContext";

interface EviBootstrap {
  success: boolean;
  provider: string;
  acronym: string;
  websocket_url: string;
  local_proxy: string;
  configured: boolean;
  has_key: boolean;
  has_config_id: boolean;
  proxy_status: string;
  status: string;
  next_steps: string[];
}

interface TranscriptLine {
  id: string;
  role: "user" | "model" | "system";
  text: string;
  ts: string;
}

type SessionState = "idle" | "connecting" | "ready" | "error";

const EMOTION_SAMPLES = [
  "anxiety",
  "boredom",
  "triumph",
  "warmth",
  "doubt",
  "excitement",
  "calm",
  "frustration",
];

const DEFAULT_SYSTEM =
  "You are a warm, emotionally attuned conversational companion. Keep replies concise and natural.";

const EviSession: React.FC = () => {
  const { health, error } = useBackend();
  const [bootstrap, setBootstrap] = useState<EviBootstrap | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  // Live session state
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [isMicActive, setIsMicActive] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [interim, setInterim] = useState("");
  const [emotion, setEmotion] = useState<{
    top: string[];
    scores: Record<string, number>;
  } | null>(null);
  const [textInput, setTextInput] = useState("");
  const [configId, setConfigId] = useState("");
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM);
  const [showConfig, setShowConfig] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [modelSpeaking, setModelSpeaking] = useState(false);
  const [sessionInfo, setSessionInfo] = useState<{
    chat_id?: string;
    chat_group_id?: string;
  }>({});

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const scriptNodeRef = useRef<ScriptProcessorNode | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const transcriptEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchEviSession()
      .then((d) => {
        if (!cancelled && d) setBootstrap(d);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  });

  const addLine = useCallback((role: TranscriptLine["role"], text: string) => {
    setTranscript((prev) => [
      ...prev.slice(-200),
      {
        id: `${Date.now()}-${Math.random()}`,
        role,
        text,
        ts: new Date().toLocaleTimeString(),
      },
    ]);
  }, []);

  const resampleAndEncode = useCallback(
    (inputBuffer: Float32Array, inputRate: number): Int16Array => {
      const outputRate = 16000;
      const ratio = inputRate / outputRate;
      const outputLength = Math.ceil(inputBuffer.length / ratio);
      const output = new Int16Array(outputLength);
      for (let i = 0; i < outputLength; i++) {
        const srcIdx = Math.min(Math.floor(i * ratio), inputBuffer.length - 1);
        const s = Math.max(-1, Math.min(1, inputBuffer[srcIdx]));
        output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      return output;
    },
    [],
  );

  const cleanupMic = useCallback(() => {
    scriptNodeRef.current?.disconnect();
    scriptNodeRef.current = null;
    for (const t of micStreamRef.current?.getTracks() ?? []) t.stop();
    micStreamRef.current = null;
  }, []);

  const scheduleWav = useCallback(async (wavBytes: ArrayBuffer) => {
    const ctx = audioCtxRef.current;
    if (!ctx) return;
    if (ctx.state === "suspended") await ctx.resume();
    try {
      const audioBuffer = await ctx.decodeAudioData(wavBytes.slice(0));
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      const startTime = Math.max(ctx.currentTime, nextPlayTimeRef.current);
      source.start(startTime);
      nextPlayTimeRef.current = startTime + audioBuffer.duration;
      setModelSpeaking(true);
      source.onended = () => {
        if (nextPlayTimeRef.current <= ctx.currentTime + 0.05)
          setModelSpeaking(false);
      };
    } catch (e) {
      console.warn("EVI audio decode error:", e);
    }
  }, []);

  const stopSession = useCallback(() => {
    cleanupMic();
    wsRef.current?.close();
    wsRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    nextPlayTimeRef.current = 0;
    setSessionState("idle");
    setIsMicActive(false);
    setModelSpeaking(false);
  }, [cleanupMic]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopSession();
    };
  }, [stopSession]);

  const startSession = useCallback(async () => {
    setErrorMsg("");
    setSessionState("connecting");
    addLine("system", "Connecting to Hume EVI…");

    const token = localStorage.getItem("SPEECH_MCP_AUTH_TOKEN") || "";
    const params = new URLSearchParams({ provider: "hume" });
    if (configId.trim()) params.set("config_id", configId.trim());
    if (systemPrompt.trim()) params.set("system", systemPrompt.trim());
    if (token) params.set("token", token);
    const wsUrl = `${BACKEND.replace(/^http/, "ws")}/ws/stream?${params}`;

    const ctx = new AudioContext({ sampleRate: 48000 });
    audioCtxRef.current = ctx;
    nextPlayTimeRef.current = 0;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.binaryType = "arraybuffer";

    ws.onmessage = async (ev) => {
      if (ev.data instanceof ArrayBuffer) {
        await scheduleWav(ev.data);
        return;
      }
      try {
        const msg = JSON.parse(ev.data as string);
        switch (msg.type) {
          case "session_ready":
            setSessionState("ready");
            addLine(
              "system",
              `EVI session ready${msg.config_id ? ` — config ${msg.config_id}` : ""}`,
            );
            break;
          case "transcript":
            setInterim("");
            addLine(msg.role, msg.text);
            break;
          case "interim":
            setInterim(msg.text);
            break;
          case "emotion":
            setEmotion({ top: msg.top ?? [], scores: msg.scores ?? {} });
            break;
          case "session_info":
            setSessionInfo({
              chat_id: msg.chat_id,
              chat_group_id: msg.chat_group_id,
            });
            break;
          case "interrupted":
            nextPlayTimeRef.current = 0;
            setModelSpeaking(false);
            addLine("system", "[interrupted — you took the floor]");
            break;
          case "turn_complete":
            setModelSpeaking(false);
            break;
          case "error":
            setErrorMsg(msg.message);
            addLine("system", `Error: ${msg.message}`);
            setSessionState("error");
            break;
        }
      } catch (_) {}
    };

    ws.onclose = () => {
      setSessionState("idle");
      setIsMicActive(false);
      setModelSpeaking(false);
      addLine("system", "Session closed.");
      cleanupMic();
    };

    ws.onerror = () => {
      setErrorMsg("WebSocket connection failed");
      setSessionState("error");
    };
  }, [configId, systemPrompt, addLine, scheduleWav, cleanupMic]);

  const startMic = useCallback(async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const ctx = audioCtxRef.current;
    if (!ctx) return;
    if (ctx.state === "suspended") await ctx.resume();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      micStreamRef.current = stream;
      const source = ctx.createMediaStreamSource(stream);
      const processor = ctx.createScriptProcessor(4096, 1, 1);
      scriptNodeRef.current = processor;
      processor.onaudioprocess = (ev) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
          return;
        const input = ev.inputBuffer.getChannelData(0);
        const pcm16 = resampleAndEncode(input, ctx.sampleRate);
        wsRef.current.send(pcm16.buffer);
      };
      source.connect(processor);
      processor.connect(ctx.destination);
      setIsMicActive(true);
    } catch (e) {
      setErrorMsg(
        `Mic access failed: ${e instanceof Error ? e.message : String(e)}`,
      );
    }
  }, [resampleAndEncode]);

  const stopMic = useCallback(() => {
    cleanupMic();
    setIsMicActive(false);
  }, [cleanupMic]);

  const toggleMic = useCallback(() => {
    if (isMicActive) stopMic();
    else startMic();
  }, [isMicActive, startMic, stopMic]);

  const sendText = useCallback(() => {
    if (
      !textInput.trim() ||
      !wsRef.current ||
      wsRef.current.readyState !== WebSocket.OPEN
    )
      return;
    wsRef.current.send(
      JSON.stringify({ type: "text", text: textInput.trim() }),
    );
    addLine("user", textInput.trim());
    setTextInput("");
  }, [textInput, addLine]);

  const copy = useCallback(async (label: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(label);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      setCopied(null);
    }
  }, []);

  const backendOnline = !error && health?.status === "healthy";
  const hasKey = bootstrap?.has_key ?? health?.tokens.hume_api_key ?? false;
  const hasConfig =
    bootstrap?.has_config_id ?? health?.tokens.hume_config_id ?? false;
  const humeAvailable = health?.providers.hume ?? false;
  const configured = bootstrap?.configured ?? (hasKey && hasConfig);
  const isConnected = sessionState === "ready";
  const isConnecting = sessionState === "connecting";

  return (
    <div className="h-full space-y-8 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Hume Voice Chat
          </h1>
          <p className="text-sm text-white/40 font-bold uppercase tracking-widest">
            Empathic Voice Interface — Hume AI realtime conversation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-black uppercase tracking-widest border ${
              isConnected
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : isConnecting
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-400 animate-pulse"
                  : sessionState === "error"
                    ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                    : "bg-white/5 border-white/10 text-white/40"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isConnected
                  ? "bg-emerald-400"
                  : isConnecting
                    ? "bg-amber-400 animate-pulse"
                    : sessionState === "error"
                      ? "bg-rose-400"
                      : "bg-white/20"
              }`}
            />
            {isConnected
              ? "Live"
              : isConnecting
                ? "Connecting"
                : sessionState === "error"
                  ? "Error"
                  : "Idle"}
          </span>
          <button
            type="button"
            onClick={() => setShowConfig(!showConfig)}
            className="p-2 bg-white/5 border border-white/10 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-all"
          >
            <Settings2 size={16} />
          </button>
          <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-full text-xs font-black uppercase tracking-widest text-white/40 flex items-center gap-2">
            <ShieldCheck size={12} />
            Bidirectional — the AI hears you
          </div>
        </div>
      </header>

      {/* What EVI is */}
      <div className="glass-card p-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-white/5 p-3 rounded-xl border border-white/10 text-rose-300">
            <HeartPulse size={20} />
          </div>
          <h2 className="text-xl font-black text-white uppercase tracking-tighter">
            What EVI is
          </h2>
        </div>
        <p className="text-sm text-white/60 leading-relaxed max-w-3xl">
          <span className="text-white font-bold">
            EVI = Empathic Voice Interface
          </span>{" "}
          (Hume AI). Full-duplex conversation that detects 50+ emotional nuances
          in your voice and adapts its own tone in realtime — backchanneling,
          affective dialog, native interrupts. This is not{" "}
          <span className="text-white font-bold">Octave TTS</span>, which is
          batch text-to-speech with emotional prosody. Use EVI for live
          discovery or coaching-style dialog; use Octave (TTS page) or Gemini
          Live (Gemini Voice Chat page) for narration and low-latency duplex.
        </p>
        <div className="flex flex-wrap gap-2 mt-4">
          {EMOTION_SAMPLES.map((e) => (
            <span
              key={e}
              className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-bold text-white/60 uppercase tracking-wider"
            >
              {e}
            </span>
          ))}
        </div>
        {emotion && emotion.top.length > 0 && (
          <div className="mt-4 p-4 rounded-xl bg-rose-500/5 border border-rose-500/20">
            <div className="text-xs font-black text-rose-300 uppercase tracking-widest mb-2">
              Live prosody — top emotions
            </div>
            <div className="flex flex-wrap gap-2">
              {emotion.top.map((e) => (
                <span
                  key={e}
                  className="px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-xs font-bold text-rose-200"
                >
                  {e}{" "}
                  {emotion.scores[e] !== undefined
                    ? emotion.scores[e].toFixed(2)
                    : ""}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {showConfig && (
        <div className="glass-card p-6 space-y-4 border-white/10 animate-in fade-in duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="evi-config"
                className="block text-xs font-black text-white/40 uppercase tracking-widest mb-2"
              >
                Hume config ID (optional — server default otherwise)
              </label>
              <input
                id="evi-config"
                value={configId}
                onChange={(e) => setConfigId(e.target.value)}
                disabled={isConnected || isConnecting}
                placeholder="from evi.hume.ai"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-mono outline-none focus:border-rose-500/40 disabled:opacity-40"
              />
            </div>
            <div>
              <label
                htmlFor="evi-system"
                className="block text-xs font-black text-white/40 uppercase tracking-widest mb-2"
              >
                System prompt / persona
              </label>
              <textarea
                id="evi-system"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                disabled={isConnected || isConnecting}
                rows={2}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-rose-500/40 resize-none disabled:opacity-40"
              />
            </div>
          </div>
          {bootstrap && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <CopyRow
                label="Hume EVI"
                value={bootstrap.websocket_url}
                copied={copied === "evi"}
                onCopy={() => copy("evi", bootstrap.websocket_url)}
              />
              <CopyRow
                label="Local proxy"
                value={bootstrap.local_proxy}
                copied={copied === "proxy"}
                onCopy={() => copy("proxy", bootstrap.local_proxy)}
              />
            </div>
          )}
        </div>
      )}

      {errorMsg && (
        <div className="glass-card p-4 border border-rose-500/30 text-rose-400 text-sm font-bold flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse flex-shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Readiness */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-8">
          <h3 className="text-xs font-black text-white/40 uppercase tracking-widest mb-6">
            Readiness
          </h3>
          <div className="space-y-3">
            <ReadinessRow
              label="Backend"
              ok={backendOnline}
              hint={backendOnline ? "online" : "offline — start backend :10909"}
            />
            <ReadinessRow
              label="HUME_API_KEY"
              ok={hasKey}
              hint={hasKey ? "set" : "missing in .env"}
            />
            <ReadinessRow
              label="HUME_CONFIG_ID"
              ok={hasConfig}
              hint={
                hasConfig
                  ? "set (evi.hume.ai)"
                  : "missing — EVI chat needs it, Octave TTS does not"
              }
            />
            <ReadinessRow
              label="Hume provider"
              ok={humeAvailable}
              hint={
                humeAvailable ? "available" : "unavailable until key is set"
              }
            />
          </div>
          {!configured && (
            <div className="mt-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-sm text-amber-200 leading-relaxed">
              Setup: add <span className="font-mono">HUME_API_KEY</span> +{" "}
              <span className="font-mono">HUME_CONFIG_ID</span> (from
              evi.hume.ai) to <span className="font-mono">.env</span>, restart
              the backend. See{" "}
              <span className="font-mono">docs/providers/hume.md</span>.
            </div>
          )}
        </div>

        <div className="glass-card p-8">
          <h3 className="text-xs font-black text-white/40 uppercase tracking-widest mb-6">
            Session
          </h3>
          {!isConnected && !isConnecting ? (
            <button
              type="button"
              onClick={startSession}
              disabled={!configured}
              className="w-full py-3.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-30 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all shadow-lg shadow-rose-600/20 flex items-center justify-center gap-2"
            >
              <Mic size={15} /> Connect EVI
            </button>
          ) : (
            <button
              type="button"
              onClick={stopSession}
              className="w-full py-3.5 bg-white/10 hover:bg-white/20 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all flex items-center justify-center gap-2"
            >
              <StopCircle size={15} /> Disconnect
            </button>
          )}
          <div className="space-y-2 pt-4 mt-4 border-t border-white/5">
            {[
              { label: "Model", value: "Hume EVI (eLLM)" },
              { label: "In", value: "16kHz PCM Linear16" },
              { label: "Out", value: "48kHz WAV" },
              {
                label: "Chat",
                value: sessionInfo.chat_id
                  ? sessionInfo.chat_id.slice(0, 8)
                  : "—",
              },
            ].map((r) => (
              <div key={r.label} className="flex justify-between text-xs">
                <span className="text-white/30 uppercase tracking-wider font-bold">
                  {r.label}
                </span>
                <span className="text-white/70 font-mono">{r.value}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-white/30 mt-4 leading-relaxed">
            From an MCP client:{" "}
            <code className="font-mono text-white/60">start_evi_session()</code>{" "}
            returns the same WebSocket targets. Web one-click voice is live on
            this page.
          </p>
        </div>
      </div>

      {/* Live transcript + mic */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div
          className="lg:col-span-2 glass-card flex flex-col"
          style={{ height: 480 }}
        >
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-black text-white/40 uppercase tracking-widest">
              <Activity size={13} />
              Transcript
            </div>
            <button
              type="button"
              onClick={() => {
                setTranscript([]);
                setInterim("");
              }}
              className="p-1.5 text-white/20 hover:text-white/60 transition-colors"
            >
              <Trash2 size={13} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-3 font-mono text-sm">
            {transcript.length === 0 && !interim ? (
              <div className="h-full flex items-center justify-center text-white/10 uppercase tracking-widest text-xs font-black">
                Connect to begin
              </div>
            ) : (
              <>
                {transcript.map((line) => (
                  <div
                    key={line.id}
                    className="flex gap-3 animate-in fade-in duration-200"
                  >
                    <span className="text-white/20 text-xs w-14 shrink-0 pt-0.5">
                      {line.ts.slice(0, 5)}
                    </span>
                    <span
                      className={`text-xs font-black uppercase tracking-wider shrink-0 w-12 pt-0.5 ${
                        line.role === "user"
                          ? "text-rose-300"
                          : line.role === "model"
                            ? "text-emerald-400"
                            : "text-white/20"
                      }`}
                    >
                      {line.role === "user"
                        ? "YOU"
                        : line.role === "model"
                          ? "EVI"
                          : "SYS"}
                    </span>
                    <span
                      className={`flex-1 leading-relaxed ${
                        line.role === "system"
                          ? "text-white/30 italic"
                          : "text-white/85"
                      }`}
                    >
                      {line.text}
                    </span>
                  </div>
                ))}
                {interim && (
                  <div className="flex gap-3 opacity-60">
                    <span className="text-white/20 text-xs w-14 shrink-0 pt-0.5">
                      …
                    </span>
                    <span className="text-xs font-black uppercase tracking-wider shrink-0 w-12 pt-0.5 text-rose-300/60">
                      YOU
                    </span>
                    <span className="flex-1 leading-relaxed text-white/50 italic">
                      {interim}
                    </span>
                  </div>
                )}
              </>
            )}
            <div ref={transcriptEndRef} />
          </div>
          <div className="px-6 py-4 border-t border-white/5">
            <div className="flex gap-3">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendText()}
                placeholder={isConnected ? "Type a message…" : "Connect first"}
                disabled={!isConnected}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-rose-500/40 disabled:opacity-30 transition-all"
              />
              <button
                type="button"
                onClick={sendText}
                disabled={!isConnected || !textInput.trim()}
                className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-30 text-white rounded-xl transition-all"
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="glass-card p-8 flex flex-col items-center gap-6">
            <div className="relative">
              <button
                type="button"
                onClick={toggleMic}
                disabled={!isConnected}
                className={`w-28 h-28 rounded-full flex items-center justify-center transition-all duration-300 disabled:opacity-30 ${
                  isMicActive
                    ? "bg-rose-500 shadow-[0_0_40px_rgba(239,68,68,0.4)] scale-110"
                    : "bg-white/10 hover:bg-white/20"
                }`}
              >
                {isMicActive ? (
                  <MicOff size={40} className="text-white" />
                ) : (
                  <Mic size={40} className="text-white" />
                )}
              </button>
              {isMicActive && (
                <div className="absolute inset-0 rounded-full border-2 border-rose-400/40 animate-ping" />
              )}
              {modelSpeaking && (
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                  {[0, 1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="w-1 bg-emerald-400 rounded-full animate-bounce"
                      style={{
                        height: 8 + i * 4,
                        animationDelay: `${i * 0.1}s`,
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
            <div className="text-center">
              <p className="text-sm font-black text-white uppercase tracking-widest">
                {isMicActive
                  ? "Mic Active"
                  : isConnected
                    ? "Mic Off"
                    : "Not Connected"}
              </p>
              <p className="text-xs text-white/30 mt-1 uppercase tracking-wider">
                {modelSpeaking
                  ? "EVI speaking…"
                  : isMicActive
                    ? "Listening…"
                    : "Click to toggle"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ReadinessRow = ({
  label,
  ok,
  hint,
}: {
  label: string;
  ok: boolean;
  hint: string;
}) => (
  <div className="flex justify-between items-center bg-white/[0.02] p-4 rounded-xl border border-white/5">
    <span className="text-sm font-bold text-white">{label}</span>
    <span className="text-right">
      <span
        className={`text-xs font-black uppercase ${ok ? "text-emerald-400" : "text-white/30"}`}
      >
        {ok ? "Ready" : "—"}
      </span>
      <span className="block text-xs text-white/40 font-mono mt-1">{hint}</span>
    </span>
  </div>
);

const CopyRow = ({
  label,
  value,
  copied,
  onCopy,
}: {
  label: string;
  value: string;
  copied: boolean;
  onCopy: () => void;
}) => (
  <div className="flex justify-between items-center bg-white/[0.02] p-4 rounded-xl border border-white/5 gap-4">
    <div className="min-w-0">
      <div className="text-xs font-black text-white/40 uppercase tracking-widest">
        {label}
      </div>
      <div className="text-sm font-mono text-white truncate">{value}</div>
    </div>
    <button
      type="button"
      onClick={onCopy}
      className="shrink-0 p-2 bg-white/5 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-all"
      title={`Copy ${label}`}
    >
      <Copy size={14} />
      <span className="sr-only">{copied ? "Copied" : `Copy ${label}`}</span>
    </button>
  </div>
);

export default EviSession;
