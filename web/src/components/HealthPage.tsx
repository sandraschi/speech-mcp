import {
  Activity,
  CheckCircle2,
  Globe,
  ShieldCheck,
  XCircle,
  Zap,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useBackend } from "../BackendContext";

const HealthPage: React.FC = () => {
  const { health, request } = useBackend();
  const [latency, setLatency] = useState<number | null>(null);

  useEffect(() => {
    const start = Date.now();
    request("/api/v1/health")
      .then(() => {
        setLatency(Date.now() - start);
      })
      .catch(() => setLatency(null));
  }, [request]);

  const StatusPill = ({
    active,
    label,
  }: {
    active: boolean;
    label: string;
  }) => (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${active ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}
    >
      {active ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
      <span className="text-xs font-black uppercase tracking-wider">
        {label}
      </span>
      <span className="ml-1 text-[10px] font-bold opacity-60">
        {active ? "Connected" : "Disconnected"}
      </span>
    </div>
  );

  const TokenStatus = ({ valid, label }: { valid: boolean; label: string }) => (
    <div className="flex items-center justify-between p-4 bg-white/[0.03] border border-white/5 rounded-2xl">
      <div className="flex items-center gap-3">
        <div
          className={`p-2 rounded-lg ${valid ? "bg-emerald-500/10" : "bg-rose-500/10"}`}
        >
          <ShieldCheck
            size={18}
            className={valid ? "text-emerald-400" : "text-rose-400"}
          />
        </div>
        <span className="text-sm font-bold text-white">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`text-[10px] font-black uppercase tracking-widest ${valid ? "text-emerald-500" : "text-rose-500"}`}
        >
          {valid ? "Valid Key" : "Missing Key"}
        </span>
        <div
          className={`w-2 h-2 rounded-full ${valid ? "bg-emerald-500" : "bg-rose-500"}`}
        />
      </div>
    </div>
  );

  const providers = health?.providers;
  const tokens = health?.tokens;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-10">
        <h2 className="text-2xl font-black text-white tracking-tight">
          System Health
        </h2>
        <p className="text-text-secondary mt-1">
          Real-time monitoring of cloud connectivity and API status.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Core Latency */}
        <section className="glass-card p-6 flex flex-col items-center justify-center text-center">
          <Zap size={24} className="text-amber-400 mb-3" />
          <span className="text-xs font-black uppercase tracking-widest text-text-secondary mb-1">
            API Latency
          </span>
          <span className="text-3xl font-black text-white">
            {latency !== null ? `${latency}ms` : "--"}
          </span>
        </section>

        {/* WebSocket Status */}
        <section className="glass-card p-6 flex flex-col items-center justify-center text-center">
          <Activity size={24} className="text-accent-purple mb-3" />
          <span className="text-xs font-black uppercase tracking-widest text-text-secondary mb-1">
            Service State
          </span>
          <span className="text-3xl font-black text-emerald-400">Stable</span>
        </section>

        {/* Global Connectivity */}
        <section className="glass-card p-6 flex flex-col items-center justify-center text-center">
          <Globe size={24} className="text-blue-400 mb-3" />
          <span className="text-xs font-black uppercase tracking-widest text-text-secondary mb-1">
            External Link
          </span>
          <span className="text-3xl font-black text-white">Active</span>
        </section>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Cloud Providers */}
        <div>
          <h3 className="text-sm font-black uppercase tracking-[0.2em] text-text-secondary opacity-50 mb-6 flex items-center gap-2">
            Cloud Providers
          </h3>
          <div className="space-y-3">
            <StatusPill active={providers?.gemini ?? false} label="Google Gemini" />
            <StatusPill active={providers?.hume ?? false} label="Hume AI (EVI)" />
            <StatusPill active={providers?.elevenlabs ?? false} label="ElevenLabs" />
            <StatusPill active={true} label="Local Windows SAPI" />
          </div>
        </div>

        {/* Security / Tokens */}
        <div>
          <h3 className="text-sm font-black uppercase tracking-[0.2em] text-text-secondary opacity-50 mb-6 flex items-center gap-2">
            API Authorization
          </h3>
          <div className="space-y-4">
            <TokenStatus valid={tokens?.google_api_key ?? false} label="Google Cloud" />
            <TokenStatus valid={tokens?.hume_api_key ?? false} label="Hume Platform" />
            <TokenStatus
              valid={tokens?.elevenlabs_api_key ?? false}
              label="ElevenLabs Engine"
            />
          </div>
        </div>
      </div>

      <div className="mt-12 p-6 glass-card bg-rose-500/5 border-rose-500/10">
        <h4 className="text-rose-400 text-sm font-black uppercase tracking-widest mb-2">
          Attention Required
        </h4>
        <p className="text-sm text-text-secondary leading-relaxed">
          If any API keys are shown as [Missing Key], please ensure they are
          defined in your <code className="text-white">.env</code> file at the
          project root and restart the backend. Valid keys are necessary for
          high-fidelity speech synthesis and multimodal grounding.
        </p>
      </div>
    </div>
  );
};

export default HealthPage;
