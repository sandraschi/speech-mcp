import {
  Activity,
  Globe,
  Languages,
  Music,
  Play,
  Search,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import type React from "react";
import { useMemo, useRef, useState } from "react";

import { BACKEND, runDemo } from "../api";
import { StreamPlayback } from "./StreamPlayback";

const GEMINI_VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Orion", "Puck"];

interface LanguageSample {
  name: string;
  code: string;
  native: string;
  flag: string;
  category: "European" | "Slavic" | "Classical" | "Experimental" | "Global";
  samples: {
    title: string;
    author: string;
    content: string;
  }[];
}

const LANGUAGES: LanguageSample[] = [
  {
    name: "English",
    code: "en",
    native: "English",
    flag: "🇬🇧",
    category: "European",
    samples: [
      {
        title: "The Raven",
        author: "Edgar Allan Poe",
        content:
          "[serious] Once upon a midnight dreary, while I pondered, weak and weary, [whispers] Over many a quaint and curious volume of forgotten lore...",
      },
    ],
  },
  {
    name: "French",
    code: "fr",
    native: "Français",
    flag: "🇫🇷",
    category: "European",
    samples: [
      {
        title: "Le Bateau Ivre",
        author: "Arthur Rimbaud",
        content:
          "[happy] Comme je descendais des Fleuves impassibles, [whispers] Je ne me sentis plus guidé par les haleurs...",
      },
    ],
  },
  {
    name: "German",
    code: "de",
    native: "Deutsch",
    flag: "🇩🇪",
    category: "European",
    samples: [
      {
        title: "Wandrers Nachtlied II",
        author: "J.W. von Goethe",
        content:
          "[whispers] Über allen Gipfeln ist Ruh, in allen Wipfeln spürest du kaum einen Hauch; [softly] die Vögelein schweigen im Walde. Warte nur, balde ruhest du auch.",
      },
    ],
  },
  {
    name: "Spanish",
    code: "es",
    native: "Español",
    flag: "🇪🇸",
    category: "European",
    samples: [
      {
        title: "Don Quijote",
        author: "Miguel de Cervantes",
        content:
          "En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero.",
      },
    ],
  },
  {
    name: "Italian",
    code: "it",
    native: "Italiano",
    flag: "🇮🇹",
    category: "European",
    samples: [
      {
        title: "Divina Commedia",
        author: "Dante Alighieri",
        content:
          "Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura, ché la diritta via era smarrita.",
      },
    ],
  },
  {
    name: "Hungarian",
    code: "hu",
    native: "Magyar",
    flag: "🇭🇺",
    category: "European",
    samples: [
      {
        title: "Nemzeti Dal",
        author: "Petőfi Sándor",
        content:
          "Talpra magyar, hí hí a haza! Itt az idő, most vagy soha! Rabok legyünk, vagy szabadok? Ez a kérdés, válasszatok!",
      },
    ],
  },
  {
    name: "Russian",
    code: "ru",
    native: "Русский",
    flag: "🇷🇺",
    category: "Slavic",
    samples: [
      {
        title: "Eugene Onegin",
        author: "Alexander Pushkin",
        content:
          "[serious] Я к вам пишу — чего же боле? Что я могу еще сказать? [whispers] Теперь, я знаю, в вашей воле Меня презреньем наказать.",
      },
    ],
  },
  {
    name: "Ukrainian",
    code: "uk",
    native: "Українська",
    flag: "🇺🇦",
    category: "Slavic",
    samples: [
      {
        title: "Zapovit",
        author: "Taras Shevchenko",
        content:
          "[dramatically] Як умру, то поховайте Мене на могилі Серед степу широкого На Вкраїні милій.",
      },
    ],
  },
  {
    name: "Polish",
    code: "pl",
    native: "Polski",
    flag: "🇵🇱",
    category: "Slavic",
    samples: [
      {
        title: "Pan Tadeusz",
        author: "Adam Mickiewicz",
        content:
          "[happy] Litwo! Ojczyzno moja! ty jesteś jak zdrowie. [whispers] Ile cię trzeba cenić, ten tylko się dowie, Kto cię stracił.",
      },
    ],
  },
  {
    name: "Esperanto",
    code: "eo",
    native: "Esperanto",
    flag: "🟢",
    category: "Experimental",
    samples: [
      {
        title: "La Espero",
        author: "L. L. Zamenhof",
        content:
          "[excited] En la mondon venis nova sento, tra la mondo iras forta voko; [whispers] per flugiloj de facila vento nun de loko flugu ĝi al loko.",
      },
    ],
  },
  {
    name: "Klingon",
    code: "tlh",
    native: "tlhIngan Hol",
    flag: "⚔️",
    category: "Experimental",
    samples: [
      {
        title: "Warrior's Creed",
        author: "Klingon Empire",
        content:
          "[serious] tlhIngan Hol Dajatlh'a'? [angry] Heghlu'meH QaQ jajvam!",
      },
    ],
  },
  {
    name: "Sindarin",
    code: "sjn",
    native: "Sindarin (Elvish)",
    flag: "🧝",
    category: "Experimental",
    samples: [
      {
        title: "Meeting Star",
        author: "J.R.R. Tolkien",
        content:
          "[whispers] Elen síla lúmenn' omentielvo. A star shines on the hour of our meeting.",
      },
    ],
  },
  {
    name: "Latin",
    code: "la",
    native: "Latina",
    flag: "🏛️",
    category: "Classical",
    samples: [
      {
        title: "Aeneid",
        author: "Virgil",
        content:
          "Arma virumque cano, Troiae qui primus ab oris Italiam, fato profugus, Laviniaque venit litora.",
      },
    ],
  },
  {
    name: "Classical Greek",
    code: "grc",
    native: "Ἑλληνική",
    flag: "📜",
    category: "Classical",
    samples: [
      {
        title: "Odyssey",
        author: "Homer",
        content:
          "Ἄνδρα μοι ἔννεπε, Μοῦσα, πολύτροπον, ὃς μάλα πολλὰ πλάγχθη, ἐпеὶ Τροίης ἱερὸн πτολίεθρον ἔπερσεν.",
      },
    ],
  },
  {
    name: "Ancient Sumerian",
    code: "sux",
    native: "𒅴𒂠",
    flag: "🏺",
    category: "Classical",
    samples: [
      {
        title: "En-metena",
        author: "Lagash",
        content:
          "Ningirsu-ra, En-metena-ke, E-ninnu-mu-na-du. For Ningirsu, En-metena built the Eninnu.",
      },
    ],
  },
  {
    name: "Hindi",
    code: "hi",
    native: "हिन्दी",
    flag: "🇮🇳",
    category: "Global",
    samples: [
      {
        title: "Pratishodh",
        author: "Jai Shankar Prasad",
        content: "वह देख, उस आकाश में कैसे बादलों का जमघट है। वह सब मेरी आँखों के आँसू हैं।",
      },
    ],
  },
  {
    name: "Cantonese",
    code: "zh-HK",
    native: "廣東話",
    flag: "🇭🇰",
    category: "Global",
    samples: [
      {
        title: "Quiet Night",
        author: "Li Bai (Cantonese)",
        content: "床前明月光，疑是地上霜。舉頭望明月，低頭思故鄉。",
      },
    ],
  },
  {
    name: "Kiswahili",
    code: "sw",
    native: "Kiswahili",
    flag: "🇰🇪",
    category: "Global",
    samples: [
      {
        title: "Mshairi",
        author: "Shaaban Robert",
        content:
          "Kila mtu ni mshairi wa maisha yake mwenyewe. Maneno ni nguvu, na sauti ni roho.",
      },
    ],
  },
  {
    name: "Tagalog",
    code: "tl",
    native: "Tagalog",
    flag: "🇵🇭",
    category: "Global",
    samples: [
      {
        title: "Sa Aking Mga Kabata",
        author: "José Rizal",
        content:
          "Kapagka ang baya'y sadyang umiibig Sa kanyang salitang kaloob ng langit.",
      },
    ],
  },
];

const TONGUE_TWISTERS = [
  "Betty Botter bought some butter, but she said the butter's bitter.",
  "Ang relo ni Leroy ay rolex.",
  "Six slippery snails slid slowly seaward.",
];

const CreativeLabs: React.FC = () => {
  const [selectedLang, setSelectedLang] = useState(LANGUAGES[0]);
  const [selectedSample, setSelectedSample] = useState(LANGUAGES[0].samples[0]);
  const [emotion, setEmotion] = useState(50);
  const [translation, setTranslation] = useState("");
  const [isLoading, _setIsLoading] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [ttsError, _setTtsError] = useState("");
  const [streamData, setStreamData] = useState<{
    url: string;
    text: string;
    provider: "gemini" | "hume" | "elevenlabs" | "windows";
  } | null>(null);
  const [selectedVoice, setSelectedVoice] = useState("Aoede");
  const [playKey, setPlayKey] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const filteredLanguages = useMemo(() => {
    if (!searchQuery) return LANGUAGES;
    const q = searchQuery.toLowerCase();
    return LANGUAGES.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.native.toLowerCase().includes(q) ||
        l.category.toLowerCase().includes(q),
    );
  }, [searchQuery]);

  const handleRead = async (text: string) => {
    if (!text) return;
    setIsConnecting(true);
    const flat = text.replace(/\n+/g, " ").trim();
    const token =
      localStorage.getItem("SPEECH_MCP_AUTH_TOKEN") || "admin-token";
    const wsUrl =
      BACKEND.replace("http", "ws") +
      `/ws/stream?provider=gemini&voice=${selectedVoice}&token=${token}`;

    setStreamData({
      url: wsUrl,
      text: flat,
      provider: "gemini" as const,
    });
    setPlayKey((prev) => prev + 1);
  };

  const handleTranslate = (text: string) => {
    if (text.toLowerCase().includes("hello")) setTranslation("Kamusta");
    else if (text.toLowerCase().includes("world")) setTranslation("Mundo");
    else if (text.length > 3) setTranslation("...");
    else setTranslation("");
  };

  const handleRunModernDemo = async (demo: string) => {
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
      {/* biome-ignore lint/a11y/useMediaCaption: Hidden audio element for logic context */}
      <audio ref={audioRef} style={{ display: "none" }} />

      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Creative Labs
          </h1>
          <p className="text-sm font-bold uppercase tracking-widest text-slate-400">
            Prosody & Translation
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <span className="px-3 py-1 bg-violet-500/10 border border-violet-500/20 rounded-full text-xs font-black uppercase tracking-widest text-violet-400">
            Expressive Emotion
          </span>
          <span className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs font-black uppercase tracking-widest text-text-secondary opacity-60">
            Global Polyglot
          </span>
        </div>
      </header>

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
            {ttsError || "Executing Demo..."}
          </span>
        </div>
      )}

      {/* Polyglot Lab Overlay Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xl animate-in fade-in zoom-in duration-300">
          <div className="glass-card w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden border-white/10 shadow-2xl">
            <header className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-4">
                <div className="bg-violet-600 p-2.5 rounded-xl text-white shadow-lg shadow-violet-600/20">
                  <Globe size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-white uppercase tracking-tighter">
                    Linguistic Library
                  </h2>
                  <p className="text-xs font-bold text-white/30 uppercase tracking-[0.2em]">
                    Zero-Shot Multilingual Mastery
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="p-2 hover:bg-white/10 rounded-full text-white/40 hover:text-white transition-all"
              >
                <X size={24} />
              </button>
            </header>

            <div className="p-4 bg-white/[0.01] border-b border-white/5">
              <div className="relative">
                <Search
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20"
                  size={18}
                />
                <input
                  type="text"
                  placeholder="Search languages by name or category..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white outline-none focus:border-violet-500/40 transition-all font-bold uppercase text-xs tracking-widest"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-12">
              {[
                "European",
                "Slavic",
                "Classical",
                "Experimental",
                "Global",
              ].map((category) => {
                const langs = filteredLanguages.filter(
                  (l) => l.category === category,
                );
                if (langs.length === 0) return null;
                return (
                  <div key={category} className="space-y-4">
                    <h3 className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] border-l-2 border-violet-600 pl-3">
                      {category} Group
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {langs.map((l) => (
                        <button
                          key={l.code}
                          type="button"
                          onClick={() => {
                            setSelectedLang(l);
                            setSelectedSample(l.samples[0]);
                            setIsModalOpen(false);
                          }}
                          className={`group relative p-6 rounded-2xl border text-left transition-all hover:scale-[1.02] active:scale-[0.98] ${
                            selectedLang.code === l.code
                              ? "bg-violet-600 border-violet-500 shadow-xl shadow-violet-600/20"
                              : "bg-white/[0.03] border-white/10 hover:border-white/20 hover:bg-white/[0.06]"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-3xl">{l.flag}</span>
                            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                              <Play
                                size={14}
                                className="text-white fill-current"
                              />
                            </div>
                          </div>
                          <div
                            className={`font-black uppercase tracking-tighter ${selectedLang.code === l.code ? "text-white" : "text-white/80"}`}
                          >
                            {l.name}
                          </div>
                          <div
                            className={`text-[10px] font-bold uppercase tracking-widest ${selectedLang.code === l.code ? "text-white/60" : "text-white/30"}`}
                          >
                            {l.native}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Modern Showcase */}
      <section className="space-y-4">
        <h2 className="text-sm font-black text-white/40 uppercase tracking-[0.2em] px-1">
          Modern Showcase
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
                onClick={() => handleRunModernDemo(d.id)}
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
        {/* Left Column: Polyglot Lab */}
        <div className="lg:col-span-8 space-y-6">
          <div className="glass-card p-8">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
              <div className="flex items-center gap-4">
                <div className="bg-violet-500/10 p-2.5 rounded-xl border border-violet-500/20 text-violet-400">
                  <Languages size={18} />
                </div>
                <div>
                  <h2 className="text-lg font-black text-white uppercase tracking-tighter">
                    Polyglot Lab
                  </h2>
                  <p className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">
                    {selectedLang.name} Mastery
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4 glass-card px-4 py-2 bg-white/[0.02] border-white/10">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(true)}
                  className="bg-violet-600 hover:bg-violet-500 px-3 py-1.5 rounded-lg text-[10px] font-black text-white uppercase tracking-widest transition-all flex items-center gap-2"
                >
                  <Globe size={12} />
                  {selectedLang.flag} Change Language
                </button>

                <div className="h-4 w-px bg-white/10" />

                <div className="flex items-center gap-3">
                  <label
                    htmlFor="voiceSelect"
                    className="text-xs font-bold text-white/50 uppercase tracking-wider"
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
                </div>

                <div className="h-4 w-px bg-white/10" />

                <div className="flex items-center gap-3">
                  <label
                    htmlFor="prosody"
                    className="text-xs font-bold text-white/50 uppercase tracking-wider"
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
                    className="w-16 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-violet-500"
                  />
                </div>
              </div>
            </header>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
              {selectedLang.samples.map((s) => (
                <button
                  key={s.title}
                  type="button"
                  onClick={() => setSelectedSample(s)}
                  className={`p-4 rounded-xl border transition-all text-left ${
                    selectedSample.title === s.title
                      ? "bg-violet-500/10 border-violet-500/40"
                      : "bg-white/[0.02] border-white/8 hover:border-white/15 hover:bg-white/[0.04]"
                  }`}
                >
                  <div
                    className={`text-[10px] font-black uppercase tracking-widest mb-1 ${selectedSample.title === s.title ? "text-violet-400" : "text-white/40"}`}
                  >
                    {selectedSample.title === s.title
                      ? "Active Sample"
                      : selectedLang.native}
                  </div>
                  <div className="font-black text-white text-sm truncate">
                    {s.title}
                  </div>
                  <div className="text-xs text-white/40 truncate mt-0.5">
                    {s.author}
                  </div>
                </button>
              ))}
            </div>

            <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-8 relative">
              <button
                type="button"
                onClick={() => handleRead(selectedSample.content)}
                disabled={isConnecting}
                className={`absolute top-4 right-4 w-16 h-16 rounded-full bg-violet-600 hover:bg-violet-500 disabled:opacity-80 text-white flex items-center justify-center transition-all shadow-xl active:scale-95 z-10 ${isConnecting ? "animate-pulse" : ""}`}
              >
                {isConnecting ? (
                  <div className="relative">
                    <Music className="w-6 h-6 animate-bounce" />
                    <div className="absolute inset-0 w-full h-full rounded-full animate-ping bg-white/20" />
                  </div>
                ) : (
                  <Play className="w-7 h-7 fill-current ml-1" />
                )}
              </button>
              <textarea
                className="w-full bg-transparent text-white text-2xl leading-relaxed whitespace-pre-wrap italic pr-24 outline-none border-none resize-none min-h-[200px]"
                style={{ fontFamily: "Georgia, serif" }}
                value={selectedSample.content}
                onChange={(e) =>
                  setSelectedSample({
                    ...selectedSample,
                    content: e.target.value,
                  })
                }
              />
              {isConnecting && (
                <div className="absolute bottom-4 left-8 animate-pulse flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                  <span className="text-[10px] font-black text-violet-400 uppercase tracking-widest">
                    Connecting to TTS...
                  </span>
                </div>
              )}
            </div>
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
                      className="w-8 h-8 bg-white/5 rounded-lg text-white/40 border border-white/10 hover:bg-violet-600 hover:text-white hover:border-violet-500 transition-all flex items-center justify-center"
                    >
                      <Play size={14} className="fill-current" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card p-6 border-violet-500/20">
            <h4 className="text-white font-black text-xs mb-5 uppercase tracking-widest flex items-center gap-2">
              <Activity size={13} className="text-violet-400" /> Profile
            </h4>
            <div className="space-y-2">
              {[
                {
                  label: "Engine",
                  value: "Gemini 3.1",
                  color: "text-blue-400",
                },
                {
                  label: "Stability",
                  value: "v5",
                  color: "text-violet-400",
                },
                {
                  label: "Polyglot",
                  value: "Enabled",
                  color: "text-emerald-400",
                },
                {
                  label: "Prosody",
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
            provider={streamData.provider}
            text={streamData.text}
            playKey={playKey}
            onDone={() => {
              setStreamData(null);
              setIsConnecting(false);
            }}
          />
        </div>
      )}
    </div>
  );
};

export default CreativeLabs;
