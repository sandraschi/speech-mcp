import React from 'react';

const ToolsPage: React.FC = () => {
    const tools = [
        { name: 'text_to_speech', desc: 'Generate expressive speech via Hume Octave TTS (v1).', params: ['text', 'voice_id', 'emotion_features'] },
        { name: 'start_evi_session', desc: 'Initialize real-time WebSocket Empathic Voice Interface session (v2/v3).', params: ['config_id', 'voice_id'] },
        { name: 'manage_voice_clones', desc: 'Create, list, or delete high-fidelity voice clones.', params: ['action', 'name', 'file_path'] }
    ];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <section>
                <h2 style={{ fontSize: '24px', marginBottom: '16px' }}>MCP Tool Registry</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
                    Real-time analysis of the Hume AI Speech-MCP server capabilities.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {tools.map(tool => (
                        <div key={tool.name} className="glass-card" style={{ padding: '24px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                <div>
                                    <h3 style={{ color: 'var(--accent-purple)', fontSize: '18px', marginBottom: '4px' }}>{tool.name}</h3>
                                    <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{tool.desc}</p>
                                </div>
                                <div className="glass-card" style={{ padding: '4px 12px', fontSize: '12px', background: 'rgba(139, 92, 246, 0.1)' }}>
                                    v1.2.0
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                {tool.params.map(param => (
                                    <code key={param} style={{
                                        padding: '4px 10px',
                                        background: 'var(--bg-primary)',
                                        borderRadius: '6px',
                                        fontSize: '12px',
                                        border: '1px solid var(--glass-border)'
                                    }}>
                                        {param}
                                    </code>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="glass-card" style={{ padding: '32px', border: '1px dashed var(--glass-border)', background: 'transparent' }}>
                <h3 style={{ marginBottom: '12px' }}>Portmanteau Rationale</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6' }}>
                    To prevent tool explosion, all related voice operations are consolidated into three high-performance gateways.
                    This follows the FastMCP 2.14.4+ standards for industrial-grade AI orchestration.
                </p>
            </section>
        </div>
    );
};

export default ToolsPage;
