import React, { useState } from 'react';
import { Save, RefreshCw, Layers, Shield, Cloud, Terminal, Database, Cpu } from 'lucide-react';

const SettingsPage: React.FC = () => {
    const [localProvider, setLocalProvider] = useState('ollama');
    const [localModel, setLocalModel] = useState('llama3.1:8b');
    const [cloudKey, setCloudKey] = useState(localStorage.getItem('OPENAI_API_KEY') || '');
    const [humeKey, setHumeKey] = useState(localStorage.getItem('HUME_API_KEY') || '');
    const [humeSecret, setHumeSecret] = useState(localStorage.getItem('HUME_SECRET_KEY') || '');
    const [elevenKey, setElevenKey] = useState(localStorage.getItem('ELEVENLABS_API_KEY') || '');

    const handleSave = () => {
        localStorage.setItem('OPENAI_API_KEY', cloudKey);
        localStorage.setItem('HUME_API_KEY', humeKey);
        localStorage.setItem('HUME_SECRET_KEY', humeSecret);
        localStorage.setItem('ELEVENLABS_API_KEY', elevenKey);
        alert('Settings synchronized with local storage.');
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-black text-white uppercase tracking-tighter">System Configuration</h1>
                    <p className="text-text-secondary text-sm font-bold uppercase tracking-widest opacity-60">Substrate Tuning & Neural Linkage</p>
                </div>
                <button
                    onClick={handleSave}
                    className="btn-primary py-4 px-8 group shadow-[0_0_30px_rgba(59,130,246,0.2)]"
                >
                    <Save size={18} className="group-hover:scale-110 transition-transform" />
                    Save Changes
                </button>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Local LLM Stack */}
                <section className="glass-card p-8 flex flex-col h-full">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="bg-emerald-500/10 p-4 rounded-2xl border border-emerald-500/20 text-emerald-500">
                            <Cpu size={24} />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-white uppercase tracking-tighter">Local Intelligence</h3>
                            <p className="text-xs font-bold text-text-secondary uppercase tracking-widest opacity-40">On-premise inference cluster</p>
                        </div>
                    </div>

                    <div className="space-y-6 flex-1">
                        <div className="space-y-2">
                            <label className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-50 ml-1">Provider Engine</label>
                            <select
                                value={localProvider}
                                onChange={(e) => setLocalProvider(e.target.value)}
                                title="Local LLM Provider"
                                className="w-full bg-white/[0.03] border border-white/5 rounded-xl p-4 text-white focus:border-accent-purple/50 outline-none transition-all font-bold uppercase tracking-wider cursor-pointer"
                            >
                                <option value="ollama">Ollama (Detected)</option>
                                <option value="lmstudio">LM Studio</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-50 ml-1">Available Models</label>
                            <div className="flex gap-3">
                                <select
                                    value={localModel}
                                    onChange={(e) => setLocalModel(e.target.value)}
                                    title="Available LLM Models"
                                    className="flex-1 bg-white/[0.03] border border-white/5 rounded-xl p-4 text-white focus:border-accent-purple/50 outline-none transition-all font-bold tracking-wide cursor-pointer"
                                >
                                    <option value="llama3.1:8b">Llama 3.1 8B (v2)</option>
                                    <option value="gemma2:9b">Gemma 2 9B (Production)</option>
                                    <option value="mistral:latest">Mistral Instruct</option>
                                    <option value="phi3:mini">Phi-3 Mini 128K</option>
                                </select>
                                <button title="Sync Repository" className="bg-white/5 p-4 rounded-xl border border-white/5 hover:bg-white/10 hover:border-white/20 transition-all">
                                    <RefreshCw size={18} className="text-accent-blue" />
                                </button>
                            </div>
                        </div>

                        <div className="bg-emerald-500/5 border border-emerald-500/10 p-5 rounded-2xl mt-4 flex items-center gap-4">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            <p className="text-xs font-bold text-emerald-500/80 uppercase tracking-widest">
                                RTX 4090 detected. Tensor acceleration active.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Cloud & Production Keys */}
                <section className="glass-card p-8">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="bg-accent-blue/10 p-4 rounded-2xl border border-accent-blue/20 text-accent-blue">
                            <Cloud size={24} />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-white uppercase tracking-tighter">Production Keys</h3>
                            <p className="text-xs font-bold text-text-secondary uppercase tracking-widest opacity-40">External synthesis endpoints</p>
                        </div>
                    </div>

                    <div className="space-y-5">
                        <div className="space-y-2">
                            <label className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-50 ml-1">OpenAI Integration</label>
                            <div className="relative group">
                                <input
                                    type="password"
                                    value={cloudKey}
                                    onChange={(e) => setCloudKey(e.target.value)}
                                    placeholder="sk-..."
                                    title="OpenAI API Key"
                                    className="w-full bg-white/[0.02] border border-white/5 rounded-xl p-4 text-white focus:border-accent-blue/50 focus:bg-white/[0.04] outline-none font-mono text-sm transition-all pr-12"
                                />
                                <Shield className="absolute right-4 top-1/2 -translate-y-1/2 text-white/10 group-focus-within:text-accent-blue/30 transition-colors" size={16} />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-50 ml-1">Hume API</label>
                                <input
                                    type="password"
                                    value={humeKey}
                                    title="Hume API Key"
                                    placeholder="API Key"
                                    onChange={(e) => setHumeKey(e.target.value)}
                                    className="w-full bg-white/[0.02] border border-white/5 rounded-xl p-4 text-white focus:border-accent-purple/50 outline-none font-mono text-xs transition-all"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-50 ml-1">Hume Secret</label>
                                <input
                                    type="password"
                                    value={humeSecret}
                                    title="Hume Secret Key"
                                    placeholder="Secret Key"
                                    onChange={(e) => setHumeSecret(e.target.value)}
                                    className="w-full bg-white/[0.02] border border-white/5 rounded-xl p-4 text-white focus:border-accent-purple/50 outline-none font-mono text-xs transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-50 ml-1">ElevenLabs Synthesis</label>
                            <input
                                type="password"
                                value={elevenKey}
                                title="ElevenLabs API Key"
                                placeholder="Key for high-fidelity cloning"
                                onChange={(e) => setElevenKey(e.target.value)}
                                className="w-full bg-white/[0.02] border border-white/5 rounded-xl p-4 text-white focus:border-accent-blue/50 outline-none font-mono text-sm transition-all"
                            />
                        </div>
                    </div>
                </section>

                {/* Substrate Integration */}
                <section className="glass-card p-8 lg:col-span-2">
                    <div className="flex items-center gap-4 mb-10">
                        <div className="bg-accent-purple/10 p-4 rounded-2xl border border-accent-purple/20 text-accent-purple">
                            <Layers size={24} />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-white uppercase tracking-tighter">Substrate Diagnostics</h3>
                            <p className="text-xs font-bold text-text-secondary uppercase tracking-widest opacity-40">Protocol bridge & vector status</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <StatusItem icon={<Terminal size={14} />} label="MCP Transport" value="Studion / JSON-RPC" status="active" />
                        <StatusItem icon={<Database size={14} />} label="RAG Vector DB" value="LanceDB (v13.0)" status="active" />
                        <StatusItem icon={<Cpu size={14} />} label="Hardware Accel" value="CUDA/NVIDIA RTX" status="active" />
                    </div>
                </section>
            </div>
        </div>
    );
};

const StatusItem = ({ icon, label, value, status }: { icon: React.ReactNode, label: string, value: string, status: string }) => (
    <div className="bg-white/[0.02] border border-white/5 p-6 rounded-2xl flex items-center gap-5 hover:bg-white/[0.04] hover:border-white/10 transition-all group">
        <div className="bg-white/5 p-3 rounded-xl text-text-secondary opacity-40 group-hover:opacity-100 group-hover:text-accent-blue transition-all">
            {icon}
        </div>
        <div>
            <div className="text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-40 mb-1">{label}</div>
            <div className="text-sm font-black text-white leading-tight">{value}</div>
            <div className={`text-xs uppercase font-black mt-2 flex items-center gap-2 ${status === 'active' ? 'text-emerald-500' : 'text-rose-500'}`}>
                <span className={`w-1 h-1 rounded-full ${status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                {status}
            </div>
        </div>
    </div>
);

export default SettingsPage;
