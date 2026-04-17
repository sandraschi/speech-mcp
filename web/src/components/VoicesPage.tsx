import { Music, Play, Star, Upload } from "lucide-react";
import type React from "react";
import { useRef, useState } from "react";

import { BACKEND } from "../api";

interface Voice {
  id: string;
  name: string;
  type: "base" | "cloned";
  isFavorite: boolean;
}

const VOICES: Voice[] = [
  { id: "ito", name: "Ito", type: "base", isFavorite: true },
  { id: "koda", name: "Koda", type: "base", isFavorite: false },
  {
    id: "win-default",
    name: "System Default (SAPI)",
    type: "base",
    isFavorite: false,
  },
  { id: "clone-1", name: "Sandra Proxy", type: "cloned", isFavorite: true },
  {
    id: "rachel-11l",
    name: "Rachel (ElevenLabs)",
    type: "base",
    isFavorite: false,
  },
];

const VoicesPage: React.FC = () => {
  const [provider, setProvider] = useState<"windows" | "elevenlabs" | "hume">(
    "windows",
  );
  const [voices, setVoices] = useState<Voice[]>(VOICES);
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [ttsError, setTtsError] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const toggleFav = (id: string) =>
    setVoices((prev) =>
      prev.map((v) => (v.id === id ? { ...v, isFavorite: !v.isFavorite } : v)),
    );

  const preview = async (voice: Voice) => {
    if (isLoading) return;
    setIsLoading(voice.id);
    setTtsError("");
    const text =
      "This is a neural synthesis preview from the Speech MCP Gateway.";
    try {
      const res = await fetch(
        `${BACKEND}/api/v1/tts/wav?text=${encodeURIComponent(text)}&provider=${provider}`,
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

  const filtered = voices.filter((v) => {
    if (provider === "hume")
      return !v.name.includes("ElevenLabs") && !v.name.includes("SAPI");
    if (provider === "elevenlabs") return v.name.includes("ElevenLabs");
    if (provider === "windows")
      return v.name.includes("SAPI") || v.type === "base";
    return true;
  });

  return (
    <div className="space-y-6">
      <audio ref={audioRef} className="hidden" aria-hidden="true" />

      <header>
        <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
          Voice Architecture
        </h1>
        <p className="text-sm text-white/50 uppercase tracking-widest mt-1">
          Neural identity library
        </p>
      </header>

      {ttsError && (
        <div className="glass-card p-3 border border-rose-500/30 text-rose-400 text-sm">
          {ttsError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Provider + Library */}
        <div className="lg:col-span-2 glass-card p-6 space-y-5">
          {/* Provider tabs */}
          <div className="flex gap-2">
            {(["windows", "hume", "elevenlabs"] as const).map((p) => (
              <button
                key={p}
                onClick={() => setProvider(p)}
                className={`px-4 py-2 rounded-lg text-xs font-black uppercase tracking-wider transition-all ${
                  provider === p
                    ? "bg-violet-600 text-white"
                    : "bg-white/5 text-white/50 hover:bg-white/10"
                }`}
              >
                {p === "windows"
                  ? "Windows"
                  : p === "hume"
                    ? "Hume AI"
                    : "ElevenLabs"}
              </button>
            ))}
          </div>

          {/* Voice list */}
          <div className="space-y-2">
            {filtered.length === 0 ? (
              <div className="py-8 text-center text-white/30 text-sm">
                No voices for this provider
              </div>
            ) : (
              filtered.map((voice) => (
                <div
                  key={voice.id}
                  className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/10 hover:border-white/20 transition-all"
                >
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 ${
                      voice.type === "cloned"
                        ? "bg-violet-500/15 border border-violet-500/25"
                        : "bg-white/5 border border-white/10"
                    }`}
                  >
                    {voice.type === "cloned" ? "🤖" : "👤"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-white text-sm truncate">
                      {voice.name}
                    </div>
                    <div className="text-xs text-white/40 uppercase tracking-wider">
                      {voice.type === "cloned" ? "Neural Clone" : "Base Voice"}
                    </div>
                  </div>
                  <button
                    onClick={() => toggleFav(voice.id)}
                    title="Toggle favorite"
                    className={`p-2 rounded-lg transition-all ${voice.isFavorite ? "text-amber-400" : "text-white/20 hover:text-white/50"}`}
                  >
                    <Star
                      size={15}
                      fill={voice.isFavorite ? "currentColor" : "none"}
                    />
                  </button>
                  <button
                    onClick={() => preview(voice)}
                    disabled={!!isLoading}
                    title="Preview voice"
                    className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all border ${
                      isLoading === voice.id
                        ? "bg-violet-600 border-violet-500 text-white"
                        : "bg-white/5 border-white/10 text-white/40 hover:bg-violet-600 hover:text-white hover:border-violet-500"
                    }`}
                  >
                    {isLoading === voice.id ? (
                      <Music size={14} className="animate-bounce" />
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
        <div className="glass-card p-6 space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-violet-500/10 border border-violet-500/20 rounded-xl flex items-center justify-center text-violet-400">
              <Upload size={16} />
            </div>
            <h3 className="text-sm font-black text-white uppercase tracking-wider">
              Clone Voice
            </h3>
          </div>

          <div className="border-2 border-dashed border-white/10 rounded-xl p-6 text-center hover:border-violet-500/30 transition-all">
            <div className="text-3xl mb-2">📤</div>
            <p className="text-sm font-bold text-white/60">Drop audio sample</p>
            <p className="text-xs text-white/30 mt-1">
              Min. 5 seconds recommended
            </p>
          </div>

          <div>
            <label className="block text-xs font-bold text-white/50 uppercase tracking-wider mb-2">
              Clone Name
            </label>
            <input
              type="text"
              placeholder="e.g. My Voice"
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-3 text-white text-sm outline-none focus:border-violet-500/40"
            />
          </div>

          <button className="w-full btn-primary py-3 text-sm">
            Start Cloning
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoicesPage;
