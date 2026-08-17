import { Activity, Volume2, XCircle } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";

interface StreamPlaybackProps {
  streamUrl: string | null;
  provider: "gemini" | "hume" | "elevenlabs" | "windows";
  text?: string;
  playKey?: number; // increment to force re-play same URL
  onDone?: () => void;
}

/**
 * SOTA Stream Playback with Real-time Chunking and Interrupt Support.
 */
export const StreamPlayback: React.FC<StreamPlaybackProps> = ({
  streamUrl,
  provider,
  text,
  playKey = 0,
  onDone,
}) => {
  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const nextStartTimeRef = useRef<number>(0);
  const isPlayingRef = useRef<boolean>(false);

  const [status, setStatus] = useState<
    "idle" | "connecting" | "streaming" | "playing" | "error"
  >("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const interrupt = () => {
    if (socketRef.current) {
      socketRef.current.send(JSON.stringify({ type: "interrupt" }));
      socketRef.current.close();
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
    }
    setStatus("idle");
    if (onDone) onDone();
  };

  // biome-ignore lint/correctness/useExhaustiveDependencies: playKey and status must trigger re-evaluation
  useEffect(() => {
    if (!streamUrl) return;

    // Cleanup previous
    socketRef.current?.close();
    audioContextRef.current?.close().catch(() => {});

    let isMounted = true;
    setStatus("connecting");
    setErrorMsg("");
    nextStartTimeRef.current = 0;
    isPlayingRef.current = true;

    const AudioContextClass =
      (window as unknown as { AudioContext: typeof AudioContext })
        .AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    const audioCtx = new AudioContextClass();
    audioContextRef.current = audioCtx;

    const socket = new WebSocket(streamUrl);
    socketRef.current = socket;
    socket.binaryType = "arraybuffer";

    socket.onopen = () => {
      if (!isMounted) return;
      setStatus("streaming");

      // Ensure audio context is actually running (browser security)
      if (audioCtx.state === "suspended") {
        audioCtx.resume();
      }

      // Standard TTS request payload for the Gateway
      if (text) {
        socket.send(JSON.stringify({ type: "tts", text }));
      }
    };

    socket.onmessage = async (event: MessageEvent) => {
      if (!isMounted || !isPlayingRef.current) return;

      // Handle metadata messages (like interrupts from server)
      if (typeof event.data === "string") {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "interrupted") {
            setStatus("idle");
            return;
          }
        } catch (_e) {}
        return;
      }

      // High-fidelity chunked playback
      if (event.data instanceof ArrayBuffer && event.data.byteLength > 0) {
        try {
          const audioBuffer = await audioCtx.decodeAudioData(event.data);
          const source = audioCtx.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioCtx.destination);

          // Schedule next chunk at the end of the last one
          const startTime = Math.max(
            audioCtx.currentTime,
            nextStartTimeRef.current,
          );
          source.start(startTime);
          nextStartTimeRef.current = startTime + audioBuffer.duration;

          if (status !== "playing") setStatus("playing");
        } catch (e) {
          console.error("Audio chunk decode error:", e);
        }
      }
    };

    socket.onclose = () => {
      if (!isMounted) return;
      // Wait a bit for the last scheduled buffer to play
      setTimeout(() => {
        if (isMounted) {
          setStatus("idle");
          if (onDone) onDone();
        }
      }, 500);
    };

    socket.onerror = (e) => {
      console.error("WebSocket error:", e);
      if (isMounted) {
        setErrorMsg("Stream connection failed");
        setStatus("error");
      }
    };

    return () => {
      isMounted = false;
      isPlayingRef.current = false;
      socketRef.current?.close();
      audioContextRef.current?.close().catch(() => {});
    };
  }, [streamUrl, text, onDone, status, playKey]);

  if (status === "idle") return null;

  return (
    <div className="glass-card p-5 mt-4 animate-in fade-in zoom-in-95 duration-500 border border-white/10 bg-slate-900/60 backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden relative group">
      <div className="absolute inset-0 bg-accent-blue/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

      <div className="flex items-center justify-between relative">
        <div className="flex items-center gap-4">
          <div
            className={`p-3 rounded-xl border ${
              status === "error"
                ? "bg-rose-500/10 border-rose-500/20 text-rose-500"
                : "bg-accent-blue/10 border-accent-blue/20 text-accent-blue"
            }`}
          >
            {status === "playing" ? (
              <Activity className="w-5 h-5 animate-pulse" />
            ) : (
              <Volume2 className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mb-0.5">
              {provider} •{" "}
              {status === "connecting"
                ? "Connecting..."
                : status === "streaming"
                  ? "Handshaking..."
                  : status === "playing"
                    ? "Stream active"
                    : status}
            </div>
            <div className="text-sm font-bold text-white/90 truncate max-w-[200px]">
              {status === "connecting"
                ? "Preparing synthetic voice..."
                : text || "Waiting for audio..."}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {errorMsg && (
            <span className="text-[10px] font-black text-rose-400 uppercase bg-rose-500/10 px-2 py-1 rounded-md">
              {errorMsg}
            </span>
          )}
          <button
            type="button"
            onClick={interrupt}
            className="p-3 bg-white/5 hover:bg-rose-500/20 border border-white/10 hover:border-rose-500/30 text-white/40 hover:text-rose-500 rounded-xl transition-all active:scale-95"
            title="Interrupt / Stop"
          >
            <XCircle size={18} />
          </button>
        </div>
      </div>

      {(status === "streaming" || status === "playing") && (
        <div className="mt-4 h-1 bg-white/5 rounded-full overflow-hidden">
          <div className="h-full bg-accent-blue animate-[progress_3s_ease-in-out_infinite] w-full origin-left" />
        </div>
      )}
    </div>
  );
};
