import React, { useState } from 'react';
import { StreamPlayback } from './StreamPlayback';

interface Voice {
    id: string;
    name: string;
    type: 'base' | 'cloned';
    isFavorite: boolean;
    previewUrl: string;
}

const VoicesPage: React.FC = () => {
    const [provider, setProvider] = useState<'hume' | 'elevenlabs' | 'windows'>('hume');
    const [activeStream, setActiveStream] = useState<{ url: string, text: string } | null>(null);
    const [voices, setVoices] = useState<Voice[]>([
        { id: 'ito', name: 'Ito', type: 'base', isFavorite: true, previewUrl: '#' },
        { id: 'koda', name: 'Koda', type: 'base', isFavorite: false, previewUrl: '#' },
        { id: 'clone-1', name: 'Sandra Proxy', type: 'cloned', isFavorite: true, previewUrl: '#' },
        { id: 'eleven-m1', name: 'Rachel (11L)', type: 'base', isFavorite: false, previewUrl: '#' },
        { id: 'win-default', name: 'System Default (Local)', type: 'base', isFavorite: false, previewUrl: '#' },
    ]);

    const toggleFavorite = (id: string) => {
        setVoices(prev => prev.map(v => v.id === id ? { ...v, isFavorite: !v.isFavorite } : v));
    };

    const triggerPreview = (voiceId: string) => {
        const url = `ws://localhost:10760/ws/stream?provider=${provider}&voice=${voiceId}`;
        const text = "This is a neural synthesis preview from the Speech MCP Gateway.";
        setActiveStream({ url, text });
    };

    return (
        <div className="page-header">
            {/* Header Section */}
            <section>
                <h2 className="page-title">Voice Architecture</h2>
                <p className="text-secondary">Manage base identities and neural clones for empathic synthesis.</p>
            </section>

            {activeStream && (
                <StreamPlayback
                    streamUrl={activeStream.url}
                    provider={provider}
                    text={activeStream.text}
                />
            )}

            <div className="display-grid grid-cols-12 gap-24">
                {/* Voice Cloning Card */}
                <section className="glass-card cloning-card">
                    <h3 className="m-b-20 d-flex align-center gap-10">
                        <span className="font-24">🧬</span> Neural Cloning
                    </h3>
                    <div className="cloning-dropzone">
                        <span className="font-400">📤</span>
                        <div className="text-center">
                            <p className="font-600">Drop audio sample here</p>
                            <p className="font-12 text-secondary">Minimum 5 seconds recommended</p>
                        </div>
                    </div>

                    <div className="m-t-24">
                        <label className="font-13 text-secondary d-block m-b-8">Clone Name</label>
                        <input type="text" placeholder="e.g. Executive Support" className="glass-card w-full p-12 bg-primary text-white outline-none" />
                    </div>

                    <button className="accent-glow btn-new-session w-full m-t-20">
                        Start Cloning
                    </button>
                </section>

                {/* Voice Library */}
                <section className="glass-card library-card">
                    <div className="d-flex justify-between align-center m-b-24">
                        <h3 className="d-flex align-center gap-10">
                            <span className="font-24">📚</span> Identity Library
                        </h3>
                        <div className="d-flex gap-8">
                            <button className="glass-card p-6-12 font-12">All</button>
                            <button className="glass-card p-6-12 font-12 opacity-50">Favorites</button>
                        </div>
                    </div>

                    <div className="provider-selector d-flex gap-8 m-b-24">
                        <button
                            className={`glass-card p-8-16 font-14 flex-1 ${provider === 'hume' ? 'active' : ''}`}
                            onClick={() => setProvider('hume')}
                        >
                            Hume AI
                        </button>
                        <button
                            className={`glass-card p-8-16 font-14 flex-1 ${provider === 'elevenlabs' ? 'active' : ''}`}
                            onClick={() => setProvider('elevenlabs')}
                        >
                            ElevenLabs
                        </button>
                        <button
                            className={`glass-card p-8-16 font-14 flex-1 ${provider === 'windows' ? 'active' : ''}`}
                            onClick={() => setProvider('windows')}
                        >
                            Windows Local
                        </button>
                    </div>

                    <div className="voice-list">
                        {voices.filter(v => {
                            if (provider === 'hume') return !v.name.includes('(11L)') && !v.name.includes('(Local)');
                            if (provider === 'elevenlabs') return v.name.includes('(11L)');
                            if (provider === 'windows') return v.name.includes('(Local)');
                            return false;
                        }).map(voice => (
                            <div key={voice.id} className="voice-item">
                                <div className={`voice-item-avatar ${voice.type}`}>
                                    {voice.type === 'base' ? '👤' : '🤖'}
                                </div>

                                <div className="voice-item-info">
                                    <div className="voice-item-name">{voice.name}</div>
                                    <div className="voice-item-meta">
                                        {voice.type === 'base' ? 'Official Base Voice' : 'Neural Clone'}
                                    </div>
                                </div>

                                <div className="d-flex gap-12 align-center">
                                    <button
                                        onClick={() => triggerPreview(voice.id)}
                                        className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
                                        title={`Preview ${voice.name}`}
                                    >
                                        ▶️
                                    </button>
                                    <button
                                        onClick={() => toggleFavorite(voice.id)}
                                        className={`btn-favorite ${voice.isFavorite ? 'active' : 'inactive'}`}
                                        title={voice.isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                                    >
                                        {voice.isFavorite ? '⭐' : '☆'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
};

export default VoicesPage;
