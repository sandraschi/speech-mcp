import { Download, Mic, MonitorUp, Square } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { BACKEND } from "../api";

interface TranscriptLine {
  turnId: number | string;
  speaker: string;
  text: string;
}

function download(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// Nearest-neighbor float32 -> 16kHz int16 PCM (same approach as VoiceChat.tsx's
// resampleAndEncode; Muse accepts PCM_16KHZ directly).
function resampleTo16kInt16(
  input: Float32Array,
  inputRate: number,
): Int16Array {
  const outputRate = 16000;
  const ratio = inputRate / outputRate;
  const outputLength = Math.ceil(input.length / ratio);
  const output = new Int16Array(outputLength);
  for (let i = 0; i < outputLength; i++) {
    const srcIdx = Math.min(Math.floor(i * ratio), input.length - 1);
    const s = Math.max(-1, Math.min(1, input[srcIdx]));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output;
}

type SessionState = "idle" | "connecting" | "live" | "error";

export default function LiveTranscribePage() {
  const [state, setState] = useState<SessionState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [includeSystemAudio, setIncludeSystemAudio] = useState(true);
  const [lines, setLines] = useState<TranscriptLine[]>([]);
  const [partial, setPartial] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const displayStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const cleanupAudio = useCallback(() => {
    processorRef.current?.disconnect();
    processorRef.current = null;
    micStreamRef.current?.getTracks().forEach((t) => {
      t.stop();
    });
    micStreamRef.current = null;
    displayStreamRef.current?.getTracks().forEach((t) => {
      t.stop();
    });
    displayStreamRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
  }, []);

  const stopSession = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_turn" }));
    }
    wsRef.current?.close();
    wsRef.current = null;
    cleanupAudio();
    setState("idle");
    setPartial("");
  }, [cleanupAudio]);

  const startSession = useCallback(async () => {
    setError(null);
    setLines([]);
    setPartial("");
    setState("connecting");

    let micStream: MediaStream;
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      setError(
        `Mic access failed: ${e instanceof Error ? e.message : String(e)}`,
      );
      setState("error");
      return;
    }
    micStreamRef.current = micStream;

    let displayStream: MediaStream | null = null;
    if (includeSystemAudio) {
      try {
        // Chrome requires a video constraint to offer "share system/tab audio";
        // the video track is discarded immediately below.
        displayStream = await navigator.mediaDevices.getDisplayMedia({
          audio: true,
          video: true,
        });
        for (const track of displayStream.getVideoTracks()) track.stop();
        if (displayStream.getAudioTracks().length === 0) {
          setError(
            'No audio track in the shared source - re-share with "Share system audio" (or a tab that has audio) checked.',
          );
          displayStream = null;
        }
      } catch (e) {
        // User cancelled the picker - fall back to mic-only rather than aborting.
        console.warn("Display audio capture skipped:", e);
      }
    }
    displayStreamRef.current = displayStream;

    const token = localStorage.getItem("SPEECH_MCP_AUTH_TOKEN") || "";
    const params = new URLSearchParams({
      provider: "muse",
      ...(token ? { token } : {}),
    });
    const ws = new WebSocket(
      `${BACKEND.replace(/^http/, "ws")}/ws/stream?${params}`,
    );
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data as string);
        switch (event.type) {
          case "session":
            setState("live");
            break;
          case "transcript":
            if (!event.final) setPartial(event.transcript || "");
            break;
          case "speechComplete":
            setPartial("");
            setLines((prev) => [
              ...prev,
              {
                turnId: event.turnId ?? prev.length,
                speaker: event.speaker ?? "?",
                text: (event.transcript || "").trim(),
              },
            ]);
            break;
          case "error":
            setError(event.message || "Unknown streaming error");
            setState("error");
            break;
        }
      } catch {
        // ignore non-JSON frames
      }
    };
    ws.onerror = () => {
      setError("WebSocket connection failed");
      setState("error");
    };
    ws.onclose = () => {
      cleanupAudio();
      setState((s) => (s === "error" ? s : "idle"));
    };

    const ctx = new AudioContext();
    audioCtxRef.current = ctx;
    const mixBus = ctx.createGain();
    ctx.createMediaStreamSource(micStream).connect(mixBus);
    if (displayStream)
      ctx.createMediaStreamSource(displayStream).connect(mixBus);

    const processor = ctx.createScriptProcessor(4096, 1, 1);
    processorRef.current = processor;
    processor.onaudioprocess = (ev) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) return;
      const pcm16 = resampleTo16kInt16(
        ev.inputBuffer.getChannelData(0),
        ctx.sampleRate,
      );
      wsRef.current.send(pcm16.buffer);
    };
    mixBus.connect(processor);
    // ScriptProcessorNode only fires while connected to a destination; route
    // through a silent gain so the mixed audio is never played back out loud.
    const silent = ctx.createGain();
    silent.gain.value = 0;
    processor.connect(silent);
    silent.connect(ctx.destination);
  }, [includeSystemAudio, cleanupAudio]);

  const saveTranscript = useCallback(() => {
    const text = lines
      .map((l) => `[Speaker ${l.speaker}] ${l.text}`)
      .join("\n");
    download(`live-transcript-${Date.now()}.txt`, text);
  }, [lines]);

  const busy = state === "connecting" || state === "live";

  return (
    <div className="space-y-6" data-testid="live-transcribe-page">
      <header>
        <h1 className="text-2xl font-black mb-1">Live Transcribe</h1>
        <p className="text-sm text-text-secondary">
          Diarized real-time transcription (Meta Muse Voice Transcribe) from
          your mic plus, optionally, the audio of a shared tab or your whole
          screen - useful for transcribing a call in progress. Speaker labels
          stay consistent for the whole session, unlike batch-uploading
          recordings in chunks.
        </p>
        <p className="text-xs text-amber-400 mt-2">
          This does not trigger your call app's own recording indicator. Make
          sure other participants know you're transcribing.
        </p>
      </header>

      <section className="glass-card p-6">
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-text-secondary">
            <input
              type="checkbox"
              checked={includeSystemAudio}
              onChange={(e) => setIncludeSystemAudio(e.target.checked)}
              disabled={busy}
            />
            <MonitorUp size={15} /> Include shared tab/system audio
          </label>
          {state === "idle" || state === "error" ? (
            <button
              type="button"
              onClick={startSession}
              data-testid="live-start"
              className="inline-flex items-center gap-2 text-sm font-bold text-white bg-accent-purple/80 hover:bg-accent-purple px-4 py-2 rounded-lg transition-colors"
            >
              <Mic size={16} /> Start
            </button>
          ) : (
            <button
              type="button"
              onClick={stopSession}
              data-testid="live-stop"
              className="inline-flex items-center gap-2 text-sm font-bold text-white bg-rose-500/80 hover:bg-rose-500 px-4 py-2 rounded-lg transition-colors"
            >
              <Square size={16} /> Stop
            </button>
          )}
          {lines.length > 0 && (
            <button
              type="button"
              onClick={saveTranscript}
              className="inline-flex items-center gap-2 text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg"
            >
              <Download size={13} /> Save transcript
            </button>
          )}
          <span className="text-xs font-mono text-text-secondary uppercase">
            {state}
          </span>
        </div>
        {error && (
          <p className="mt-3 text-sm text-rose-400" data-testid="live-error">
            {error}
          </p>
        )}
      </section>

      <section
        className="glass-card p-6 space-y-2"
        data-testid="live-transcript"
      >
        {lines.length === 0 && !partial && (
          <p className="text-sm text-text-secondary">
            No speech yet. Click Start and speak.
          </p>
        )}
        {lines.map((l) => (
          <div key={`${l.turnId}`} className="text-sm flex gap-3">
            <span className="font-mono text-accent-purple shrink-0">
              [{l.speaker}]
            </span>
            <span className="text-white">{l.text}</span>
          </div>
        ))}
        {partial && (
          <div className="text-sm flex gap-3 opacity-50 italic">
            <span className="font-mono shrink-0">[...]</span>
            <span>{partial}</span>
          </div>
        )}
      </section>
    </div>
  );
}
