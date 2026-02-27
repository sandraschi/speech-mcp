import React, { useState } from 'react';
import AppLayout from './components/AppLayout';
import ToolsPage from './components/ToolsPage';
import VoicesPage from './components/VoicesPage';
import SemanticSearch from './components/SemanticSearch';
import InteractionLab from './components/InteractionLab';
import CreativeLabs from './components/CreativeLabs';
import ServiceLinkage from './components/ServiceLinkage';
import HistoryPage from './components/HistoryPage';

// Stable wave data generated outside component to avoid impure render calls
const WAVE_DATA = [...Array(20)].map((_, i) => ({
  height: `${20 + Math.random() * 80}%`,
  delay: `${Math.random()}s`,
  opacity: 0.3 + (i * 0.03)
}));
const Dashboard: React.FC<{ onNavigate: (page: string) => void }> = ({ onNavigate }) => (
  <div className="dashboard-grid">
    <section className="glass-card visualizer-section">
      <div className="m-b-16">
        <h2 className="font-14 uppercase tracking-widest text-secondary">Active Voice Stream</h2>
        <p className="font-14 text-secondary">Empathic detection: <span className="text-accent">Calm / Focused</span></p>
      </div>

      <div className="wave-container">
        {WAVE_DATA.map((wave, i) => (
          <div key={i} className="wave-bar" style={{
            '--wave-height': wave.height,
            '--wave-opacity': wave.opacity,
            '--pulse-speed': `${0.5 + parseFloat(wave.delay)}s`
          } as React.CSSProperties} />
        ))}
      </div>
    </section>

    <section className="glass-card emotion-section">
      <h2 className="font-14 uppercase tracking-widest text-secondary m-b-24">Emotional Dynamics</h2>
      <div className="emotion-list">
        <EmotionBar label="Admiration" value={82} color="#fcd34d" />
        <EmotionBar label="Calmness" value={95} color="#3b82f6" />
        <EmotionBar label="Interest" value={64} color="#8b5cf6" />
        <EmotionBar label="Joy" value={21} color="#f472b6" />
      </div>
    </section>

    <div className="action-grid">
      <ActionCard
        title="Clone Voice"
        desc="Create high-fidelity clones from 5s audio."
        icon="👥"
        onClick={() => onNavigate('voices')}
      />
      <ActionCard
        title="Synthesize"
        desc="Generate expressive speech via Octave."
        icon="✨"
        onClick={() => onNavigate('tts')}
      />
      <ActionCard
        title="Forensic Trace"
        desc="Access previous voice interactions."
        icon="🕒"
        onClick={() => onNavigate('history')}
      />
    </div>
  </div>
);

function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [authToken, setAuthToken] = useState<string | null>(localStorage.getItem('SPEECH_MCP_AUTH_TOKEN'));

  const handleLogin = (token: string) => {
    localStorage.setItem('SPEECH_MCP_AUTH_TOKEN', token);
    setAuthToken(token);
  };

  if (!authToken) {
    return <AuthOverlay onLogin={handleLogin} />;
  }

  return (
    <AppLayout onNavigate={setActivePage} activePage={activePage}>
      {activePage === 'dashboard' ? (
        <Dashboard onNavigate={setActivePage} />
      ) : activePage === 'voices' ? (
        <VoicesPage />
      ) : activePage === 'semantic' ? (
        <SemanticSearch />
      ) : (activePage === 'lab' || activePage === 'evi') ? (
        <InteractionLab />
      ) : (activePage === 'creative' || activePage === 'tts') ? (
        <CreativeLabs />
      ) : activePage === 'tools' ? (
        <ToolsPage />
      ) : activePage === 'services' ? (
        <ServiceLinkage />
      ) : (activePage === 'history' || activePage === 'analysis') ? (
        <HistoryPage />
      ) : (
        <div className="glass-card under-construction">
          <h2 className="m-b-16">Module Under Construction</h2>
          <p className="text-secondary">The {activePage} interface is currently being synchronized with the MCP substrate.</p>
        </div>
      )}
    </AppLayout>
  );
}

const EmotionBar = ({ label, value, color }: { label: string, value: number, color: string }) => (
  <div className="emotion-item">
    <div className="emotion-label">
      <span>{label}</span>
      <span className="text-secondary">{value}%</span>
    </div>
    <div className="emotion-track">
      <div className="emotion-fill" style={{
        width: `${value}%`,
        background: color,
        boxShadow: `0 0 10px ${color}33`
      }} />
    </div>
  </div>
);

const ActionCard = ({ title, desc, icon, onClick }: { title: string, desc: string, icon: string, onClick?: () => void }) => (
  <div className="glass-card action-card" onClick={onClick}>
    <div className="card-icon">{icon}</div>
    <h3 className="m-b-8">{title}</h3>
    <p className="text-secondary font-14 flex-1">
      {desc}
    </p>
  </div>
);

const AuthOverlay = ({ onLogin }: { onLogin: (token: string) => void }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleAuth = () => {
    if (username === 'admin' && password === 'admin') {
      onLogin('admin-token');
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="auth-overlay">
      <div className="glass-card auth-card">
        <h2 className="m-b-16 text-center">Speech-MCP Bastion</h2>
        <p className="text-secondary m-b-24 text-center font-14">
          Restricted access. Use <span className="text-accent">admin/admin</span> for development.
        </p>

        {error && <div className="text-rose-500 m-b-16 text-center font-13">{error}</div>}

        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          className="auth-input m-b-8"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="auth-input"
        />
        <button
          onClick={handleAuth}
          className="auth-button"
        >
          Authenticate
        </button>
      </div>
    </div>
  );
};

export default App;
