import { Activity, BarChart3 } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { BACKEND } from "../api";

interface LogEntry {
  time: string;
  level: "INFO" | "DEBUG" | "WARN" | "ERROR" | "SUCCESS";
  context: string;
  msg: string;
}

const SystemLogs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [levelFilter, setLevelFilter] = useState<string>("ALL");
  const [searchText, setSearchText] = useState("");
  const [connected, setConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const wsUrl = BACKEND.replace(/^http/, "ws") + "/ws/logs";
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const newLog = JSON.parse(event.data);
      setLogs((prev: LogEntry[]) => [...prev.slice(-99), newLog]);
    };
    ws.onclose = () => setConnected(false);
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const filteredLogs = logs.filter((log: LogEntry) => {
    if (levelFilter !== "ALL" && log.level !== levelFilter) return false;
    if (!searchText.trim()) return true;
    const q = searchText.toLowerCase();
    return [log.time, log.level, log.context, log.msg].some((s) =>
      String(s).toLowerCase().includes(q),
    );
  });

  const exportLogs = () => {
    const text = filteredLogs
      .map((l) => `[${l.time}] ${l.level} [${l.context}] ${l.msg}`)
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `speech-mcp-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white uppercase tracking-tighter">
            System Logs
          </h1>
          <p className="text-text-secondary text-sm mt-1 uppercase tracking-widest font-bold opacity-60">
            Real-time substrate telemetry
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="bg-white/[0.03] border border-white/5 rounded-lg px-3 py-1.5 text-xs text-white placeholder-white/30 outline-none focus:border-accent-purple/50 w-40 font-mono"
          />
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${connected ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : "bg-rose-500/10 border-rose-500/20 text-rose-500"} text-xs font-black uppercase tracking-widest`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`}
            />
            {connected ? "Live" : "Offline"}
          </div>
          <select
            title="Log Level Filter"
            className="bg-white/[0.03] border border-white/5 rounded-lg px-3 py-1.5 text-xs text-text-secondary outline-none focus:border-accent-purple/50 transition-all font-bold uppercase tracking-wider cursor-pointer"
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
          >
            <option value="ALL">All Levels</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warning</option>
            <option value="ERROR">Error</option>
            <option value="DEBUG">Debug</option>
          </select>
          <button
            onClick={exportLogs}
            className="px-3 py-1.5 bg-accent-purple/20 border border-accent-purple/30 text-accent-purple rounded-lg text-xs font-black uppercase tracking-wider hover:bg-accent-purple/30 transition-all"
          >
            Export
          </button>
          <button
            onClick={() => setLogs([])}
            className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/20 text-rose-500 rounded-lg text-xs font-black uppercase tracking-wider hover:bg-rose-500/20 transition-all"
          >
            Clear
          </button>
        </div>
      </header>

      <div className="glass-card flex flex-col h-[600px] overflow-hidden">
        <div className="bg-white/5 p-4 border-b border-white/5 flex items-center gap-4 text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-40">
          <div className="w-20">Timestamp</div>
          <div className="w-20">Level</div>
          <div className="w-24">Context</div>
          <div className="flex-1 text-right md:text-left">Payload</div>
        </div>

        <div
          className="flex-1 overflow-y-auto font-mono text-sm p-2 space-y-0.5 custom-scrollbar"
          ref={scrollRef}
        >
          {filteredLogs.length === 0 ? (
            <div className="h-full flex items-center justify-center opacity-10 uppercase tracking-[0.5em] font-black text-4xl -rotate-12 select-none">
              Standby
            </div>
          ) : (
            filteredLogs.map((log: LogEntry, i: number) => (
              <div
                key={i}
                className="flex gap-4 py-1 px-2 rounded hover:bg-white/[0.03] transition-colors group"
              >
                <span className="text-text-secondary opacity-30 select-none tabular-nums w-20 shrink-0">
                  [{log.time}]
                </span>
                <span
                  className={`font-black w-20 shrink-0 ${
                    log.level === "ERROR"
                      ? "text-rose-500"
                      : log.level === "WARN"
                        ? "text-amber-500"
                        : log.level === "DEBUG"
                          ? "text-accent-blue"
                          : "text-emerald-500"
                  }`}
                >
                  {log.level}
                </span>
                <span className="text-text-secondary opacity-40 lowercase w-24 shrink-0 truncate">
                  [{log.context}]
                </span>
                <span className="text-white opacity-80 group-hover:opacity-100 transition-opacity whitespace-pre-wrap flex-1">
                  {log.msg}
                </span>
              </div>
            ))
          )}
        </div>

        <footer className="p-4 bg-white/[0.02] border-t border-white/5 flex items-center justify-between text-xs font-bold uppercase tracking-widest text-text-secondary opacity-40">
          <div className="flex items-center gap-4">
            <BarChart3 size={12} className="text-accent-blue" />
            <span>Showing {filteredLogs.length} events</span>
          </div>
          <div className="flex items-center gap-4">
            <Activity size={12} className="text-emerald-500" />
            <span>Monitoring: Prometheus</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default SystemLogs;
