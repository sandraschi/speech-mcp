import React, { useState } from 'react';

interface Voice {
    id: string;
    name: string;
    type: 'base' | 'cloned';
    isFavorite: boolean;
    previewUrl: string;
}

const VoicesPage: React.FC = () => {
    const [voices, setVoices] = useState<Voice[]>([
        { id: 'ito', name: 'Ito', type: 'base', isFavorite: true, previewUrl: '#' },
        { id: 'koda', name: 'Koda', type: 'base', isFavorite: false, previewUrl: '#' },
        { id: 'leo', name: 'Leo', type: 'base', isFavorite: false, previewUrl: '#' },
        { id: 'clone-1', name: 'Sandra Proxy', type: 'cloned', isFavorite: true, previewUrl: '#' },
    ]);

    const toggleFavorite = (id: string) => {
        setVoices(prev => prev.map(v => v.id === id ? { ...v, isFavorite: !v.isFavorite } : v));
    };

    return (
        <div className="page-header">
            {/* Header Section */}
            <section>
                <h2 className="page-title">Voice Architecture</h2>
                <p style={{ color: 'var(--text-secondary)' }}>Manage base identities and neural clones for empathic synthesis.</p>
            </section>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px' }}>
                {/* Voice Cloning Card */}
                <section className="glass-card cloning-card">
                    <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '24px' }}>🧬</span> Neural Cloning
                    </h3>
                    <div className="cloning-dropzone">
                        <span style={{ fontSize: '40px' }}>📤</span>
                        <div style={{ textAlign: 'center' }}>
                            <p style={{ fontWeight: 600 }}>Drop audio sample here</p>
                            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Minimum 5 seconds recommended</p>
                        </div>
                    </div>

                    <div style={{ marginTop: '24px' }}>
                        <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '8px' }}>Clone Name</label>
                        <input type="text" placeholder="e.g. Executive Support" className="glass-card" style={{
                            width: '100%',
                            background: 'var(--bg-primary)',
                            padding: '12px',
                            color: 'white',
                            outline: 'none',
                            border: '1px solid var(--glass-border)'
                        }} />
                    </div>

                    <button className="accent-glow btn-new-session" style={{ width: '100%', marginTop: '20px' }}>
                        Start Cloning
                    </button>
                </section>

                {/* Voice Library */}
                <section className="glass-card library-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                        <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '24px' }}>📚</span> Identity Library
                        </h3>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="glass-card" style={{ padding: '6px 12px', fontSize: '12px' }}>All</button>
                            <button className="glass-card" style={{ padding: '6px 12px', fontSize: '12px', opacity: 0.5 }}>Favorites</button>
                        </div>
                    </div>

                    <div className="voice-list">
                        {voices.map(voice => (
                            <div key={voice.id} className="voice-item">
                                <div className="voice-avatar" style={{
                                    background: voice.type === 'base' ? 'var(--accent-blue)' : 'var(--accent-purple)'
                                }}>
                                    {voice.type === 'base' ? '👤' : '🤖'}
                                </div>

                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600 }}>{voice.name}</div>
                                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                        {voice.type === 'base' ? 'Official Base Voice' : 'Neural Clone'}
                                    </div>
                                </div>

                                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                    <button style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}>▶️</button>
                                    <button
                                        onClick={() => toggleFavorite(voice.id)}
                                        style={{
                                            background: 'none',
                                            border: 'none',
                                            fontSize: '20px',
                                            cursor: 'pointer',
                                            color: voice.isFavorite ? '#fcd34d' : 'var(--text-secondary)',
                                            transition: 'var(--transition-smooth)'
                                        }}
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
