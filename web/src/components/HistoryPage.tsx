import {
  AlertCircle,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Search,
} from "lucide-react";
import React from "react";
import { BACKEND } from "../api";

interface HistoryItem {
  id: string;
  type: "tts" | "clone" | "evi";
  content: string;
  timestamp: string;
  status: "success" | "failed" | "processing";
  provider: string;
}

const HistoryPage: React.FC = () => {
  const [history, setHistory] = React.useState<HistoryItem[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${BACKEND}/api/v1/history`);
        if (res.ok) {
          const data = await res.json();
          setHistory(data);
        }
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

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
            <h1 className="text-4xl font-black text-white tracking-tighter">
              Cognitive History
            </h1>
            <p className="text-slate-400 mt-1 font-medium text-lg">
              Archived Neural Interactions & Forensic Trace
            </p>
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
            <tr className="border-b border-white/5 bg-white/[0.02]">
              <th className="px-8 py-5 text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                Event
              </th>
              <th className="px-8 py-5 text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                Cognitive Content
              </th>
              <th className="px-8 py-5 text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                Metadata
              </th>
              <th className="px-8 py-5 text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                Status
              </th>
              <th className="px-8 py-5 text-xs font-black text-text-secondary uppercase tracking-widest opacity-40 text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {history.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-8 py-20 text-center">
                  <div className="flex flex-col items-center justify-center opacity-20 uppercase tracking-[0.3em] font-black text-lg">
                    <Clock size={40} className="mb-4" />
                    {loading
                      ? "Synchronizing Substrate..."
                      : "Archival Trace Empty"}
                  </div>
                </td>
              </tr>
            ) : (
              history.map((item) => (
                <tr
                  key={item.id}
                  className="group hover:bg-white/[0.03] transition-colors border-b border-white/[0.02] last:border-0"
                >
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded-lg ${
                          item.type === "tts"
                            ? "bg-accent-blue/10 text-accent-blue"
                            : item.type === "clone"
                              ? "bg-accent-purple/10 text-accent-purple"
                              : "bg-emerald-500/10 text-emerald-400"
                        }`}
                      >
                        {item.type === "tts" || item.type === "clone" ? (
                          <FileText className="w-4 h-4" />
                        ) : (
                          <Clock className="w-4 h-4" />
                        )}
                      </div>
                      <span className="text-xs font-black text-white uppercase tracking-wider">
                        {item.type}
                      </span>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <p className="text-text-secondary text-sm font-bold line-clamp-1">
                      {item.content}
                    </p>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-col">
                      <span className="text-xs text-text-secondary font-mono mb-1">
                        {item.timestamp}
                      </span>
                      <span className="text-xs text-text-secondary font-black uppercase tracking-widest opacity-40">
                        {item.provider}
                      </span>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-2">
                      {item.status === "success" ? (
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                      ) : item.status === "failed" ? (
                        <AlertCircle className="w-4 h-4 text-rose-500" />
                      ) : (
                        <div className="w-4 h-4 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
                      )}
                      <span
                        className={`text-xs font-black uppercase tracking-widest ${
                          item.status === "success"
                            ? "text-emerald-500"
                            : item.status === "failed"
                              ? "text-rose-500"
                              : "text-accent-purple"
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <button
                      className="p-2 text-text-secondary hover:text-white hover:bg-white/10 rounded-lg transition-all"
                      title="Download interaction trace"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            label: "Total Interactions",
            value: "1,284",
            color: "text-indigo-400",
          },
          {
            label: "Synthesis Success",
            value: "99.4%",
            color: "text-emerald-400",
          },
          { label: "Storage Used", value: "4.2 GB", color: "text-blue-400" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="glass-card p-6 flex justify-between items-center bg-white/[0.02]"
          >
            <span className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
              {stat.label}
            </span>
            <span className={`text-xl font-mono font-black ${stat.color}`}>
              {stat.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HistoryPage;
