import { Clock, Database, Server } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { BackendProvider, useBackend } from "./BackendContext";
import AgenticWorkflow from "./components/AgenticWorkflow";
import AppLayout from "./components/AppLayout";
import CreativeLabs from "./components/CreativeLabs";
import DeviceSettings from "./components/DeviceSettings";
import HealthPage from "./components/HealthPage";
import HelpPage from "./components/HelpPage";
import HistoryPage from "./components/HistoryPage";
import InteractionLab from "./components/InteractionLab";
import SemanticSearch from "./components/SemanticSearch";
import ServiceLinkage from "./components/ServiceLinkage";
import { SpeechToText } from "./components/SpeechToText";
import SystemLogs from "./components/SystemLogs";
import ToolsPage from "./components/ToolsPage";
import VoiceChat from "./components/VoiceChat";
import VoicesPage from "./components/VoicesPage";

const Dashboard: React.FC<{ onNavigate: (page: string) => void }> = ({
  onNavigate,
}) => {
  const { health, stats, error } = useBackend();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <section className="glass-card lg:col-span-2 p-8 min-h-[200px] flex flex-col justify-between">
        <h2 className="text-sm font-black uppercase tracking-[0.2em] text-text-secondary opacity-50 mb-2">
          Backend Status
        </h2>
        {error || !health ? (
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full bg-rose-500 animate-pulse" />
            <span className="text-base font-bold text-rose-400 uppercase">
              Unreachable
            </span>
            <span className="text-sm text-text-secondary">
              (check backend port)
            </span>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-base font-black text-emerald-400 uppercase">
                  {health.status}
                </span>
              </div>
              <span className="text-sm text-text-secondary font-mono">
                v{health.version}
              </span>
              <span className="text-sm text-text-secondary">
                MCP: {health.mcp_server}
              </span>
            </div>
            {stats !== null && (
              <div className="flex items-center gap-4 mt-4 text-sm text-text-secondary">
                <span className="flex items-center gap-1.5">
                  <Database size={14} />
                  RAG: {stats.row_count} rows, {stats.sources?.length ?? 0}{" "}
                  sources
                </span>
              </div>
            )}
          </>
        )}
        <div className="mt-6 flex justify-end">
          <div className="w-12 h-12 rounded-full border border-white/5 flex items-center justify-center bg-white/[0.02] backdrop-blur-sm">
            <Server
              size={20}
              className={error ? "text-rose-500" : "text-accent-purple"}
            />
          </div>
        </div>
      </section>

      <section className="glass-card p-8 flex flex-col justify-between">
        <h2 className="text-xs font-black uppercase tracking-[0.2em] text-text-secondary opacity-50">
          Services
        </h2>
        {!health ? (
          <p className="text-sm text-text-secondary mt-4">—</p>
        ) : (
          <div className="space-y-4 mt-6">
            {Object.entries(health.providers).map(([name, available]) => (
              <div key={name} className="flex justify-between items-center">
                <span className="text-sm text-white capitalize">{name}</span>
                <span
                  className={`text-xs font-black uppercase ${available ? "text-emerald-500" : "text-white/30"}`}
                >
                  {available ? "Available" : "—"}
                </span>
              </div>
            ))}
            <div className="flex justify-between items-center pt-2 border-t border-white/5">
              <span className="text-sm text-white flex items-center gap-1.5">
                <Clock size={14} /> Active timers
              </span>
              <span className="text-sm font-mono text-white">
                {health.active_timers}
              </span>
            </div>
          </div>
        )}
      </section>

      <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6">
        <ActionCard
          title="Clone Voice"
          desc="Create high-fidelity clones from 5s audio."
          icon="👥"
          onClick={() => onNavigate("voices")}
        />
        <ActionCard
          title="Synthesize"
          desc="Generate expressive speech via Hume AI."
          icon="✨"
          onClick={() => onNavigate("tts")}
        />
        <ActionCard
          title="History"
          desc="Access previous voice interactions."
          icon="🕒"
          onClick={() => onNavigate("history")}
        />
      </div>
    </div>
  );
};

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  return (
    <BackendProvider>
      <AppLayout onNavigate={setActivePage} activePage={activePage}>
        {activePage === "dashboard" ? (
          <Dashboard onNavigate={setActivePage} />
        ) : activePage === "voicechat" ? (
          <VoiceChat />
        ) : activePage === "voices" ? (
          <VoicesPage />
        ) : activePage === "semantic" ? (
          <SemanticSearch />
        ) : activePage === "lab" || activePage === "evi" ? (
          <InteractionLab />
        ) : activePage === "creative" || activePage === "tts" ? (
          <CreativeLabs />
        ) : activePage === "tools" ? (
          <ToolsPage />
        ) : activePage === "services" ? (
          <ServiceLinkage />
        ) : activePage === "stt" ? (
          <SpeechToText />
        ) : activePage === "history" || activePage === "analysis" ? (
          <HistoryPage />
        ) : activePage === "settings" ? (
          <DeviceSettings />
        ) : activePage === "health" ? (
          <HealthPage />
        ) : activePage === "agentic" ? (
          <AgenticWorkflow />
        ) : activePage === "logger" ? (
          <SystemLogs />
        ) : activePage === "help" ? (
          <HelpPage />
        ) : (
          <div className="glass-card p-12 text-center max-w-2xl mx-auto">
            <h2 className="text-2xl font-black mb-4">Not Yet Implemented</h2>
            <p className="text-text-secondary leading-relaxed">
              The{" "}
              <span className="text-accent-purple font-mono">{activePage}</span>{" "}
              page is coming soon.
            </p>
          </div>
        )}
      </AppLayout>
    </BackendProvider>
  );
}

const ActionCard = ({
  title,
  desc,
  icon,
  onClick,
}: {
  title: string;
  desc: string;
  icon: string;
  onClick?: () => void;
}) => (
  <button
    type="button"
    className="glass-card p-8 group cursor-pointer flex flex-col transition-all active:scale-[0.98] text-left border-none w-full bg-transparent"
    onClick={onClick}
  >
    <div className="text-4xl mb-6 grayscale group-hover:grayscale-0 transition-all duration-500 scale-100 group-hover:scale-110 origin-left">
      {icon}
    </div>
    <h3 className="text-xl font-black mb-3 text-white group-hover:text-accent-purple transition-colors">
      {title}
    </h3>
    <p className="text-sm text-text-secondary leading-relaxed flex-1 opacity-80 group-hover:opacity-100">
      {desc}
    </p>
  </button>
);

export default App;
