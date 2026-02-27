import React, { useState } from 'react';
import AppLayout from './components/AppLayout';
import ToolsPage from './components/ToolsPage';
import VoicesPage from './components/VoicesPage';

// Stable wave data generated outside component to avoid impure render calls
const WAVE_DATA = [...Array(20)].map((_, i) => ({
  height: `${20 + Math.random() * 80}%`,
  delay: `${Math.random()}s`,
  opacity: 0.3 + (i * 0.03)
}));

function App() {
  const [activePage, setActivePage] = useState('dashboard');

  return (
    <AppLayout onNavigate={setActivePage} activePage={activePage}>
      {activePage === 'dashboard' ? (
        <div className="dashboard-grid">
          {/* Real-time Visualizer */}
          <section className="glass-card visualizer-section">
            <div style={{ marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px' }}>Active Voice Stream</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Empathic detection: <span style={{ color: 'var(--accent-purple)' }}>Calm / Focused</span></p>
            </div>

            <div className="wave-container">
              {WAVE_DATA.map((wave, i) => (
                <div key={i} className="wave-bar" style={{
                  height: wave.height,
                  opacity: wave.opacity,
                  ['--pulse-speed' as any]: `${0.5 + parseFloat(wave.delay)}s`
                }} />
              ))}
            </div>
          </section>

          {/* Emotion Wheel */}
          <section className="glass-card emotion-section">
            <h2 style={{ fontSize: '18px', marginBottom: '24px' }}>Emotional Dynamics</h2>
            <div className="emotion-list">
              <EmotionBar label="Admiration" value={82} color="#fcd34d" />
              <EmotionBar label="Calmness" value={95} color="#3b82f6" />
              <EmotionBar label="Interest" value={64} color="#8b5cf6" />
              <EmotionBar label="Joy" value={21} color="#f472b6" />
            </div>
          </section>

          {/* Action Cards */}
          <div className="action-grid">
            <ActionCard title="Clone Voice" desc="Create high-fidelity clones from 5s audio." icon="👥" onClick={() => setActivePage('voices')} />
            <ActionCard title="Synthesize" desc="Generate expressive speech via Octave." icon="✨" />
            <ActionCard title="History" desc="Access previous voice interactions." icon="🕒" />
          </div>
        </div>
      ) : activePage === 'voices' ? (
        <VoicesPage />
      ) : activePage === 'tools' ? (
        <ToolsPage />
      ) : (
        <div className="glass-card under-construction">
          <h2 style={{ marginBottom: '16px' }}>Module Under Construction</h2>
          <p style={{ color: 'var(--text-secondary)' }}>The {activePage} interface is currently being synchronized with the MCP substrate.</p>
        </div>
      )}
    </AppLayout>
  );
}

const EmotionBar = ({ label, value, color }: { label: string, value: number, color: string }) => (
  <div className="emotion-item">
    <div className="emotion-label">
      <span>{label}</span>
      <span style={{ color: 'var(--text-secondary)' }}>{value}%</span>
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
    <h3 style={{ marginBottom: '8px' }}>{title}</h3>
    <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.5' }}>{desc}</p>
  </div>
);

export default App;
