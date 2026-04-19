/**
 * VoiceChat — Real-time full-duplex voice conversation via Gemini Live API.
 *
 * Audio pipeline:
 *   Mic → ScriptProcessor (resample to 16kHz PCM) → WebSocket → backend
 *   WebSocket (WAV chunks) → AudioContext scheduler → speaker
 *
 * Controls:
 *   - Hold-to-talk OR toggle mic on/off
 *   - Text injection (type a message while voice is active)
 *   - System prompt / persona config
 *   - Voice selector (Gemini prebuilt voices)
 *   - Transcript log (both sides)
 */
import {
  Activity,
  Mic,
  MicOff,
  Send,
  Settings2,
  StopCircle,
  Trash2,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { BACKEND } from "../api";

const GEMINI_LIVE_VOICES = [
  "Aoede",
  "Charon",
  "Fenrir",
  "Kore",
  "Orion",
  "Puck",
  "Leda",
  "Orus",
  "Zephyr",
];

const DEFAULT_SYSTEM =
  "You are a helpful, conversational AI assistant. Be concise and natural.";

interface TranscriptLine {
  id: string;
  role: "user" | "model" | "system";
  text: string;
  ts: string;
}

type SessionState = "idle" | "connecting" | "ready" | "error";

const VoiceChat: React.FC = () => {
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [isMicActive, setIsMicActive] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [textInput, setTextInput] = useState("");
  const [voice, setVoice] = useState("Kore");
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM);
  const [showConfig, setShowConfig] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [modelSpeaking, setModelSpeaking] = useState(false);

  // Refs — audio infra
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const scriptNodeRef = useRef<ScriptProcessorNode | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const transcriptEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

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

  // ── Resample float32 → 16kHz int16 PCM ──────────────────────────────────
  const resampleAndEncode = useCallback(
    (inputBuffer: Float32Array, inputRate: number): Int16Array => {
      const outputRate = 16000;
      const ratio = inputRate / outputRate;
      const outputLength = Math.ceil(inputBuffer.length / ratio);
      const output = new Int16Array(outputLength);
      for (let i = 0; i < outputLength; i++) {
        const srcIdx = Math.min(Math.floor(i * ratio), inputBuffer.length - 1);
        // Clamp and convert float32 → int16
        const s = Math.max(-1, Math.min(1, inputBuffer[srcIdx]));
        output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      return output;
    },
    [],
  );

  // ── Mic utility ──────────────────────────────────────────────────────────
  const cleanupMic = useCallback(() => {
    scriptNodeRef.current?.disconnect();
    scriptNodeRef.current = null;
    micStreamRef.current?.getTracks().forEach((t) => {
      t.stop();
    });
    micStreamRef.current = null;
  }, []);

  // ── Schedule WAV chunk for playback ────────────────────────────────────
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
        if (nextPlayTimeRef.current <= ctx.currentTime + 0.05) {
          setModelSpeaking(false);
        }
      };
    } catch (e) {
      console.warn("Audio decode error:", e);
    }
  }, []);

  // ── Start session ────────────────────────────────────────────────────────
  const startSession = useCallback(async () => {
    setErrorMsg("");
    setSessionState("connecting");
    addLine("system", "Connecting to Gemini Live…");

    const token = localStorage.getItem("SPEECH_MCP_AUTH_TOKEN") || "";
    const params = new URLSearchParams({
      provider: "gemini_live",
      voice,
      system: systemPrompt,
      ...(token ? { token } : {}),
    });
    const wsUrl = `${BACKEND.replace(/^http/, "ws")}/ws/stream?${params}`;

    const ctx = new AudioContext({ sampleRate: 48000 });
    audioCtxRef.current = ctx;
    nextPlayTimeRef.current = 0;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      // session_ready comes from backend — wait for it
    };

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
            addLine("system", `Session ready — ${msg.model} / ${msg.voice}`);
            break;
          case "transcript":
            addLine(msg.role, msg.text);
            break;
          case "interrupted":
            // Flush scheduled audio
            nextPlayTimeRef.current = 0;
            setModelSpeaking(false);
            addLine("system", "[interrupted]");
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
  }, [voice, systemPrompt, addLine, scheduleWav, cleanupMic]);

  // ── Stop session ─────────────────────────────────────────────────────────
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

  // ── Mic on/off ────────────────────────────────────────────────────────────

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
      // ScriptProcessor gives us raw PCM — deprecated but universally supported
      // without needing AudioWorklet files
      const bufferSize = 4096;
      const processor = ctx.createScriptProcessor(bufferSize, 1, 1);
      scriptNodeRef.current = processor;

      processor.onaudioprocess = (ev) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
          return;
        const input = ev.inputBuffer.getChannelData(0);
        const pcm16 = resampleAndEncode(input, ctx.sampleRate);
        wsRef.current.send(pcm16.buffer);
      };

      source.connect(processor);
      processor.connect(ctx.destination); // needed to keep processor running
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
    // Signal end of user audio turn
    wsRef.current?.send(JSON.stringify({ type: "end_turn" }));
  }, [cleanupMic]);

  const toggleMic = useCallback(() => {
    if (isMicActive) {
      stopMic();
    } else {
      startMic();
    }
  }, [isMicActive, startMic, stopMic]);

  // ── Send text ─────────────────────────────────────────────────────────────
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

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopSession();
    };
  }, [stopSession]);

  const isConnected = sessionState === "ready";
  const isConnecting = sessionState === "connecting";

  return (
    <div className="h-full space-y-6 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Voice Chat
          </h1>
          <p className="text-sm font-bold uppercase tracking-widest text-slate-400">
            Gemini Live · Full-Duplex · Real-Time
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
        </div>
      </header>

      {/* Config panel */}
      {showConfig && (
        <div className="glass-card p-6 space-y-4 border-white/10 animate-in fade-in duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="voice-select"
                className="block text-xs font-black text-white/40 uppercase tracking-widest mb-2"
              >
                Voice
              </label>
              <select
                id="voice-select"
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                disabled={isConnected || isConnecting}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-bold outline-none focus:border-violet-500/40 disabled:opacity-40"
              >
                {GEMINI_LIVE_VOICES.map((v) => (
                  <option key={v} value={v} className="bg-slate-900">
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                htmlFor="system-prompt"
                className="block text-xs font-black text-white/40 uppercase tracking-widest mb-2"
              >
                System Prompt / Persona
              </label>
              <textarea
                id="system-prompt"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                disabled={isConnected || isConnecting}
                rows={2}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-violet-500/40 resize-none disabled:opacity-40"
              />
            </div>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="glass-card p-4 border border-rose-500/30 text-rose-400 text-sm font-bold flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse flex-shrink-0" />
          {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Transcript */}
        <div
          className="lg:col-span-2 glass-card flex flex-col"
          style={{ height: 480 }}
        >
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-black text-white/40 uppercase tracking-widest">
              <Activity size={13} className="text-violet-400" />
              Transcript
            </div>
            <button
              type="button"
              onClick={() => setTranscript([])}
              className="p-1.5 text-white/20 hover:text-white/60 transition-colors"
            >
              <Trash2 size={13} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-3 font-mono text-sm">
            {transcript.length === 0 ? (
              <div className="h-full flex items-center justify-center text-white/10 uppercase tracking-widest text-xs font-black">
                Start a session to begin
              </div>
            ) : (
              transcript.map((line) => (
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
                        ? "text-violet-400"
                        : line.role === "model"
                          ? "text-emerald-400"
                          : "text-white/20"
                    }`}
                  >
                    {line.role === "user"
                      ? "YOU"
                      : line.role === "model"
                        ? "AI"
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
              ))
            )}
            <div ref={transcriptEndRef} />
          </div>

          {/* Text input */}
          <div className="px-6 py-4 border-t border-white/5">
            <div className="flex gap-3">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendText()}
                placeholder={
                  isConnected ? "Type a message…" : "Start session first"
                }
                disabled={!isConnected}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm outline-none focus:border-violet-500/40 disabled:opacity-30 transition-all"
              />
              <button
                type="button"
                onClick={sendText}
                disabled={!isConnected || !textInput.trim()}
                className="px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-30 text-white rounded-xl transition-all"
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="space-y-4">
          {/* Big mic button */}
          <div className="glass-card p-8 flex flex-col items-center gap-6">
            <div className="relative">
              <button
                type="button"
                onClick={toggleMic}
                disabled={!isConnected}
                className={`w-28 h-28 rounded-full flex items-center justify-center transition-all duration-300 disabled:opacity-30 ${
                  isMicActive
                    ? "bg-rose-500 shadow-[0_0_40px_rgba(239,68,68,0.4)] scale-110"
                    : "bg-violet-600 hover:bg-violet-500 shadow-[0_0_20px_rgba(167,139,250,0.2)]"
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
                  ? "Model speaking…"
                  : isMicActive
                    ? "Listening…"
                    : "Click to toggle"}
              </p>
            </div>
          </div>

          {/* Session controls */}
          <div className="glass-card p-6 space-y-3">
            {!isConnected && !isConnecting ? (
              <button
                type="button"
                onClick={startSession}
                className="w-full py-3.5 bg-violet-600 hover:bg-violet-500 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all shadow-lg shadow-violet-600/20 flex items-center justify-center gap-2"
              >
                <Mic size={15} /> Start Session
              </button>
            ) : (
              <button
                type="button"
                onClick={stopSession}
                className="w-full py-3.5 bg-rose-600 hover:bg-rose-500 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all flex items-center justify-center gap-2"
              >
                <StopCircle size={15} /> End Session
              </button>
            )}

            {/* Session info */}
            <div className="space-y-2 pt-2 border-t border-white/5">
              {[
                { label: "Model", value: "gemini-3.1-flash-live" },
                { label: "Voice", value: voice },
                { label: "In", value: "16kHz PCM" },
                { label: "Out", value: "24kHz WAV" },
              ].map((r) => (
                <div key={r.label} className="flex justify-between text-xs">
                  <span className="text-white/30 uppercase tracking-wider font-bold">
                    {r.label}
                  </span>
                  <span className="text-white/70 font-mono">{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Robot note */}
          <div className="glass-card p-5 border-violet-500/20 bg-violet-500/5">
            <p className="text-xs font-black text-violet-400 uppercase tracking-widest mb-2">
              🤖 Yahboom / Robot Bridge
            </p>
            <p className="text-xs text-white/40 leading-relaxed">
              Connect via the yahboom-mcp bridge: route robot STT → this session
              as text injection, and forward model audio back to the robot
              speaker.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceChat;
