import {
  Activity,
  CheckCircle2,
  Mic,
  MicOff,
  Settings2,
  ShieldCheck,
  Zap,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { controlWakeWord } from "../api";
import { useBackend } from "../BackendContext";

export const SpeechToText: React.FC = () => {
  const { health } = useBackend();
  const [isPending, setIsPending] = useState(false);
  const [keyword, setKeyword] = useState("hey_jarvis");
  const [sensitivity, setSensitivity] = useState(0.5);
  const [logs, setLogs] = useState<
    {
      id: string;
      time: string;
      msg: string;
      type: "info" | "success" | "error";
    }[]
  >([]);

  const isActive = health?.wake_word_active ?? false;

  const addLog = useCallback(
    (msg: string, type: "info" | "success" | "error" = "info") => {
      const time = new Date().toLocaleTimeString();
      const id = `${Date.now()}-${Math.random()}`;
      setLogs((prev) => [{ id, time, msg, type }, ...prev].slice(0, 50));
    },
    [],
  );

  const handleToggle = async () => {
    setIsPending(true);
    const action = isActive ? "stop" : "start";
    addLog(`Requesting wake-word ${action}...`, "info");

    try {
      const res = await controlWakeWord(action, keyword, sensitivity);
      if (res.success) {
        addLog(
          `Wake-word listener ${res.status === "listening" ? "started" : "stopped"}.`,
          "success",
        );
      } else {
        addLog(`Error: ${res.error}`, "error");
      }
    } catch (_err) {
      addLog("Failed to communicate with backend.", "error");
    } finally {
      setIsPending(false);
    }
  };

  // Sync log on backend status change
  useEffect(() => {
    if (isActive) {
      addLog("System Status: Wake-word listener active.", "success");
    } else {
      addLog("System Status: Wake-word listener standby.", "info");
    }
  }, [isActive, addLog]);

  const KEYWORDS = [
    "alexa",
    "hey_jarvis",
    "hey_mycroft",
    "hey_rhasspy",
    "timers",
    "weather",
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-4xl font-black tracking-tighter text-white mb-2">
            SPEECH SYSTEM
          </h2>
          <p className="text-text-secondary font-medium tracking-wide flex items-center gap-2">
            <ShieldCheck size={16} className="text-accent-purple" />
            V4.0 Wake-Word Detection
          </p>
        </div>

        <button
          type="button"
          disabled={isPending}
          onClick={handleToggle}
          className={`
            relative group px-8 py-4 rounded-2xl font-black tracking-widest uppercase transition-all duration-500 overflow-hidden
            ${
              isActive
                ? "bg-rose-500 text-white shadow-lg shadow-rose-500/20"
                : "bg-accent-purple text-white shadow-lg shadow-accent-purple/20"
            }
            ${isPending ? "opacity-50 cursor-not-allowed" : "hover:scale-105 active:scale-95"}
          `}
        >
          <div className="flex items-center gap-3 relative z-10">
            {isActive ? <MicOff size={20} /> : <Mic size={20} />}
            <span>
              {isPending
                ? "Pending..."
                : isActive
                  ? "Deactivate"
                  : "Activate Listener"}
            </span>
          </div>
          <div
            className={`absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-500`}
          />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Real-time Status Card */}
        <div className="glass-card p-8 flex flex-col justify-between relative overflow-hidden group">
          <div className="relative z-10">
            <div className="flex justify-between items-center mb-6">
              <span className="text-xs font-black uppercase tracking-widest text-text-secondary">
                Listener State
              </span>
              <div
                className={`
                flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter
                ${isActive ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5 text-text-secondary"}
              `}
              >
                <div
                  className={`w-1.5 h-1.5 rounded-full ${isActive ? "bg-emerald-400 animate-pulse" : "bg-text-secondary"}`}
                />
                {isActive ? "Running" : "Standby"}
              </div>
            </div>

            <div className="flex flex-col items-center justify-center py-6">
              <div
                className={`
                w-24 h-24 rounded-full flex items-center justify-center transition-all duration-700
                ${isActive ? "bg-emerald-500/10 scale-110 shadow-[0_0_40px_rgba(16,185,129,0.2)]" : "bg-white/5 scale-100"}
              `}
              >
                <Mic
                  size={40}
                  className={`transition-colors duration-700 ${isActive ? "text-emerald-400" : "text-white/20"}`}
                />
              </div>

              {isActive && (
                <div className="mt-6 flex gap-1 items-end h-8">
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={`bar-${["a", "b", "c", "d", "e", "f", "g", "h"][i]}`}
                      className="w-1 bg-emerald-400/60 rounded-full animate-waveform"
                      style={{
                        height: `${20 + Math.random() * 80}%`,
                        animationDelay: `${i * 0.1}s`,
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Background Highlight */}
          <div
            className={`
            absolute -bottom-24 -right-24 w-64 h-64 rounded-full blur-[100px] transition-opacity duration-1000
            ${isActive ? "bg-emerald-500/20 opacity-100" : "bg-accent-purple/10 opacity-0"}
          `}
          />
        </div>

        {/* Configuration Panel */}
        <div className="lg:col-span-2 glass-card p-8">
          <div className="flex items-center gap-3 mb-8">
            <Settings2 size={18} className="text-accent-purple" />
            <h3 className="text-lg font-black tracking-tight text-white uppercase">
              Engine Parameters
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            <div className="space-y-4">
              <label
                htmlFor="wake-keyword-selector"
                className="text-xs font-black uppercase tracking-widest text-text-secondary flex justify-between"
              >
                Wake Keyword
                <span className="text-accent-purple font-mono lowercase">
                  pvporcupine/4.x
                </span>
              </label>
              <div className="grid grid-cols-2 gap-2 max-h-[220px] overflow-y-auto custom-scrollbar pr-2">
                {KEYWORDS.map((k) => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setKeyword(k)}
                    className={`
                      px-4 py-3 rounded-xl text-xs font-bold transition-all border
                      ${
                        keyword === k
                          ? "bg-accent-purple/20 border-accent-purple text-white"
                          : "bg-white/[0.03] border-white/5 text-text-secondary hover:bg-white/5 hover:text-white"
                      }
                    `}
                  >
                    {k}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-8">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label
                    htmlFor="sensitivity-slider"
                    className="text-xs font-black uppercase tracking-widest text-text-secondary"
                  >
                    Sensitivity
                  </label>
                  <span className="text-sm font-mono font-bold text-accent-purple">
                    {(sensitivity * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  id="sensitivity-slider"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={sensitivity}
                  onChange={(e) => setSensitivity(parseFloat(e.target.value))}
                  className="w-full accent-accent-purple"
                />
                <div className="flex justify-between text-[10px] font-black tracking-widest text-text-secondary opacity-50">
                  <span>LO-CAL</span>
                  <span>HIGH-SENS</span>
                </div>
              </div>

              <div className="bg-white/[0.03] rounded-2xl p-6 border border-white/5 space-y-3">
                <div className="flex items-center gap-3 text-xs font-black text-white/70 uppercase tracking-widest">
                  <Zap size={14} className="text-amber-400" />
                  Performance Note
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">
                  The local engine runs with{" "}
                  <span className="text-white font-bold">&lt;15ms</span>{" "}
                  latency. Increasing sensitivity improves recall but may
                  increase false positives in noisy environments.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Console / Event Log */}
        <div className="lg:col-span-3 glass-card p-0 flex flex-col h-[300px] overflow-hidden">
          <div className="px-8 py-5 border-b border-white/5 flex justify-between items-center bg-white/[0.01]">
            <div className="flex items-center gap-3">
              <Activity size={18} className="text-accent-purple" />
              <h3 className="text-sm font-black tracking-widest text-white uppercase">
                Events
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setLogs([])}
              className="text-[10px] font-black uppercase text-text-secondary hover:text-white transition-colors"
            >
              Clear Log
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-8 font-mono text-xs space-y-3 custom-scrollbar">
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center opacity-20">
                <Activity size={32} className="mb-4" />
                <p className="font-black tracking-widest uppercase text-center">
                  Awaiting Events
                </p>
              </div>
            ) : (
              logs.map((log) => (
                <div
                  key={log.id}
                  className="flex gap-4 animate-in fade-in slide-in-from-left-4 duration-300"
                >
                  <span className="text-text-secondary opacity-40 shrink-0">
                    [{log.time}]
                  </span>
                  <span
                    className={`
                    font-bold
                    ${log.type === "success" ? "text-emerald-400" : log.type === "error" ? "text-rose-500" : "text-white/80"}
                  `}
                  >
                    {log.type === "success" && (
                      <CheckCircle2 size={12} className="inline mr-2 -mt-0.5" />
                    )}
                    {log.msg}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
