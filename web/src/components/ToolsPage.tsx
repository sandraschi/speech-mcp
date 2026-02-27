import React from 'react';

const ToolsPage: React.FC = () => {
    const TOOLS = [
        { name: 'text_to_speech', description: 'Generate expressive speech via Hume Octave TTS (v1).', status: 'active' },
        { name: 'start_evi_session', description: 'Initialize real-time WebSocket Empathic Voice Interface session (v2/v3).', status: 'active' },
        { name: 'manage_voice_clones', description: 'Create, list, or delete high-fidelity voice clones.', status: 'active' }
    ];

    return (
        <div className="tools-container">
            <section className="m-b-32">
                <h2 className="page-title">Neural Instrumentation</h2>
                <p className="text-secondary">Analyze and manage available tools for the speech synthesis engine.</p>
            </section>

            <div className="display-grid grid-cols-12 gap-24">
                <section className="glass-card grid-span-8">
                    <div className="d-flex justify-between align-center m-b-24">
                        <h3 className="d-flex align-center gap-10">
                            <span className="font-24">🛠️</span> Available Tools
                        </h3>
                        <div className="tool-stats d-flex gap-16">
                            <div className="text-center">
                                <p className="font-12 text-secondary">Active</p>
                                <p className="font-18 font-700">12</p>
                            </div>
                            <div className="text-center">
                                <p className="font-12 text-secondary">Latency</p>
                                <p className="font-18 font-700 text-accent">45ms</p>
                            </div>
                        </div>
                    </div>

                    <div className="tools-list d-flex flex-col gap-12">
                        {TOOLS.map((tool, idx) => (
                            <div key={idx} className="glass-card p-16 d-flex justify-between align-center hover-glow transition-all">
                                <div>
                                    <h4 className="m-b-4">{tool.name}</h4>
                                    <p className="font-13 text-secondary">{tool.description}</p>
                                </div>
                                <div className="d-flex align-center gap-16">
                                    <span className={`status-indicator ${tool.status === 'active' ? 'bg-accent' : 'bg-secondary'}`} />
                                    <button className="glass-card p-6-12 font-12 opacity-70 hover-opacity-100">Details</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                <aside className="grid-span-4 d-flex flex-col gap-24">
                    <section className="glass-card bg-accent-soft p-20 border-accent-blur">
                        <h3 className="m-b-16 d-flex align-center gap-10">
                            <span className="font-24">⚡</span> Real-time Performance
                        </h3>
                        <div className="m-b-20">
                            <div className="d-flex justify-between m-b-8 font-13">
                                <span>CPU Usage</span>
                                <span className="text-accent">14%</span>
                            </div>
                            <div className="bg-secondary p-2-4 rounded-full">
                                <div className="bg-accent h-4 rounded-full w-15p" />
                            </div>
                        </div>
                        <div>
                            <div className="d-flex justify-between m-b-8 font-13">
                                <span>Memory</span>
                                <span>420MB</span>
                            </div>
                            <div className="bg-secondary p-2-4 rounded-full">
                                <div className="bg-white h-4 rounded-full w-35p" />
                            </div>
                        </div>
                    </section>

                    <section className="glass-card flex-1">
                        <h3 className="m-b-16">Registry Status</h3>
                        <div className="d-flex flex-col gap-16">
                            <div className="d-flex align-center gap-12">
                                <div className="p-8 glass-card bg-accent-glow">
                                    🌐
                                </div>
                                <div>
                                    <p className="font-14 font-600">Global Hub Connected</p>
                                    <p className="font-12 text-secondary">Last sync: 2m ago</p>
                                </div>
                            </div>
                            <div className="d-flex align-center gap-12">
                                <div className="p-8 glass-card">
                                    🔒
                                </div>
                                <div>
                                    <p className="font-14 font-600">Security Layers Active</p>
                                    <p className="font-12 text-secondary">E2E Encryption verified</p>
                                </div>
                            </div>
                        </div>
                    </section>
                </aside>
            </div>
        </div>
    );
};

export default ToolsPage;
