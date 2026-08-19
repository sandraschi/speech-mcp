import {
  BookMarked,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Plus,
  Search,
} from "lucide-react";
import React from "react";
import {
  BACKEND,
  fetchAnalytics,
  fetchMemory,
  fetchMemoryStats,
  type MemoryEpisode,
  storeMemory,
} from "../api";

interface HistoryItem {
  id: string;
  type: string;
  content: string;
  provider: string;
  timestamp: string;
}

const HistoryPage: React.FC = () => {
  const [history, setHistory] = React.useState<HistoryItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [episodes, setEpisodes] = React.useState<MemoryEpisode[]>([]);
  const [memoryQuery, setMemoryQuery] = React.useState("");
  const [memoryText, setMemoryText] = React.useState("");
  const [memoryMsg, setMemoryMsg] = React.useState<string | null>(null);
  const [analytics, setAnalytics] =
    React.useState<Awaited<ReturnType<typeof fetchAnalytics>>>(null);
  const [memoryTotal, setMemoryTotal] = React.useState(0);

  React.useEffect(() => {
    const fetchHistoryData = async () => {
      try {
        const res = await fetch(`${BACKEND}/api/v1/history`);
        if (res.ok) {
          const data = await res.json();
          setHistory(data.reverse());
        }
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistoryData();
    fetchMemory(15).then(setEpisodes);
    fetchAnalytics(24).then(setAnalytics);
    fetchMemoryStats().then((s) => setMemoryTotal(s.total));
  }, []);

  const searchMemory = async (q: string) => {
    setMemoryQuery(q);
    if (!q.trim()) {
      fetchMemory(15).then(setEpisodes);
      return;
    }
    try {
      const res = await fetch(
        `${BACKEND}/api/v1/memory/search?q=${encodeURIComponent(q)}`,
      );
      const data = await res.json();
      setEpisodes(data.results ?? []);
    } catch {
      setEpisodes([]);
    }
  };

  const addNote = async () => {
    const text = memoryText.trim();
    if (!text) return;
    const res = await storeMemory({ text, kind: "note" });
    setMemoryMsg(res.success ? "Note stored." : "Store failed.");
    setMemoryText("");
    fetchMemory(15).then(setEpisodes);
  };

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
              Interaction History
            </h1>
            <p className="text-slate-400 mt-1 font-medium text-lg">
              Past TTS, STT and agent interactions
            </p>
          </div>
        </div>

        <div className="relative w-full md:w-96">
          <label htmlFor="interaction-search" className="sr-only">
            Search interaction logs
          </label>
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-5 h-5" />
          <input
            id="interaction-search"
            type="text"
            placeholder="Search interaction logs..."
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
                Content
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
                    {loading ? "Loading history..." : "Archival Trace Empty"}
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
                      <CheckCircle className="w-4 h-4 text-emerald-500" />
                      <span className="text-xs font-black uppercase tracking-widest text-emerald-500">
                        verified
                      </span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <button
                      type="button"
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

      {/* Voice Memory */}
      <div className="glass-card p-8 bg-white/[0.02]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-accent-purple/10 text-accent-purple">
              <BookMarked size={18} />
            </div>
            <div>
              <h2 className="text-xl font-black text-white tracking-tight">
                Voice Memory
              </h2>
              <p className="text-xs text-text-secondary uppercase tracking-widest">
                Persistent episodic diary - survives restarts
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Search size={14} className="text-white/30" />
            <input
              type="text"
              value={memoryQuery}
              onChange={(e) => searchMemory(e.target.value)}
              placeholder="Search memory..."
              data-testid="memory-search"
              className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-1.5 text-sm focus:border-accent-purple/50 outline-none"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <input
            type="text"
            value={memoryText}
            onChange={(e) => setMemoryText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addNote()}
            placeholder="Quick note to remember..."
            data-testid="memory-input"
            className="flex-1 bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-2 text-sm focus:border-accent-purple/50 outline-none"
          />
          <button
            type="button"
            onClick={addNote}
            data-testid="memory-add"
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-accent-purple/70 hover:bg-accent-purple px-3 py-2 rounded-lg transition-colors"
          >
            <Plus size={13} /> Remember
          </button>
        </div>
        {memoryMsg && (
          <p className="text-xs text-text-secondary mb-4">{memoryMsg}</p>
        )}

        {episodes.length === 0 ? (
          <p className="text-sm text-text-secondary">
            No voice memory yet. Say something, chat, or add a note above.
          </p>
        ) : (
          <div className="space-y-2 max-h-[360px] overflow-y-auto pr-2">
            {episodes.map((ep) => (
              <div
                key={ep.id}
                className="flex items-start gap-3 p-3 bg-white/[0.03] border border-white/5 rounded-xl"
              >
                <span
                  className={`mt-1 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${
                    ep.kind === "tts"
                      ? "bg-accent-blue/20 text-accent-blue"
                      : ep.kind === "stt"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : ep.kind === "chat"
                          ? "bg-accent-purple/20 text-accent-purple"
                          : "bg-white/10 text-white/60"
                  }`}
                >
                  {ep.kind}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/90 leading-snug">
                    {ep.text}
                  </p>
                  <div className="flex gap-3 mt-1 text-[10px] text-text-secondary uppercase tracking-wider font-bold">
                    <span>{ep.ts}</span>
                    {ep.topic && <span>#{ep.topic}</span>}
                    {ep.provider && <span>{ep.provider}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Real telemetry (replaces the old hardcoded footer stats) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 flex justify-between items-center bg-white/[0.02]">
          <span className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
            Analytics calls (24h)
          </span>
          <span className="text-xl font-mono font-black text-indigo-400">
            {analytics ? analytics.total_calls : "—"}
          </span>
        </div>
        <div className="glass-card p-6 flex justify-between items-center bg-white/[0.02]">
          <span className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
            p95 latency
          </span>
          <span className="text-xl font-mono font-black text-emerald-400">
            {analytics
              ? Math.max(
                  ...Object.values(analytics.providers).map(
                    (p) => p.p95_latency_ms ?? 0,
                  ),
                ) > 0
                ? `${Math.max(
                    ...Object.values(analytics.providers).map(
                      (p) => p.p95_latency_ms ?? 0,
                    ),
                  )}ms`
                : "—"
              : "—"}
          </span>
        </div>
        <div className="glass-card p-6 flex justify-between items-center bg-white/[0.02]">
          <span className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
            Memory episodes
          </span>
          <span className="text-xl font-mono font-black text-blue-400">
            {memoryTotal > 0 ? memoryTotal : "—"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;
