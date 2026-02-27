import React, { useState, useEffect, useRef } from 'react';
import { Send, Terminal, Sparkles, Activity, Zap, Cpu, ArrowRight, ShieldCheck, Clock, Sun, Lightbulb, Bell } from 'lucide-react';

interface TraceLog {
  id: string;
  type: 'thought' | 'action' | 'observation' | 'system';
  content: string;
  timestamp: string;
}

interface ActiveWidget {
  id: string;
  type: 'timer' | 'weather' | 'iot';
  label: string;
  value: string;
  expiry?: number;
}

const InteractionLab: React.FC = () => {
  const [input, setInput] = useState('');
  const [trace, setTrace] = useState<TraceLog[]>([]);
  const [widgets, setWidgets] = useState<ActiveWidget[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const traceEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    traceEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [trace]);

  const [currentTime, setCurrentTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setCurrentTime(now);
      setWidgets(prev => prev.filter(w => !w.expiry || w.expiry > now));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const addTrace = (type: TraceLog['type'], content: string) => {
    const newLog: TraceLog = {
      id: Math.random().toString(36).substr(2, 9),
      type,
      content,
      timestamp: new Date().toLocaleTimeString(),
    };
    setTrace(prev => [...prev, newLog]);
  };

  const handleInteract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userText = input.toLowerCase();
    setInput('');
    setIsProcessing(true);

    addTrace('system', `Interaction initiated: "${userText}"`);

    // Simulated Alexa Logic
    setTimeout(() => {
      addTrace('thought', `Classifying domestic intent for: ${userText}`);

      if (userText.includes('timer')) {
        const seconds = 60; // Mock parsing
        addTrace('action', `manage_domestic_utility(action='set', type='timer', value=${seconds}, label='Coffee')`);
        setTimeout(() => {
          addTrace('observation', `Timer set for ${seconds}s.`);
          setWidgets(prev => [...prev, {
            id: Math.random().toString(),
            type: 'timer',
            label: 'Coffee Timer',
            value: `${seconds}s`,
            expiry: Date.now() + seconds * 1000
          }]);
          setIsProcessing(false);
        }, 800);
      }
      else if (userText.includes('weather')) {
        addTrace('action', "manage_domestic_utility(action='query', type='weather', label='Vienna')");
        setTimeout(() => {
          addTrace('observation', "Vienna: 21°C, Cloudy with a chance of data.");
          setWidgets(prev => [...prev.filter(w => w.type !== 'weather'), {
            id: 'weather-vienna',
            type: 'weather',
            label: 'Vienna',
            value: '21°C / Cloudy'
          }]);
          setIsProcessing(false);
        }, 800);
      }
      else if (userText.includes('light')) {
        const state = userText.includes('on') ? 'on' : 'off';
        addTrace('action', `trigger_action(action_type='light_${state}', params={"room": "living_room"})`);
        setTimeout(() => {
          addTrace('observation', `Living Room light successfully turned ${state}.`);
          setIsProcessing(false);
        }, 800);
      }
      else {
        addTrace('thought', "General intent. Dispatching to EVI session.");
        setTimeout(() => {
          addTrace('system', "EVI Session initialized for continuous dialogue.");
          setIsProcessing(false);
        }, 800);
      }
    }, 500);
  };

  return (
    <div className="h-full space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Top Section: Header Card */}
      <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-3xl p-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="bg-indigo-600 p-3 rounded-2xl text-white shadow-lg">
            <Cpu className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-black text-white tracking-tight">Interaction Lab</h1>
            <p className="text-slate-400 font-medium">Mini-Alexa Gateway & Agentic Trace Monitor</p>
          </div>
        </div>
        <div className="flex gap-4">
          <div className="bg-slate-800/50 px-4 py-2 rounded-xl border border-slate-700 flex items-center gap-3">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold text-slate-300 uppercase">Trust Standard: SEP-1577</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Main Interaction Card (Spans 8) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col min-h-[450px]">
            <div className="flex items-center gap-3 mb-8">
              <div className="bg-indigo-500/20 p-2 rounded-lg text-indigo-400">
                <Bell className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-white tracking-tight">Active Command Interface</h2>
            </div>

            <div className="flex-1 flex flex-col justify-center items-center text-center space-y-8">
              <div className={`p-10 rounded-full bg-slate-800/50 border border-slate-700/50 ${isProcessing ? 'animate-pulse scale-110 shadow-[0_0_30px_rgba(59,130,246,0.3)]' : ''} transition-all duration-500`}>
                <Zap className={`w-20 h-20 ${isProcessing ? 'text-blue-400 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'text-slate-600'}`} />
              </div>
              <div className="space-y-2">
                <p className="text-2xl font-bold text-white">Domestic Utility Active</p>
                <p className="text-slate-400 text-lg max-w-sm mx-auto">
                  Try "Set 60s timer", "What's the weather?", or "Lights on".
                </p>
              </div>
            </div>

            <form onSubmit={handleInteract} className="mt-10 relative group">
              <div className="absolute inset-0 bg-indigo-500/10 blur-2xl opacity-0 group-focus-within:opacity-100 transition-opacity" />
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Dictate command or query assistant..."
                className="relative w-full bg-slate-950 border border-slate-800 rounded-2xl pl-10 pr-24 py-10 text-white text-2xl font-light focus:border-indigo-500/50 focus:ring-0 transition-all placeholder-slate-700"
              />
              <button
                type="submit"
                disabled={isProcessing}
                className="absolute right-4 top-4 bottom-4 aspect-square flex items-center justify-center bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white rounded-2xl transition-all group shadow-2xl"
              >
                {isProcessing ? <Activity className="w-8 h-8 animate-spin" /> : <ArrowRight className="w-8 h-8 group-hover:translate-x-1 transition-transform" />}
              </button>
            </form>
          </div>

          {/* Trace Card */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-3xl p-6 font-mono text-sm overflow-hidden flex flex-col h-[400px] shadow-inner relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-slate-500" />
                <span className="text-xs uppercase tracking-widest font-black text-slate-500">Cognitive Forensic Trace</span>
              </div>
              <div className="flex gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-slate-800" />
                <div className="w-2.5 h-2.5 rounded-full bg-slate-800" />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-3 custom-scrollbar">
              {trace.length === 0 ? (
                <div className="h-full flex items-center justify-center text-slate-700 italic">
                  Awaiting cognitive signal...
                </div>
              ) : (
                trace.map((log) => (
                  <div key={log.id} className="animate-in fade-in slide-in-from-left-4 duration-500">
                    <div className="flex items-start gap-4 group">
                      <span className="text-slate-600 shrink-0 font-mono">[{log.timestamp}]</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase shrink-0 mt-0.5 border ${log.type === 'thought' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                        log.type === 'action' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                          log.type === 'observation' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                            'bg-slate-800 text-slate-500 border-transparent'
                        }`}>
                        {log.type}
                      </span>
                      <span className={`flex-1 ${log.type === 'action' ? 'text-indigo-200' : log.type === 'thought' ? 'text-blue-200' : 'text-slate-400'}`}>
                        {log.content}
                      </span>
                    </div>
                  </div>
                ))
              )}
              <div ref={traceEndRef} />
            </div>
          </div>
        </div>

        {/* Sidebar Cards (Spans 4) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Widgets Card */}
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-xl">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-6 px-2 flex items-center gap-2">
              <Zap className="w-3 h-3" /> Live Utility Widgets
            </h3>
            <div className="space-y-4">
              {widgets.length === 0 ? (
                <div className="bg-slate-950/50 border border-dashed border-slate-800 rounded-2xl p-10 text-center">
                  <p className="text-slate-700 text-xs font-medium">No active domestic tasks</p>
                </div>
              ) : (
                widgets.map(w => (
                  <div key={w.id} className="bg-slate-950 border border-slate-800 p-5 rounded-2xl animate-in zoom-in-95 duration-300 hover:border-indigo-500/30 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className={`${w.type === 'timer' ? 'bg-amber-500/20 text-amber-400' :
                        w.type === 'weather' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-emerald-500/20 text-emerald-400'
                        } p-3 rounded-xl shadow-inner`}>
                        {w.type === 'timer' ? <Clock className="w-5 h-5" /> :
                          w.type === 'weather' ? <Sun className="w-5 h-5" /> :
                            <Lightbulb className="w-5 h-5" />}
                      </div>
                      <div className="flex-1">
                        <div className="text-[10px] font-black text-slate-600 uppercase tracking-tighter">{w.label}</div>
                        <div className="text-white font-mono text-xl font-black">
                          {w.expiry ? `${Math.max(0, Math.ceil((w.expiry - currentTime) / 1000))}s` : w.value}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Status Card */}
          <div className="bg-gradient-to-br from-indigo-900/20 to-slate-900/20 border border-indigo-500/20 rounded-3xl p-6">
            <h3 className="text-white font-black mb-6 flex items-center gap-2 text-xs uppercase tracking-widest">
              Cognitive Bus Status
            </h3>
            <div className="space-y-4">
              {[
                { label: 'OSC Signal', value: '127.0.0.1:10760', color: 'text-indigo-400' },
                { label: 'Model', value: 'Gemini 3 Pro', color: 'text-blue-400' },
                { label: 'Latency', value: '42ms', color: 'text-emerald-400' },
                { label: 'Wake Word', value: 'Enabled', color: 'text-amber-400' },
              ].map((spec) => (
                <div key={spec.label} className="flex justify-between items-center bg-slate-950/30 p-3 rounded-xl border border-slate-800/10">
                  <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{spec.label}</div>
                  <div className={`text-xs font-mono font-bold ${spec.color}`}>{spec.value}</div>
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
