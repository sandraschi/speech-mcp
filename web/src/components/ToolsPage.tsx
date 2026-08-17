import { Activity, ChevronRight, Cpu, Zap } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";

import { BACKEND } from "../api";

interface Tool {
  name: string;
  description: string;
}

interface HealthData {
  status: string;
  version: string;
  providers: { hume: boolean; elevenlabs: boolean; windows: boolean };
  active_timers: number;
}

interface ToolsResponse {
  success: boolean;
  tools: Tool[];
  count: number;
}

const ToolsPage: React.FC = () => {
  const [tools, setTools] = useState<Tool[] | null>(null);
  const [toolsError, setToolsError] = useState(false);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    fetch(`${BACKEND}/api/tools`)
      .then((r) => r.json())
      .then((data: ToolsResponse) => {
        if (data.success) setTools(data.tools);
        else setToolsError(true);
      })
      .catch(() => setToolsError(true));
    fetch(`${BACKEND}/api/v1/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealthError(true));
  }, []);

  return (
    <div className="space-y-6" data-testid="tools-page">
      <header>
        <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
          Tools
        </h1>
        <p className="text-sm text-white/50 uppercase tracking-widest mt-1">
          MCP tool registry
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tool list — 2/3 width */}
        <div
          className="lg:col-span-2 glass-card p-6 space-y-3"
          data-testid="tool-list"
        >
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2">
              🛠️ Available Tools
            </h2>
            <span className="text-xs font-black text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full uppercase tracking-widest">
              {tools ? `${tools.length} Registered` : "—"}
            </span>
          </div>

          {toolsError ? (
            <div className="text-xs text-rose-400 font-bold">
              Tool registry unreachable — backend offline or /api/tools missing.
            </div>
          ) : tools === null ? (
            <div className="text-xs text-white/30 animate-pulse">
              Loading tool registry…
            </div>
          ) : tools.length === 0 ? (
            <div className="text-xs text-white/30">No tools registered.</div>
          ) : (
            tools.map((tool) => (
              <div
                key={tool.name}
                className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/10 hover:border-white/20 hover:bg-white/[0.05] transition-all group"
              >
                <div className="w-2 h-2 rounded-full flex-shrink-0 bg-emerald-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-mono font-bold text-sm text-white truncate">
                    {tool.name}
                  </div>
                  <div className="text-xs text-white/50 mt-0.5 leading-snug">
                    {tool.description || "No description"}
                  </div>
                </div>
                <ChevronRight
                  size={14}
                  className="text-white/20 group-hover:text-white/50 flex-shrink-0 transition-colors"
                />
              </div>
            ))
          )}
        </div>

        {/* Sidebar — 1/3 */}
        <div className="space-y-4">
          {/* Health / providers */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-2">
              <Activity size={13} className="text-violet-400" /> Backend Health
            </h3>

            {healthError ? (
              <div className="text-xs text-rose-400 font-bold">
                Backend unreachable
              </div>
            ) : health ? (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/50">Status</span>
                  <span className="text-xs font-black text-emerald-400 uppercase">
                    {health.status}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/50">Version</span>
                  <span className="text-xs font-mono text-white">
                    {health.version}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-white/50">Active Timers</span>
                  <span className="text-xs font-mono text-white">
                    {health.active_timers}
                  </span>
                </div>
                <div className="border-t border-white/5 pt-3 space-y-2">
                  {Object.entries(health.providers).map(([name, ok]) => (
                    <div
                      key={name}
                      className="flex justify-between items-center"
                    >
                      <span className="text-xs text-white/50 capitalize">
                        {name}
                      </span>
                      <span
                        className={`text-[10px] font-black uppercase tracking-wider ${ok ? "text-emerald-400" : "text-white/30"}`}
                      >
                        {ok ? "ready" : "no key"}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-xs text-white/30 animate-pulse">
                Loading…
              </div>
            )}
          </div>

          {/* Perf — honest: no telemetry endpoint exposed */}
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-2">
              <Zap size={13} className="text-amber-400" /> Performance
            </h3>
            <div className="text-xs text-white/40 leading-relaxed">
              Telemetry is not exposed by the backend. Live metrics are not
              available — see System Health for connectivity status.
            </div>
          </div>

          {/* Registry — honest: derived from live tool list */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu size={13} className="text-blue-400" /> Registry
            </h3>
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-xl">🛠️</span>
              <div>
                <div className="text-xs font-bold text-white">MCP Tools</div>
                <div className="text-[10px] text-white/40">
                  {tools === null
                    ? "loading…"
                    : `${tools.length} registered via /api/tools`}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolsPage;
