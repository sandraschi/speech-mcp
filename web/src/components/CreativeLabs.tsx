import React, { useState } from 'react';
import { Book, Zap, Music, Play, Languages, Sliders, Sparkles, Wand2 } from 'lucide-react';

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
        content: "Comme je descendais des Fleuves impassibles,\nJe ne me sentis plus guidé par les haleurs..."
    },
    {
        title: "The Raven",
        author: "Edgar Allan Poe",
        lang: "en",
        content: "Once upon a midnight dreary, while I pondered, weak and weary,\nOver many a quaint and curious volume of forgotten lore..."
    },
    {
        title: "Sa Aking Mga Kabata",
        author: "José Rizal",
        lang: "tl",
        content: "Kapagka ang baya’y sadyang umiibig\nSa kanyang salitang kaloob ng langit..."
    }
];

const TONGUE_TWISTERS = [
    "Betty Botter bought some butter, but she said the butter's bitter.",
    "Ang relo ni Leroy ay rolex.",
    "Six slippery snails slid slowly seaward."
];

const CreativeLabs: React.FC = () => {
    const [selectedPoem, setSelectedPoem] = useState<Poem | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [emotion, setEmotion] = useState(50);
    const [translation, setTranslation] = useState('');

    const handleRead = (text: string) => {
        if (!text) return;
        setIsPlaying(true);
        // Simulated TTS call logic
        setTimeout(() => setIsPlaying(false), 3000);
    };

    const handleTranslate = (text: string) => {
        // Mock English -> Tagalog bridge
        if (text.toLowerCase().includes('hello')) setTranslation('Kamusta');
        else if (text.toLowerCase().includes('world')) setTranslation('Mundo');
        else setTranslation('Translation loop active...');
    };

    return (
        <div className="h-full space-y-8 animate-in fade-in duration-700">
            {/* Header Card */}
            <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-3xl p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
                <div className="flex items-center gap-4">
                    <div className="bg-indigo-600 p-4 rounded-3xl shadow-[0_0_20px_rgba(79,70,229,0.3)]">
                        <Wand2 className="text-white w-10 h-10" />
                    </div>
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">Creative Labs</h1>
                        <p className="text-slate-400 mt-1 font-medium text-lg">Expressive Prosody & Neural Translation Loop</p>
                    </div>
                </div>
                <div className="flex flex-wrap gap-3">
                    <span className="bg-indigo-500/10 text-indigo-400 px-4 py-1.5 rounded-full text-xs font-black border border-indigo-500/20 tracking-widest uppercase shadow-sm">SOTA Emotion</span>
                    <span className="bg-emerald-500/10 text-emerald-400 px-4 py-1.5 rounded-full text-xs font-black border border-emerald-500/20 tracking-widest uppercase shadow-sm">Polyglot v2</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                {/* Left Column (Spans 8) */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Poem Reader Card */}
                    <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 blur-[100px] rounded-full -mr-32 -mt-32" />

                        <div className="relative flex items-center justify-between mb-10">
                            <div className="flex items-center gap-4">
                                <div className="bg-indigo-600 p-3 rounded-2xl">
                                    <Book className="text-white w-6 h-6" />
                                </div>
                                <h3 className="text-2xl font-black text-white tracking-tight">Expressive Poem Reader</h3>
                            </div>
                            <div className="hidden sm:flex items-center gap-6 bg-slate-950/50 p-3 rounded-2xl border border-slate-800">
                                <div className="flex items-center gap-3">
                                    <Sliders className="w-5 h-5 text-slate-500" />
                                    <label htmlFor="prosody-steering" className="text-xs font-black text-slate-500 uppercase tracking-widest">Prosody Steering</label>
                                </div>
                                <input
                                    type="range"
                                    id="prosody-steering"
                                    min="0" max="100"
                                    value={emotion}
                                    onChange={(e) => setEmotion(parseInt(e.target.value))}
                                    className="w-40 accent-indigo-500 h-1.5 rounded-full"
                                />
                                <span className="text-sm font-mono text-indigo-400 font-bold w-10 text-right">{emotion}%</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
                            {POEMS.map(p => (
                                <button
                                    key={p.title}
                                    onClick={() => setSelectedPoem(p)}
                                    className={`relative p-6 rounded-[2rem] border-2 text-left transition-all duration-300 group ${selectedPoem?.title === p.title
                                        ? 'bg-indigo-600/10 border-indigo-500/50 shadow-[0_0_20px_rgba(79,70,229,0.1)]'
                                        : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700 hover:scale-[1.02]'
                                        }`}
                                >
                                    <div className="text-[10px] font-black uppercase tracking-widest text-indigo-500/70 mb-2">{p.lang}</div>
                                    <div className="font-black text-white text-lg truncate mb-1">{p.title}</div>
                                    <div className="text-xs font-medium opacity-60 italic">{p.author}</div>
                                    {selectedPoem?.title === p.title && (
                                        <div className="absolute top-4 right-4 animate-pulse">
                                            <div className="w-2 h-2 rounded-full bg-indigo-500" />
                                        </div>
                                    )}
                                </button>
                            ))}
                        </div>

                        {selectedPoem ? (
                            <div className="bg-slate-950 border border-slate-800 rounded-[2rem] p-10 relative group/view shadow-inner">
                                <div className="absolute top-8 right-8 z-10">
                                    <button
                                        onClick={() => handleRead(selectedPoem.content)}
                                        disabled={isPlaying}
                                        className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white w-20 h-20 rounded-full shadow-[0_10px_30px_rgba(79,70,229,0.4)] transition-all hover:scale-110 flex items-center justify-center group/btn"
                                    >
                                        {isPlaying ? <Music className="w-8 h-8 animate-bounce" /> : <Play className="w-8 h-8 fill-current translate-x-1" />}
                                    </button>
                                </div>
                                <div className="max-w-2xl mx-auto">
                                    <pre className="text-slate-200 font-serif text-2xl leading-relaxed whitespace-pre-wrap px-8 italic text-center drop-shadow-sm">
                                        "{selectedPoem.content}"
                                    </pre>
                                </div>
                            </div>
                        ) : (
                            <div className="h-64 flex flex-col items-center justify-center border-4 border-dashed border-slate-900 rounded-[2.5rem] text-slate-700 group-hover:border-slate-800 transition-colors">
                                <Sparkles className="w-12 h-12 mb-4 opacity-20" />
                                <p className="text-xl font-black uppercase tracking-tighter">Select a Poem for Neural Synthesis</p>
                            </div>
                        )}
                    </div>

                    {/* Translation Bridge Card */}
                    <div className="bg-slate-900/30 border border-slate-800 rounded-[2.5rem] p-10 shadow-xl">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="bg-emerald-500/20 p-3 rounded-2xl text-emerald-400">
                                <Languages className="w-6 h-6" />
                            </div>
                            <h3 className="text-2xl font-black text-white tracking-tight">Cognitive Translation Bridge</h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                            <div className="space-y-4">
                                <div className="flex justify-between items-center px-4">
                                    <label htmlFor="english-input" className="text-xs font-black text-slate-500 uppercase tracking-widest">English Input</label>
                                    <span className="text-[10px] text-slate-700 font-mono italic">Source: Human/EVI</span>
                                </div>
                                <textarea
                                    id="english-input"
                                    onChange={(e) => handleTranslate(e.target.value)}
                                    placeholder="Dictate in English..."
                                    className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-8 text-white text-xl font-light focus:border-emerald-500/50 focus:ring-0 min-h-[160px] shadow-inner transition-all placeholder-slate-800"
                                />
                            </div>
                            <div className="space-y-4 relative">
                                <div className="absolute -left-5 top-1/2 -translate-y-1/2 hidden md:block">
                                    <Zap className="text-emerald-500/20 w-10 h-10 animate-pulse rotate-90" />
                                </div>
                                <div className="flex justify-between items-center px-4">
                                    <label htmlFor="tagalog-output" className="text-xs font-black text-emerald-500 uppercase tracking-widest">Tagalog Output</label>
                                    <div className="flex gap-1">
                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                                    </div>
                                </div>
                                <div id="tagalog-output" className="w-full bg-slate-900 border border-emerald-950/50 rounded-2xl p-8 text-emerald-50 text-xl min-h-[160px] flex items-center justify-center font-medium text-center shadow-lg">
                                    {translation || "Awaiting Signal..."}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column (Spans 4) */}
                <div className="lg:col-span-4 space-y-8">
                    {/* Tongue Twister Card */}
                    <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden">
                        <div className="absolute bottom-0 left-0 w-48 h-48 bg-amber-500/5 blur-[80px] rounded-full -ml-24 -mb-24" />

                        <div className="relative flex items-center gap-4 mb-10">
                            <div className="bg-amber-500/20 p-3 rounded-2xl text-amber-500 shadow-inner">
                                <Sparkles className="w-6 h-6" />
                            </div>
                            <h3 className="text-2xl font-black text-white tracking-tight">Tongue Twister Lab</h3>
                        </div>

                        <div className="space-y-4 relative">
                            {TONGUE_TWISTERS.map((tt, i) => (
                                <div key={i} className="group/tt relative">
                                    <div className="absolute inset-0 bg-indigo-500/5 blur-2xl opacity-0 group-hover/tt:opacity-100 transition-opacity" />
                                    <div className="relative bg-slate-950/80 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 transition-all cursor-pointer group hover:scale-[1.02] shadow-sm">
                                        <p className="text-slate-200 text-lg leading-relaxed font-serif italic mb-4">"{tt}"</p>
                                        <div className="flex justify-between items-center border-t border-slate-800 pt-4">
                                            <span className="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em]">Challenge Mode</span>
                                            <button className="bg-indigo-600/20 p-2 rounded-xl text-indigo-400 border border-indigo-500/20 hover:bg-indigo-600 hover:text-white transition-all shadow-sm" onClick={() => handleRead(tt)} title="Synthesize and play audio">
                                                <Play className="w-5 h-5 fill-current" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Stats/Profile Card */}
                    <div className="bg-gradient-to-br from-indigo-950/30 to-slate-950/30 border border-indigo-500/10 rounded-[2.5rem] p-8 shadow-xl">
                        <h4 className="text-white font-black text-xs mb-6 uppercase tracking-widest flex items-center gap-2">
                            Neural Aesthetic Profile
                        </h4>
                        <div className="space-y-6">
                            {[
                                { label: 'Prosody Engine', value: 'Hume EVI v3', color: 'text-indigo-400' },
                                { label: 'Latency Node', value: 'Vienna-West', color: 'text-blue-400' },
                                { label: 'Cross-Link', value: 'Resonite:8000', color: 'text-emerald-400' },
                                { label: 'Emotion Depth', value: 'Industrial', color: 'text-amber-400' },
                            ].map((stat) => (
                                <div key={stat.label} className="flex justify-between items-center border-b border-white/5 pb-4 last:border-0 last:pb-0">
                                    <span className="text-[10px] font-black text-slate-600 uppercase">{stat.label}</span>
                                    <span className={`text-xs font-mono font-black ${stat.color}`}>{stat.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CreativeLabs;
