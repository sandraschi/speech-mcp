import {
  Activity,
  ArrowRight,
  Clock,
  Lightbulb,
  ShieldCheck,
  Sun,
  Terminal,
  Zap,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";

import { BACKEND } from "../api";

interface TraceLog {
  id: string;
  type: "thought" | "action" | "observation" | "system" | "error";
  content: string;
  timestamp: string;
}

interface ActiveWidget {
  id: string;
  type: "timer" | "weather" | "iot";
  label: string;
  value: string;
  expiry?: number;
}

const InteractionLab: React.FC = () => {
  const [input, setInput] = useState("");
  const [trace, setTrace] = useState<TraceLog[]>([]);
  const [widgets, setWidgets] = useState<ActiveWidget[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const traceEndRef = useRef<HTMLDivElement>(null);
  const [currentTime, setCurrentTime] = useState(() => Date.now());

  useEffect(() => {
    traceEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [trace]);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setCurrentTime(now);
      setWidgets((prev) => prev.filter((w) => !w.expiry || w.expiry > now));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const addTrace = (type: TraceLog["type"], content: string) => {
    setTrace((prev) => [
      ...prev.slice(-49),
      {
        id: Math.random().toString(36).substr(2, 9),
        type,
        content,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
  };

  const handleInteract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userText = input.toLowerCase();
    setInput("");
    setIsProcessing(true);
    addTrace("system", `Interaction initiated: "${userText}"`);

    try {
      if (userText.includes("timer")) {
        const match = userText.match(/(\d+)/);
        const seconds = match ? parseInt(match[1]) : 60;
        const label = "Timer";
        addTrace("thought", `Classified intent: timer (${seconds}s)`);
        addTrace(
          "action",
          `POST /api/v1/utility {action:'set', type:'timer', value:${seconds}, label:'${label}'}`,
        );

        const res = await fetch(`${BACKEND}/api/v1/utility`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "set",
            type: "timer",
            value: seconds,
            label,
          }),
        });
        const data = await res.json();
        if (data.success) {
          addTrace(
            "observation",
            `Timer set: ${data.expires_in}s (id: ${data.timer_id})`,
          );
          setWidgets((prev) => [
            ...prev,
            {
              id: data.timer_id,
              type: "timer",
              label,
              value: `${seconds}s`,
              expiry: Date.now() + seconds * 1000,
            },
          ]);
        } else {
          addTrace("error", `Timer failed: ${data.error}`);
        }
      } else if (userText.includes("weather")) {
        addTrace("thought", "Classified intent: weather query");
        addTrace(
          "action",
          `POST /api/v1/utility {action:'query', type:'weather', label:'Vienna'}`,
        );

        const res = await fetch(`${BACKEND}/api/v1/utility`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "query",
            type: "weather",
            label: "Vienna",
          }),
        });
        const data = await res.json();
        addTrace(
          "observation",
          `${data.location}: ${data.temp}, ${data.condition}`,
        );
        setWidgets((prev) => [
          ...prev.filter((w) => w.type !== "weather"),
          {
            id: "weather-vienna",
            type: "weather",
            label: data.location,
            value: `${data.temp} / ${data.condition}`,
          },
        ]);
      } else if (userText.includes("light")) {
        const state = userText.includes("off") ? "off" : "on";
        addTrace("thought", `Classified intent: light control → ${state}`);
        addTrace(
          "action",
          `POST /api/v1/action {action_type:'light_${state}', params:{room:'living_room'}}`,
        );

        const res = await fetch(`${BACKEND}/api/v1/action`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action_type: `light_${state}`,
            params: { room: "living_room" },
          }),
        });
        const data = await res.json();
        addTrace(
          "observation",
          `${data.room} light → ${data.state} (${data.device})`,
        );
        setWidgets((prev) => {
          const filtered = prev.filter((w) => w.type !== "iot");
          return state === "on"
            ? [
                ...filtered,
                {
                  id: "iot-light",
                  type: "iot",
                  label: "Living Room",
                  value: "ON",
                },
              ]
            : filtered;
        });
      } else {
        addTrace(
          "thought",
          "General intent. Dispatching to agentic orchestration.",
        );
        addTrace("action", `POST /api/v1/agentic {goal:'${userText}'}`);

        const res = await fetch(`${BACKEND}/api/v1/agentic`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ goal: userText }),
        });
        const data = await res.json();
        addTrace("observation", `Orchestration dispatched: ${data.message}`);
        data.trace?.forEach(
          (step: { step: number; tool: string; status: string }) => {
            addTrace(
              "action",
              `Step ${step.step}: ${step.tool} → ${step.status}`,
            );
          },
        );
      }
    } catch (err) {
      addTrace(
        "error",
        `Backend unreachable: ${err instanceof Error ? err.message : String(err)}`,
      );
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Interaction Lab
          </h1>
          <p className="text-text-secondary text-sm font-bold uppercase tracking-widest opacity-60">
            High-fidelity domestic orchestration
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-xs font-black uppercase tracking-widest text-emerald-500 flex items-center gap-2">
            <ShieldCheck size={12} />
            Protocol SEP-1577 Active
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Main Interaction Card */}
        <div className="lg:col-span-8 space-y-8">
          <div className="glass-card p-10 flex flex-col min-h-[500px] shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-accent-blue/5 blur-[120px] rounded-full -mr-32 -mt-32" />

            <div className="flex items-center gap-4 mb-12 relative">
              <div className="bg-accent-blue/10 p-3 rounded-xl border border-accent-blue/20 text-accent-blue">
                <Zap size={20} />
              </div>
              <h2 className="text-xl font-black text-white uppercase tracking-tighter">
                Command Interface
              </h2>
            </div>

            <div className="flex-1 flex flex-col justify-center items-center text-center space-y-10 py-10 relative">
              <div
                className={`relative p-12 rounded-full border-2 transition-all duration-700 ${
                  isProcessing
                    ? "border-accent-blue/40 bg-accent-blue/10 scale-110"
                    : "border-white/5 bg-white/[0.02]"
                }`}
              >
                {isProcessing && (
                  <div className="absolute inset-[-10px] rounded-full border border-accent-blue/20 animate-ping opacity-20" />
                )}
                <Zap
                  className={`w-24 h-24 transition-colors duration-700 ${isProcessing ? "text-accent-blue" : "text-white/10"}`}
                />
              </div>
              <div className="space-y-3">
                <p className="text-3xl font-black text-white tracking-tighter uppercase">
                  Substrate Active
                </p>
                <p className="text-text-secondary text-lg max-w-sm mx-auto font-bold opacity-60 uppercase tracking-wide">
                  Try "Set 60s timer", "Weather", "Lights on"
                </p>
              </div>
            </div>

            <form
              onSubmit={handleInteract}
              className="mt-12 relative group/form"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Dictate command..."
                title="Command Input"
                className="relative w-full bg-white/[0.03] border border-white/10 rounded-2xl pl-6 pr-24 py-8 text-white text-2xl font-black focus:border-accent-blue/50 focus:bg-white/[0.05] outline-none transition-all placeholder-white/10 tracking-tight"
              />
              <button
                type="submit"
                disabled={isProcessing}
                title="Execute Command"
                className="absolute right-3 top-3 bottom-3 aspect-square flex items-center justify-center bg-accent-blue hover:bg-accent-blue-hover disabled:bg-white/5 text-white rounded-xl transition-all shadow-xl"
              >
                {isProcessing ? (
                  <Activity className="w-8 h-8 animate-spin" />
                ) : (
                  <ArrowRight className="w-8 h-8" />
                )}
              </button>
            </form>
          </div>

          {/* Trace Card */}
          <div className="glass-card flex flex-col h-[400px] overflow-hidden shadow-xl border-white/5">
            <div className="bg-white/5 p-4 border-b border-white/5 flex items-center justify-between text-xs font-black text-text-secondary uppercase tracking-[0.2em] opacity-40">
              <div className="flex items-center gap-3">
                <Terminal size={14} />
                <span>Cognitive Forensic Trace</span>
              </div>
            </div>

            <div
              className="flex-1 overflow-y-auto space-y-3 p-6 font-mono text-sm"
              ref={traceEndRef}
            >
              {trace.length === 0 ? (
                <div className="h-full flex items-center justify-center text-white/10 uppercase tracking-[0.5em] font-black italic">
                  Awaiting Telemetry
                </div>
              ) : (
                trace.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-4 animate-in fade-in duration-300"
                  >
                    <span className="text-text-secondary opacity-30 select-none tabular-nums w-16 shrink-0 mt-1">
                      [{log.timestamp.split(":").slice(0, 2).join(":")}]
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-[4px] text-xs font-black uppercase shrink-0 mt-0.5 border ${
                        log.type === "thought"
                          ? "bg-accent-blue/10 text-accent-blue border-accent-blue/20"
                          : log.type === "action"
                            ? "bg-accent-purple/10 text-accent-purple border-accent-purple/20"
                            : log.type === "observation"
                              ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                              : log.type === "error"
                                ? "bg-rose-500/10 text-rose-500 border-rose-500/20"
                                : "bg-white/5 text-text-secondary border-transparent"
                      }`}
                    >
                      {log.type}
                    </span>
                    <span
                      className={`flex-1 ${
                        log.type === "action"
                          ? "text-white font-bold"
                          : log.type === "error"
                            ? "text-rose-400"
                            : log.type === "thought"
                              ? "text-text-secondary italic"
                              : "text-text-secondary opacity-70"
                      }`}
                    >
                      {log.content}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-4 space-y-8">
          <div className="glass-card p-8 shadow-xl">
            <div className="flex items-center justify-between mb-8 px-1">
              <h3 className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-60 flex items-center gap-3">
                <Zap size={14} className="text-accent-blue" />
                Live Hub
              </h3>
              <div className="px-2 py-1 bg-accent-blue/10 rounded text-xs font-black text-accent-blue uppercase tracking-widest">
                {widgets.length} Active
              </div>
            </div>

            <div className="space-y-4">
              {widgets.length === 0 ? (
                <div className="bg-white/[0.02] border border-dashed border-white/5 rounded-2xl p-12 text-center">
                  <Activity className="w-8 h-8 text-white/5 mx-auto mb-4" />
                  <p className="text-text-secondary text-xs font-black uppercase tracking-widest opacity-30">
                    Substrate Idle
                  </p>
                </div>
              ) : (
                widgets.map((w) => (
                  <div
                    key={w.id}
                    className="bg-white/[0.03] border border-white/5 p-5 rounded-2xl animate-in zoom-in-95 duration-300"
                  >
                    <div className="flex items-center gap-5">
                      <div
                        className={`${
                          w.type === "timer"
                            ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                            : w.type === "weather"
                              ? "bg-accent-blue/10 text-accent-blue border-accent-blue/20"
                              : "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                        } p-4 rounded-xl border`}
                      >
                        {w.type === "timer" ? (
                          <Clock size={20} />
                        ) : w.type === "weather" ? (
                          <Sun size={20} />
                        ) : (
                          <Lightbulb size={20} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[10px] font-black text-text-secondary uppercase tracking-widest opacity-40 mb-1">
                          {w.label}
                        </div>
                        <div className="text-white font-black text-xl tracking-tighter truncate">
                          {w.expiry
                            ? `${Math.max(0, Math.ceil((w.expiry - currentTime) / 1000))}s`
                            : w.value}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="glass-card p-8 bg-accent-blue/5 border-accent-blue/10 relative overflow-hidden shadow-2xl">
            <h3 className="text-xs font-black text-white uppercase tracking-[0.2em] mb-8 flex items-center gap-2">
              <Activity size={14} className="text-accent-blue" />
              Cognitive Bus
            </h3>
            <div className="space-y-4">
              {[
                {
                  label: "Backend",
                  value: "localhost:10918",
                  status: "online",
                },
                { label: "Stream", value: "/ws/stream", status: "ready" },
                { label: "Logs", value: "/ws/logs", status: "nominal" },
                { label: "Wake Word", value: "Enabled", status: "online" },
              ].map((spec) => (
                <div
                  key={spec.label}
                  className="flex justify-between items-center bg-white/[0.02] p-4 rounded-xl border border-white/5"
                >
                  <div className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                    {spec.label}
                  </div>
                  <div className="text-sm font-black text-white tracking-widest uppercase">
                    {spec.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractionLab;
