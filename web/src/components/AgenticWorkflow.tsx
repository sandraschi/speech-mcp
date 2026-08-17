import { Activity, AlertCircle, Play, Target } from "lucide-react";
import type React from "react";
import { useState } from "react";

import { BACKEND } from "../api";

interface TraceStep {
  step: number;
  tool: string;
  status: string;
}

interface OrchestrationResult {
  goal: string;
  status: string;
  message?: string;
  error?: string;
  error_type?: string;
  success?: boolean;
  suggestions?: string[];
  trace?: TraceStep[];
}

const AgenticWorkflow: React.FC = () => {
  const [goal, setGoal] = useState("");
  const [result, setResult] = useState<OrchestrationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExecute = async () => {
    const g =
      goal.trim() ||
      "Synthesize a calming voice response for the current emotional state";
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${BACKEND}/api/v1/agentic`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal: g }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="glass-card p-10 flex flex-col md:flex-row items-center justify-between gap-6 accent-glow">
        <div className="flex items-center gap-6">
          <div className="bg-accent-blue/20 p-5 rounded-2xl border border-accent-blue/30">
            <Target className="text-accent-blue w-10 h-10" />
          </div>
          <div>
            <h1 className="text-4xl font-black tracking-tighter text-white uppercase">
              Agentic Orchestration
            </h1>
            <p className="text-text-secondary text-sm font-bold uppercase tracking-widest opacity-60">
              Agentic workflow via MCP sampling
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-full text-[10px] font-black uppercase tracking-widest text-text-secondary">
            FastMCP 3.x
          </div>
          <div className="px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-full text-[10px] font-black uppercase tracking-widest text-amber-500">
            REST dispatch requires MCP client
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Workflow Designer */}
        <div className="glass-card p-8 space-y-8 shadow-2xl">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-black text-white uppercase tracking-tighter">
              Orchestration Goal
            </h3>
          </div>

          <div className="space-y-4">
            <label
              htmlFor="orchestration-goal"
              className="text-[10px] font-black text-text-secondary uppercase tracking-widest opacity-50"
            >
              Describe mission objective
            </label>
            <textarea
              id="orchestration-goal"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Synthesize a calming voice response for the current emotional state"
              title="Mission goal"
              rows={4}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-4 text-white focus:border-accent-blue/50 outline-none transition-all resize-none text-sm"
            />
          </div>

          {/* Static workflow visualization */}
          <div className="space-y-4 relative">
            <div className="absolute left-6 top-8 bottom-8 w-px bg-white/10" />
            <WorkflowStep
              index={1}
              title="Goal Interpretation"
              status={result?.success === true ? "completed" : "pending"}
              tool="agentic_conversation_workflow"
            />
            <WorkflowStep
              index={2}
              title="Context Retrieval"
              status={result?.success === true ? "completed" : "pending"}
              tool="search_docs"
            />
            <WorkflowStep
              index={3}
              title="Prosodic Synthesis"
              status={result?.success === true ? "completed" : "pending"}
              tool="text_to_speech"
            />
          </div>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl flex items-center gap-3 text-rose-400 text-xs font-bold">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleExecute}
            disabled={loading}
            className="w-full btn-primary py-5 mt-4 group flex items-center justify-center gap-3"
          >
            {loading ? (
              <Activity size={18} className="animate-spin" />
            ) : (
              <Play
                size={18}
                className="group-hover:translate-x-1 transition-transform"
              />
            )}
            {loading ? "Orchestrating..." : "Execute Orchestration"}
          </button>
        </div>

        {/* Result / Status */}
        <div className="space-y-8">
          <div className="glass-card p-8 bg-accent-blue/5 overflow-hidden relative">
            <div className="absolute top-0 right-0 w-32 h-32 bg-accent-blue/10 blur-[100px] rounded-full -mr-16 -mt-16" />
            <h3 className="text-xl font-black text-white uppercase tracking-tighter mb-6">
              Trace Buffer
            </h3>
            <div className="font-mono text-[11px] space-y-3">
              {result ? (
                <>
                  <div className="flex gap-3">
                    <span className="text-emerald-500 font-black w-12 shrink-0">
                      GOAL
                    </span>
                    <span className="text-white/80">{result.goal}</span>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-accent-blue font-black w-12 shrink-0">
                      STATUS
                    </span>
                    <span className="text-white/80">
                      {result.success
                        ? "dispatched"
                        : (result.status ?? "unavailable")}
                    </span>
                  </div>
                  {result.error && (
                    <div className="flex gap-3">
                      <span className="text-rose-500 font-black w-12 shrink-0">
                        ERROR
                      </span>
                      <span className="text-rose-400">{result.error}</span>
                    </div>
                  )}
                  {result.suggestions?.map((s) => (
                    <div key={s} className="flex gap-3">
                      <span className="text-text-secondary opacity-40 w-12 shrink-0">
                        NEXT
                      </span>
                      <span className="text-white/50">{s}</span>
                    </div>
                  ))}
                  {result.trace?.map((step) => (
                    <div key={step.step} className="flex gap-3">
                      <span className="text-accent-purple font-black w-12 shrink-0">
                        S{step.step}
                      </span>
                      <span className="text-white/60">
                        <span className="text-white font-black">
                          {step.tool}
                        </span>{" "}
                        → {step.status}
                      </span>
                    </div>
                  ))}
                  {result.message && (
                    <div className="flex gap-3 mt-2 pt-2 border-t border-white/10">
                      <span className="text-text-secondary opacity-40 w-12 shrink-0">
                        MSG
                      </span>
                      <span className="text-white/50 italic">
                        {result.message}
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="flex gap-3">
                    <span className="text-text-secondary opacity-30 w-12 shrink-0">
                      idle
                    </span>
                    <span className="text-white/30">
                      Awaiting orchestration dispatch...
                    </span>
                  </div>
                  <div className="flex gap-3 animate-pulse">
                    <span className="text-text-secondary opacity-30 w-12 shrink-0">
                      ...
                    </span>
                    <span className="text-accent-blue/30 italic font-bold">
                      Set a goal and click Execute
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const WorkflowStep = ({
  index,
  title,
  status,
  tool,
}: {
  index: number;
  title: string;
  status: "completed" | "active" | "pending";
  tool: string;
}) => (
  <div
    className={`glass-card p-5 pl-12 flex items-center gap-6 border-l-4 transition-all ${
      status === "completed"
        ? "border-emerald-500/50 bg-emerald-500/5"
        : status === "active"
          ? "border-accent-blue bg-accent-blue/10"
          : "border-white/5 opacity-50"
    }`}
  >
    <div
      className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-black shrink-0 ${
        status === "completed"
          ? "bg-emerald-500 text-white"
          : status === "active"
            ? "bg-accent-blue text-white animate-pulse"
            : "bg-white/10 text-text-secondary"
      }`}
    >
      {index}
    </div>
    <div className="flex-1">
      <h4 className="font-black text-sm text-white uppercase tracking-tight">
        {title}
      </h4>
      <div className="text-[9px] font-mono text-text-secondary uppercase tracking-[0.2em] opacity-40">
        {tool}
      </div>
    </div>
  </div>
);

export default AgenticWorkflow;
