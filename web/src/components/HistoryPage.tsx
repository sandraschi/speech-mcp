import React from 'react';
import { Clock, Download, CheckCircle, AlertCircle, FileText, Search } from 'lucide-react';

interface HistoryItem {
    id: string;
    type: 'tts' | 'clone' | 'evi';
    content: string;
    timestamp: string;
    status: 'success' | 'failed' | 'processing';
    provider: string;
}

const HISTORY_DATA: HistoryItem[] = [
    { id: '1', type: 'tts', content: "Hello, this is a test of the neural synthesis engine.", timestamp: '2026-02-27 14:30', status: 'success', provider: 'Hume EVI' },
    { id: '2', type: 'clone', content: "Voice Clone: Sandra Prototype", timestamp: '2026-02-27 12:15', status: 'success', provider: 'ElevenLabs' },
    { id: '3', type: 'evi', content: "Session: Emotional Analysis 001", timestamp: '2026-02-27 11:00', status: 'success', provider: 'Hume AI' },
    { id: '4', type: 'tts', content: "Oskar Werner induction attempt.", timestamp: '2026-02-27 09:45', status: 'failed', provider: 'ElevenLabs' },
];

const HistoryPage: React.FC = () => {
    return (
        <div className="h-full space-y-8 animate-in fade-in duration-700">
            {/* Header Card */}
            <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-3xl p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 blur-[100px] rounded-full -mr-32 -mt-32" />
                <div className="relative flex items-center gap-6">
                    <div className="bg-indigo-600 p-4 rounded-3xl shadow-[0_0_20px_rgba(79,70,229,0.3)]">
                        <Clock className="text-white w-10 h-10" />
                    </div>
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">Cognitive History</h1>
                        <p className="text-slate-400 mt-1 font-medium text-lg">Archived Neural Interactions & Forensic Trace</p>
                    </div>
                </div>

                <div className="relative w-full md:w-96">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Search forensic logs..."
                        className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-12 pr-4 py-4 text-white focus:border-indigo-500/50 focus:ring-0 transition-all placeholder-slate-600"
                    />
                </div>
            </div>

            {/* History Table */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] overflow-hidden shadow-2xl">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-slate-800 bg-slate-950/50">
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Event</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Cognitive Content</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Metadata</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Status</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {HISTORY_DATA.map((item) => (
                            <tr key={item.id} className="group hover:bg-slate-800/20 transition-colors">
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${item.type === 'tts' ? 'bg-blue-500/10 text-blue-400' :
                                            item.type === 'clone' ? 'bg-purple-500/10 text-purple-400' :
                                                'bg-emerald-500/10 text-emerald-400'
                                            }`}>
                                            {item.type === 'tts' ? <FileText className="w-4 h-4" /> :
                                                item.type === 'clone' ? <Download className="w-4 h-4" /> :
                                                    <Clock className="w-4 h-4" />}
                                        </div>
                                        <span className="text-xs font-bold text-white uppercase tracking-tight">{item.type}</span>
                                    </div>
                                </td>
                                <td className="px-8 py-6">
                                    <p className="text-slate-300 text-sm font-medium line-clamp-1">{item.content}</p>
                                </td>
                                <td className="px-8 py-6">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-slate-200 font-mono">{item.timestamp}</span>
                                        <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{item.provider}</span>
                                    </div>
                                </td>
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-2">
                                        {item.status === 'success' ? (
                                            <CheckCircle className="w-4 h-4 text-emerald-500" />
                                        ) : item.status === 'failed' ? (
                                            <AlertCircle className="w-4 h-4 text-rose-500" />
                                        ) : (
                                            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                                        )}
                                        <span className={`text-[10px] font-black uppercase tracking-widest ${item.status === 'success' ? 'text-emerald-500' :
                                            item.status === 'failed' ? 'text-rose-500' : 'text-indigo-500'
                                            }`}>{item.status}</span>
                                    </div>
                                </td>
                                <td className="px-8 py-6 text-right">
                                    <button className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-all" title="Download interaction trace">
                                        <Download className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Footer Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: 'Total Interactions', value: '1,284', color: 'text-indigo-400' },
                    { label: 'Synthesis Success', value: '99.4%', color: 'text-emerald-400' },
                    { label: 'Storage Used', value: '4.2 GB', color: 'text-blue-400' },
                ].map((stat) => (
                    <div key={stat.label} className="bg-slate-900/30 border border-slate-800 p-6 rounded-3xl flex justify-between items-center">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</span>
                        <span className={`text-xl font-mono font-black ${stat.color}`}>{stat.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default HistoryPage;
