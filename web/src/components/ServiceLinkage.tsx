import React, { useState } from 'react';
import { ExternalLink, Search, Cpu, Globe, Zap, Box, Shield, Activity, LayoutGrid } from 'lucide-react';

interface Service {
    id: string;
    label: string;
    port: number;
    repo_path: string;
    tags: string[];
}

const SERVICES: Service[] = [
    { id: 'virtualization-mcp', label: 'Virtualization MCP', port: 10700, repo_path: 'D:/Dev/repos/virtualization-mcp', tags: ['frontend', 'sota'] },
    { id: 'robotics-mcp', label: 'Robotics MCP', port: 10706, repo_path: 'D:/Dev/repos/robotics-mcp', tags: ['frontend', 'sota'] },
    { id: 'devices-mcp', label: 'Devices MCP (Tapo/Ring)', port: 10716, repo_path: 'D:/Dev/repos/devices-mcp', tags: ['infra', 'sota'] },
    { id: 'filesystem-mcp-frontend', label: 'Filesystem MCP', port: 10743, repo_path: 'D:/Dev/repos/filesystem-mcp', tags: ['frontend', 'sota'] },
    { id: 'windows-operations-mcp-frontend', label: 'Windows Operations', port: 10749, repo_path: 'D:/Dev/repos/windows-operations-mcp', tags: ['frontend', 'sota'] },
    { id: 'resolume-mcp', label: 'Resolume VJ MCP', port: 10770, repo_path: 'D:/Dev/repos/resolume-mcp', tags: ['frontend', 'sota', 'media'] },
    { id: 'reaper-mcp', label: 'Reaper MCP', port: 10796, repo_path: 'D:/Dev/repos/reaper-mcp', tags: ['frontend', 'sota'] },
    { id: 'obs-mcp-frontend', label: 'OBS Control', port: 10818, repo_path: 'D:/Dev/repos/obs-mcp', tags: ['frontend', 'media', 'sota'] },
    { id: 'local-llm-mcp-frontend', label: 'Local LLM Hub', port: 10832, repo_path: 'D:/Dev/repos/local-llm-mcp', tags: ['frontend', 'ai', 'sota'] },
    { id: 'home-assistant-mcp-frontend', label: 'Home Assistant', port: 10834, repo_path: 'D:/Dev/repos/home-assistant-mcp', tags: ['frontend', 'smart-home', 'sota'] },
    { id: 'advanced-memory-mcp-frontend', label: 'Advanced Memory', port: 10704, repo_path: 'D:/Dev/repos/advanced-memory-mcp', tags: ['frontend', 'knowledge', 'sota'] },
    { id: 'mcp-federation-hub', label: 'Fleet Command Hub', port: 10856, repo_path: 'D:/Dev/repos/mcp-federation-hub', tags: ['frontend', 'command', 'sota'] },
];

const ServiceLinkage: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState('');

    const filteredServices = SERVICES.filter(s =>
        s.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="h-full space-y-8 animate-in fade-in duration-700">
            {/* Header Card */}
            <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-3xl p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 blur-[100px] rounded-full -mr-32 -mt-32" />
                <div className="relative flex items-center gap-6">
                    <div className="bg-indigo-600 p-4 rounded-3xl shadow-[0_0_20px_rgba(79,70,229,0.3)]">
                        <LayoutGrid className="text-white w-10 h-10" />
                    </div>
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">Apps Hub</h1>
                        <p className="text-slate-400 mt-1 font-medium text-lg">Central Fleet Discovery & Cross-Link Navigation</p>
                    </div>
                </div>

                <div className="relative w-full md:w-96">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Search services or tags..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-12 pr-4 py-4 text-white focus:border-indigo-500/50 focus:ring-0 transition-all placeholder-slate-600"
                    />
                </div>
            </div>

            {/* Grid of Services */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredServices.map((service) => (
                    <a
                        key={service.id}
                        href={`http://localhost:${service.port}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 hover:bg-slate-900/80 transition-all duration-300 flex flex-col justify-between min-h-[220px] shadow-lg hover:shadow-indigo-500/10 hover:-translate-y-1"
                    >
                        <div className="space-y-4">
                            <div className="flex justify-between items-start">
                                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 group-hover:border-indigo-500/30 transition-colors">
                                    {service.tags.includes('media') ? <Globe className="w-6 h-6 text-blue-400" /> :
                                        service.tags.includes('ai') ? <Cpu className="w-6 h-6 text-purple-400" /> :
                                            service.tags.includes('infra') ? <Shield className="w-6 h-6 text-emerald-400" /> :
                                                <Box className="w-6 h-6 text-indigo-400" />}
                                </div>
                                <div className="flex items-center gap-1.5 bg-slate-950/50 px-3 py-1 rounded-full border border-slate-800">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Port {service.port}</span>
                                </div>
                            </div>

                            <div>
                                <h3 className="text-xl font-bold text-white group-hover:text-indigo-400 transition-colors">{service.label}</h3>
                                <div className="flex flex-wrap gap-2 mt-3">
                                    {service.tags.map(tag => (
                                        <span key={tag} className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md bg-slate-950 text-slate-500 border border-slate-800 group-hover:border-indigo-500/20">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="mt-6 flex items-center justify-between">
                            <span className="text-xs font-medium text-slate-600 truncate max-w-[180px]">{service.repo_path.split('/').pop()}</span>
                            <div className="bg-indigo-600/10 text-indigo-400 p-2 rounded-xl group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-sm">
                                <ExternalLink className="w-4 h-4" />
                            </div>
                        </div>
                    </a>
                ))}
            </div>

            {/* Quick Actions Card */}
            <div className="bg-gradient-to-br from-indigo-950/30 to-slate-950/30 border border-indigo-500/10 rounded-[2.5rem] p-8 flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="flex items-center gap-6">
                    <div className="bg-white/5 p-4 rounded-3xl backdrop-blur-md">
                        <Activity className="text-indigo-400 w-8 h-8" />
                    </div>
                    <div>
                        <h4 className="text-white font-bold text-xl">Fleet Command Integration</h4>
                        <p className="text-slate-500 text-sm">Cross-link protocol SEP-1577 v1.2 active for all local substrate webapps.</p>
                    </div>
                </div>
                <div className="flex gap-4">
                    <div className="bg-slate-950/50 px-6 py-3 rounded-2xl border border-slate-800 flex flex-col items-center">
                        <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">Active Peers</span>
                        <span className="text-white font-mono font-black text-xl">{SERVICES.length}</span>
                    </div>
                    <div className="bg-slate-950/50 px-6 py-3 rounded-2xl border border-slate-800 flex flex-col items-center">
                        <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-1">Core Mesh</span>
                        <span className="text-white font-mono font-black text-xl">SOTA</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ServiceLinkage;
