import {
  Activity,
  Book,
  Languages,
  Music,
  Play,
  Sliders,
  Sparkles,
  Zap,
} from "lucide-react";
import type React from "react";
import { useRef, useState } from "react";

import { BACKEND, runDemo } from "../api";
import { StreamPlayback } from "./StreamPlayback";

const GEMINI_VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Orion", "Puck"];

interface Poem {
  title: string;
  author: string;
  lang: string;
  content: string;
}

const POEMS: Poem[] = [
  {
    title: "Le Bateau Ivre",
    author: "Arthur Rimbaud",
    lang: "fr",
    content:
      "Comme je descendais des Fleuves impassibles,\nJe ne me sentis plus guidé par les haleurs...",
  },
  {
    title: "The Raven",
    author: "Edgar Allan Poe",
    lang: "en",
    content:
      "Once upon a midnight dreary, while I pondered, weak and weary,\nOver many a quaint and curious volume of forgotten lore...",
  },
  {
    title: "Sa Aking Mga Kabata",
    author: "José Rizal",
    lang: "tl",
    content:
      "Kapagka ang baya'y sadyang umiibig\nSa kanyang salitang kaloob ng langit...",
  },
];

const TONGUE_TWISTERS = [
  "Betty Botter bought some butter, but she said the butter's bitter.",
  "Ang relo ni Leroy ay rolex.",
  "Six slippery snails slid slowly seaward.",
];

const CreativeLabs: React.FC = () => {
  const [selectedPoem, setSelectedPoem] = useState<Poem | null>(null);
  const [emotion, setEmotion] = useState(50);
  const [translation, setTranslation] = useState("");
  const [isLoading, _setIsLoading] = useState(false);
  const [ttsError, _setTtsError] = useState("");
  const [streamData, setStreamData] = useState<{
    url: string;
    text: string;
    provider: string;
  } | null>(null);
  const [selectedVoice, setSelectedVoice] = useState("Aoede");
  const [playKey, setPlayKey] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleRead = async (text: string) => {
    if (!text) return;
    const flat = text.replace(/\n+/g, " ").trim();
    const token = localStorage.getItem("SPEECH_MCP_AUTH_TOKEN") || "admin-token";
    const wsUrl =
      BACKEND.replace("http", "ws") +
      `/ws/stream?provider=gemini&voice=${selectedVoice}&token=${token}`;

    setStreamData({ url: wsUrl, text: flat, provider: "gemini" });
    setPlayKey((prev) => prev + 1);
  };

  const handleTranslate = (text: string) => {
    if (text.toLowerCase().includes("hello")) setTranslation("Kamusta");
    else if (text.toLowerCase().includes("world")) setTranslation("Mundo");
    else if (text.length > 3) setTranslation("...");
    else setTranslation("");
  };

  const handleRunIndustrialDemo = async (demo: string) => {
    _setIsLoading(true);
    _setTtsError("");
    try {
      const res = await runDemo(demo);
      if (!res.success) throw new Error(res.error);
    } catch (e) {
      _setTtsError(e instanceof Error ? e.message : String(e));
    } finally {
      _setIsLoading(false);
    }
  };

  return (
    <div className="h-full space-y-8 animate-in fade-in duration-700">
      {/* Hidden audio element */}
      {/* biome-ignore lint/a11y/useMediaCaption: Hidden audio element for logic only */}
      <audio ref={audioRef} style={{ display: "none" }} />

      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Creative Labs
          </h1>
          <p
            className="text-sm font-bold uppercase tracking-widest"
            style={{ color: "#94a3b8" }}
          >
            Neural Prosody & Translation
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <span className="px-3 py-1 bg-violet-500/10 border border-violet-500/20 rounded-full text-xs font-black uppercase tracking-widest text-violet-400">
            SOTA Emotion
          </span>
          <span className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs font-black uppercase tracking-widest text-text-secondary opacity-60">
            Polyglot v2
          </span>
        </div>
      </header>

      {/* Status bar */}
      {(isLoading || ttsError) && (
        <div
          className={`glass-card p-3 flex items-center gap-3 ${ttsError ? "border-rose-500/30" : ""}`}
        >
          <div
            className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isLoading ? "bg-yellow-400 animate-pulse" : "bg-rose-500"}`}
          />
          <span
            className={`text-sm ${ttsError ? "text-rose-400" : "text-white/80"}`}
          >
            {ttsError || "Synthesizing…"}
          </span>
        </div>
      )}

      {/* Industrial Showcase */}
      <section className="space-y-4">
        <h2 className="text-sm font-black text-white/40 uppercase tracking-[0.2em] px-1">
          Industrial Showcase
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              id: "neko",
              title: "Wagahai wa Neko",
              desc: "Japanese literary reading via Gemini 3.1 Flash.",
              icon: "🐈",
              color: "border-emerald-500/20",
              btn: "bg-emerald-600",
            },
            {
              id: "shakespeare",
              title: "The Bard's Soliloquy",
              desc: "Dramatic Hamlet monologue with Charon voice.",
              icon: "🎭",
              color: "border-violet-500/20",
              btn: "bg-violet-600",
            },
            {
              id: "price",
              title: "The Price Experience",
              desc: "Sinister horror narration via Hume Octave.",
              icon: "🦇",
              color: "border-rose-500/20",
              btn: "bg-rose-600",
            },
          ].map((d) => (
            <div
              key={d.id}
              className={`glass-card p-6 flex flex-col justify-between border ${d.color} hover:bg-white/[0.04] transition-all group`}
            >
              <div>
                <div className="text-3xl mb-4 group-hover:scale-110 transition-transform origin-left">
                  {d.icon}
                </div>
                <h3 className="text-base font-black text-white uppercase tracking-tighter mb-2">
                  {d.title}
                </h3>
                <p className="text-xs text-white/40 leading-relaxed font-bold uppercase tracking-wide">
                  {d.desc}
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleRunIndustrialDemo(d.id)}
                disabled={isLoading}
                className={`mt-6 w-full py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest text-white transition-all active:scale-[0.98] ${d.btn} shadow-lg shadow-black/20`}
              >
                Trigger Execution
              </button>
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column */}
        <div className="lg:col-span-8 space-y-8">
          {/* Poem Reader */}
          <div className="glass-card p-8 relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
              <div className="flex items-center gap-3">
                <div className="bg-violet-500/10 p-2.5 rounded-xl border border-violet-500/20 text-violet-400">
                  <Book size={18} />
                </div>
                <h2 className="text-lg font-black text-white uppercase tracking-tighter">
                  Poem Reader
                </h2>
              </div>
              <div className="flex items-center gap-4 glass-card px-4 py-2 bg-white/[0.02]">
                <label
                  htmlFor="voiceSelect"
                  className="text-xs font-bold text-white/60 uppercase tracking-wider"
                >
                  Voice
                </label>
                <select
                  id="voiceSelect"
                  value={selectedVoice}
                  onChange={(e) => setSelectedVoice(e.target.value)}
                  className="bg-transparent text-xs font-black text-violet-400 outline-none border-none cursor-pointer"
                >
                  {GEMINI_VOICES.map((v) => (
                    <option key={v} value={v} className="bg-slate-900">
                      {v}
                    </option>
                  ))}
                </select>
                <div className="h-4 w-px bg-white/10" />
                <Sliders size={13} className="text-white/40" />
                <label
                  htmlFor="prosody"
                  className="text-xs font-bold text-white/60 uppercase tracking-wider"
                >
                  Prosody
                </label>
                <input
                  type="range"
                  id="prosody"
                  min="0"
                  max="100"
                  value={emotion}
                  onChange={(e) => setEmotion(parseInt(e.target.value, 10))}
                  className="w-28 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-violet-500"
                />
                <span className="text-xs font-black text-violet-400 w-8 text-right tabular-nums">
                  {emotion}%
                </span>
              </div>
            </div>

            {/* Poem selector */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
              {POEMS.map((p) => (
                <button
                  key={p.title}
                  type="button"
                  onClick={() => setSelectedPoem(p)}
                  className={`p-4 rounded-xl border transition-all text-left ${
                    selectedPoem?.title === p.title
                      ? "bg-violet-500/10 border-violet-500/40"
                      : "bg-white/[0.02] border-white/8 hover:border-white/15 hover:bg-white/[0.04]"
                  }`}
                >
                  <div
                    className={`text-xs font-black uppercase tracking-widest mb-1 ${selectedPoem?.title === p.title ? "text-violet-400" : "text-white/40"}`}
                  >
                    {p.lang}
                  </div>
                  <div className="font-black text-white text-sm truncate">
                    {p.title}
                  </div>
                  <div className="text-xs text-white/40 truncate mt-0.5">
                    {p.author}
                  </div>
                </button>
              ))}
            </div>

            {selectedPoem ? (
              <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-8 relative">
                <button
                  type="button"
                  onClick={() => handleRead(selectedPoem.content)}
                  disabled={isLoading}
                  title="Play"
                  className="absolute top-4 right-4 w-14 h-14 rounded-full bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white flex items-center justify-center transition-all shadow-lg"
                >
                  {isLoading ? (
                    <Music className="w-6 h-6 animate-bounce" />
                  ) : (
                    <Play className="w-6 h-6 fill-current ml-0.5" />
                  )}
                </button>
                <pre
                  className="text-white text-lg leading-relaxed whitespace-pre-wrap italic pr-20"
                  style={{ fontFamily: "Georgia, serif" }}
                >
                  {selectedPoem.content}
                </pre>
              </div>
            ) : (
              <div className="h-40 flex items-center justify-center border-2 border-dashed border-white/8 rounded-2xl">
                <p className="text-sm text-white/30 uppercase tracking-widest">
                  Select a poem above
                </p>
              </div>
            )}
          </div>

          {/* Translation Bridge */}
          <div className="glass-card p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-emerald-500/10 p-2.5 rounded-xl border border-emerald-500/20 text-emerald-400">
                <Languages size={18} />
              </div>
              <h2 className="text-lg font-black text-white uppercase tracking-tighter">
                Translation Bridge
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label
                  htmlFor="english-input"
                  className="block text-xs font-bold text-white/50 uppercase tracking-wider mb-2"
                >
                  English Input
                </label>
                <textarea
                  id="english-input"
                  onChange={(e) => handleTranslate(e.target.value)}
                  placeholder="Type something..."
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-4 text-white text-base focus:border-emerald-500/40 outline-none min-h-[120px] resize-none"
                />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Zap size={12} className="text-emerald-400" />
                  <label
                    htmlFor="tagalog-output"
                    className="text-xs font-bold text-emerald-400 uppercase tracking-wider"
                  >
                    Tagalog Output
                  </label>
                </div>
                <div
                  id="tagalog-output"
                  className="w-full bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4 text-emerald-100 text-xl font-black min-h-[120px] flex items-center justify-center"
                >
                  {translation || (
                    <span className="text-white/20 text-sm uppercase tracking-widest">
                      Waiting…
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-4 space-y-6">
          {/* Tongue Twisters */}
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 mb-5">
              <Sparkles size={15} className="text-amber-400" />
              <h3 className="text-xs font-black text-white uppercase tracking-widest">
                Prosody Lab
              </h3>
            </div>
            <div className="space-y-3">
              {TONGUE_TWISTERS.map((tt) => (
                <div
                  key={tt}
                  className="bg-white/[0.03] border border-white/8 rounded-xl p-4 hover:border-violet-500/30 transition-all"
                >
                  <p className="text-white/85 text-sm leading-relaxed italic mb-3">
                    "{tt}"
                  </p>
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => handleRead(tt)}
                      title="Play"
                      className="w-8 h-8 bg-white/5 rounded-lg text-white/40 border border-white/10 hover:bg-violet-600 hover:text-white hover:border-violet-500 transition-all flex items-center justify-center"
                    >
                      <Play size={14} className="fill-current" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Info */}
          <div className="glass-card p-6 border-violet-500/20">
            <h4 className="text-white font-black text-xs mb-5 uppercase tracking-widest flex items-center gap-2">
              <Activity size={13} className="text-violet-400" />
              Profile
            </h4>
            <div className="space-y-2">
              {[
                {
                  label: "Engine",
                  value: "Windows SAPI5",
                  color: "text-blue-400",
                },
                {
                  label: "Prosody",
                  value: "Hume EVI v3",
                  color: "text-violet-400",
                },
                {
                  label: "OSC",
                  value: "Resonite:9000",
                  color: "text-emerald-400",
                },
                {
                  label: "Emotion",
                  value: `${emotion}%`,
                  color: "text-amber-400",
                },
              ].map((s) => (
                <div
                  key={s.label}
                  className="flex justify-between items-center p-3 bg-white/[0.02] rounded-lg border border-white/5"
                >
                  <span className="text-xs text-white/50 uppercase tracking-wider">
                    {s.label}
                  </span>
                  <span
                    className={`text-xs font-black ${s.color} uppercase tracking-wider`}
                  >
                    {s.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {streamData && (
        <div className="fixed bottom-8 right-8 z-50 w-full max-w-md">
          <StreamPlayback
            streamUrl={streamData.url}
            provider={streamData.provider as "gemini" | "hume" | "elevenlabs" | "windows"}
            text={streamData.text}
            playKey={playKey}
            onDone={() => setStreamData(null)}
          />
        </div>
      )}
    </div>
  );
};

export default CreativeLabs;
