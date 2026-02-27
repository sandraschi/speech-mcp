import React from 'react';

interface AppLayoutProps {
    children: React.ReactNode;
    onNavigate: (page: string) => void;
    activePage: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, onNavigate, activePage }) => {
    return (
        <div className="app-container">
            {/* Sidebar */}
            <aside className="glass-card sidebar">
                <div className="logo">
                    SPEECH-MCP
                </div>

                <nav className="nav-list">
                    <NavItem icon="🏠" label="Dashboard" active={activePage === 'dashboard'} onClick={() => onNavigate('dashboard')} />
                    <NavItem icon="🎙️" label="EVI Session" active={activePage === 'evi'} onClick={() => onNavigate('evi')} />
                    <NavItem icon="🔊" label="Octave TTS" active={activePage === 'tts'} onClick={() => onNavigate('tts')} />
                    <NavItem icon="👤" label="Voice Clones" active={activePage === 'voices'} onClick={() => onNavigate('voices')} />
                    <NavItem icon="📊" label="Analysis" active={activePage === 'analysis'} onClick={() => onNavigate('analysis')} />
                    <NavItem icon="🔧" label="Tools" active={activePage === 'tools'} onClick={() => onNavigate('tools')} />
                </nav>

                <div className="sidebar-footer">
                    <div className="glass-card status-card">
                        <div className="status-row">
                            <span>MCP Server</span>
                            <span className="status-online">● Online</span>
                        </div>
                        <div className="status-row">
                            <span>Port</span>
                            <span>10760</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <header className="main-header">
                    <h1 className="header-title">Midnight Empathy</h1>
                    <div className="header-actions">
                        <button className="glass-card btn-settings">Settings</button>
                        <button className="accent-glow btn-new-session">New Session</button>
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
        className={`nav-item ${active ? 'active' : ''}`}>
        <span className="nav-icon">{icon}</span>
        <span>{label}</span>
    </div>
);

export default AppLayout;
