import React from 'react';

interface AppLayoutProps {
    children: React.ReactNode;
    onNavigate: (page: string) => void;
    activePage: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, onNavigate, activePage }) => {
    return (
        <div className="app-container" style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
            {/* Sidebar */}
            <aside className="glass-card" style={{
                width: '280px',
                margin: '16px',
                display: 'flex',
                flexDirection: 'column',
                padding: '24px',
                gap: '32px'
            }}>
                <div className="logo" style={{ fontSize: '24px', fontWeight: 800, background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    SPEECH-MCP
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <NavItem icon="🏠" label="Dashboard" active={activePage === 'dashboard'} onClick={() => onNavigate('dashboard')} />
                    <NavItem icon="🎙️" label="EVI Session" active={activePage === 'evi'} onClick={() => onNavigate('evi')} />
                    <NavItem icon="🔊" label="Octave TTS" active={activePage === 'tts'} onClick={() => onNavigate('tts')} />
                    <NavItem icon="👤" label="Voice Clones" active={activePage === 'voices'} onClick={() => onNavigate('voices')} />
                    <NavItem icon="📊" label="Analysis" active={activePage === 'analysis'} onClick={() => onNavigate('analysis')} />
                    <NavItem icon="🔧" label="Tools" active={activePage === 'tools'} onClick={() => onNavigate('tools')} />
                </nav>

                <div style={{ marginTop: 'auto' }}>
                    <div className="glass-card" style={{ padding: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <span>MCP Server</span>
                            <span style={{ color: '#10b981' }}>● Online</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Port</span>
                            <span>10760</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main style={{ flex: 1, padding: '32px', overflowY: 'auto' }}>
                <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
                    <h1 style={{ fontSize: '32px' }}>Midnight Empathy</h1>
                    <div style={{ display: 'flex', gap: '16px' }}>
                        <button className="glass-card" style={{ padding: '10px 20px', color: 'var(--text-primary)' }}>Settings</button>
                        <button className="accent-glow" style={{
                            padding: '10px 24px',
                            background: 'var(--accent-gradient)',
                            border: 'none',
                            borderRadius: '12px',
                            color: 'white',
                            fontWeight: 600
                        }}>New Session</button>
                    </div>
                </header>

                {children}
            </main>
        </div>
    );
};

const NavItem = ({ icon, label, active = false, onClick }: { icon: string, label: string, active?: boolean, onClick: () => void }) => (
    <div
        onClick={onClick}
        style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '12px',
            cursor: 'pointer',
            background: active ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
            color: active ? 'var(--accent-purple)' : 'var(--text-secondary)',
            transition: 'var(--transition-smooth)',
            fontWeight: active ? 600 : 400
        }}>
        <span style={{ fontSize: '20px' }}>{icon}</span>
        <span>{label}</span>
    </div>
);

export default AppLayout;
