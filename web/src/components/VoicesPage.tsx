import { Loader2, Play, Star, Upload } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";

import { BACKEND, fetchVoices } from "../api";

interface Voice {
  id: string;
  name: string;
  provider: string;
  type: "base" | "cloned";
  isFavorite: boolean;
}

const VoicesPage: React.FC = () => {
  const [provider, setProvider] = useState<
    "windows" | "elevenlabs" | "hume" | "gemini"
  >("windows");
  const [voices, setVoices] = useState<Voice[]>([]);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [isFetching, setIsFetching] = useState(true);
  const [isCloning, setIsCloning] = useState(false);
  const [ttsError, setTtsError] = useState("");
  const [cloneSuccess, setCloneSuccess] = useState("");
  const [cloneName, setCloneName] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    async function init() {
      setIsFetching(true);
      const data = await fetchVoices();
      const all: Voice[] = [];
      data.providers?.forEach((p: { voices: string[]; name: string }) => {
        p.voices.forEach((v: string) => {
          all.push({
            id: v,
            name: v,
            provider: p.name,
            type: "base",
            isFavorite: false,
          });
        });
      });
      setVoices(all);
      setIsFetching(false);
    }
    init();
  }, []);

  const toggleFav = (id: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const preview = async (voice: Voice) => {
    if (isLoading) return;
    setIsLoading(voice.id);
    setTtsError("");
    const text =
      "This is a neural synthesis preview from the Speech MCP Gateway.";
    try {
      const res = await fetch(
        `${BACKEND}/api/v1/tts/wav?text=${encodeURIComponent(text)}&provider=${voice.provider}&voice_id=${encodeURIComponent(voice.id)}`,
      );
      if (!res.ok) throw new Error(`Backend ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        await audioRef.current.play();
      }
    } catch (e) {
      setTtsError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsLoading(null);
    }
  };

  const [cloneFile, setCloneFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleClone = async () => {
    if (!cloneName || !cloneFile) return;
    setIsCloning(true);
    setTtsError("");
    try {
      const token = localStorage.getItem("SPEECH_MCP_AUTH_TOKEN") || "";
      const formData = new FormData();
      formData.append("name", cloneName);
      formData.append("file", cloneFile);
      const res = await fetch(`${BACKEND}/api/v1/voices/clone`, {
        method: "POST",
        headers: token ? { "X-Speech-MCP-Auth": token } : {},
        body: formData,
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.detail || data.error || "Clone failed");
      setCloneSuccess(`Cloned OK — voice_id: ${data.voice_id}`);
      setTtsError("");
      setCloneName("");
      setCloneFile(null);
      // Refresh voice list
      const fresh = await fetchVoices();
      const all: Voice[] = [];
      fresh.providers?.forEach((p: { voices: string[]; name: string }) => {
        p.voices.forEach((v: string) => {
          all.push({ id: v, name: v, provider: p.name, type: "base", isFavorite: false });
        });
      });
      setVoices(all);
    } catch (e) {
      setTtsError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsCloning(false);
    }
  };

  const filtered = voices.filter((v) => v.provider === provider);

  return (
    <div className="space-y-6 animate-in fade-in duration-700">
      {/* biome-ignore lint/a11y/useMediaCaption: Hidden audio element for logic only */}
      <audio ref={audioRef} className="hidden" />

      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Voice Architecture
          </h1>
          <p className="text-sm text-white/50 uppercase tracking-widest mt-1">
            Neural identity library — {voices.length} Identity segments
          </p>
        </div>
        {isFetching && (
          <Loader2 className="animate-spin text-violet-500 mb-2" size={20} />
        )}
      </header>

      {ttsError && (
        <div className="glass-card p-4 border border-rose-500/30 text-rose-400 text-sm font-bold uppercase tracking-wider flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          {ttsError}
        </div>
      )}
      {cloneSuccess && (
        <div className="glass-card p-4 border border-emerald-500/30 text-emerald-400 text-sm font-bold uppercase tracking-wider flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          {cloneSuccess}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Provider + Library */}
        <div className="lg:col-span-2 glass-card p-8 space-y-6">
          {/* Provider tabs */}
          <div className="flex flex-wrap gap-2">
            {(["windows", "hume", "elevenlabs", "gemini"] as const).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setProvider(p)}
                className={`px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                  provider === p
                    ? "bg-violet-600 text-white shadow-lg shadow-violet-600/20"
                    : "bg-white/5 text-white/40 hover:bg-white/10 hover:text-white"
                }`}
              >
                {p === "windows"
                  ? "SAPI5"
                  : p === "hume"
                    ? "Octave"
                    : p === "elevenlabs"
                      ? "ElevenLabs"
                      : "Gemini 3.1"}
              </button>
            ))}
          </div>

          {/* Voice list */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {isFetching ? (
              Array(6)
                .fill(0)
                .map((_, i) => (
                  <div
                    /* biome-ignore lint/suspicious/noArrayIndexKey: Safe for static skeleton */
                    key={i}
                    className="h-16 rounded-xl bg-white/[0.02] animate-pulse"
                  />
                ))
            ) : filtered.length === 0 ? (
              <div className="py-12 md:col-span-2 text-center text-white/20 text-sm uppercase font-black tracking-[0.2em]">
                No active voices for this substrate
              </div>
            ) : (
              filtered.map((voice) => (
                <div
                  key={voice.id}
                  className="flex items-center gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-violet-500/30 transition-all group"
                >
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 bg-white/5 border border-white/5 group-hover:bg-violet-600/10 group-hover:border-violet-600/30 transition-all font-black text-white/20 group-hover:text-violet-400">
                    {voice.name[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-black text-white text-sm truncate uppercase tracking-tight">
                      {voice.name}
                    </div>
                    <div className="text-[10px] text-white/30 uppercase tracking-widest font-bold">
                      {voice.provider}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleFav(voice.id)}
                    className={`p-2 rounded-lg transition-all ${favorites.has(voice.id) ? "text-amber-400 scale-110" : "text-white/10 hover:text-white/30"}`}
                  >
                    <Star
                      size={14}
                      fill={favorites.has(voice.id) ? "currentColor" : "none"}
                    />
                  </button>
                  <button
                    type="button"
                    onClick={() => preview(voice)}
                    disabled={!!isLoading}
                    className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all bg-white/5 text-white/30 hover:bg-violet-600 hover:text-white`}
                  >
                    {isLoading === voice.id ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Play size={14} className="fill-current ml-0.5" />
                    )}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Clone panel */}
        <div className="glass-card p-8 space-y-6 flex flex-col">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-10 h-10 bg-violet-600/10 border border-violet-600/20 rounded-xl flex items-center justify-center text-violet-500 shadow-inner">
              <Upload size={18} />
            </div>
            <div>
              <h3 className="text-sm font-black text-white uppercase tracking-widest">
                Identity Clone
              </h3>
              <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest">
                Instant Voice Cloning
              </p>
            </div>
          </div>

          <div
            className="flex-1 border-2 border-dashed border-white/5 rounded-2xl p-8 text-center hover:border-violet-500/20 transition-all cursor-pointer bg-white/[0.01]"
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,.mp3,.wav,.m4a,.flac,.ogg"
              className="hidden"
              onChange={(e) => setCloneFile(e.target.files?.[0] ?? null)}
            />
            <div className="text-4xl mb-4 opacity-40">🧬</div>
            <p className="text-sm font-black text-white uppercase tracking-tighter">
              {cloneFile ? cloneFile.name : "Snippet Ingestion"}
            </p>
            <p className="text-[10px] text-white/20 mt-2 uppercase tracking-widest font-bold">
              {cloneFile ? `${(cloneFile.size / 1024).toFixed(0)} KB — click to change` : "MP3, WAV, M4A — 5s minimum"}
            </p>
          </div>

          <div>
            <label
              htmlFor="clone-handle"
              className="block text-xs font-black text-white/40 uppercase tracking-widest mb-3"
            >
              Cloned Handle
            </label>
            <input
              id="clone-handle"
              type="text"
              value={cloneName}
              onChange={(e) => setCloneName(e.target.value)}
              placeholder="e.g. Sandra_V1"
              className="w-full bg-white/[0.03] border border-white/5 rounded-xl p-4 text-white text-sm outline-none focus:border-violet-500/30 transition-all font-mono"
            />
          </div>

          <button
            type="button"
            onClick={handleClone}
            disabled={isCloning || !cloneName || !cloneFile}
            className="w-full btn-primary py-4 uppercase font-black tracking-widest text-xs flex items-center justify-center gap-2"
          >
            {isCloning && <Loader2 size={14} className="animate-spin" />}
            Start Synthesis
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoicesPage;
