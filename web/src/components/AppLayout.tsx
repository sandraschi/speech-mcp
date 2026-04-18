import {
  Activity,
  Brain,
  ChevronLeft,
  History,
  Menu,
  Settings,
  Target,
  X,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useBackend } from "../BackendContext";

interface AppLayoutProps {
  children: React.ReactNode;
  onNavigate: (page: string) => void;
  activePage: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  onNavigate,
  activePage,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { health, error } = useBackend();
  const backendOnline = !error && health?.status === "healthy";

  return (
    <div className="flex min-h-screen bg-bg-primary font-sans">
      {/* Mobile Toggle */}
      <button
        type="button"
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 bg-accent-purple text-white rounded-xl shadow-lg shadow-accent-purple/30 active:scale-95 transition-transform"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`
                fixed inset-y-0 left-0 z-40 lg:relative lg:translate-x-0 transition-all duration-500
                ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
                ${isCollapsed ? "w-20" : "w-[280px]"}
                bg-bg-secondary border-r border-white/5 flex flex-col p-6
            `}
      >
        <div className="flex items-center justify-between mb-12">
          <div className="font-black text-xl tracking-tighter text-white">
            {!isCollapsed ? "SPEECH-MCP" : "S-M"}
          </div>
          <button
            type="button"
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            className="p-1.5 bg-white/5 border border-white/10 text-text-secondary rounded-lg hover:text-white transition-colors"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            <ChevronLeft
              size={16}
              className={`transition-transform duration-300 ${isCollapsed ? "rotate-180" : ""}`}
            />
          </button>
        </div>

        <nav className="flex-1 flex flex-col gap-2 overflow-y-auto custom-scrollbar">
          <NavItem
            icon="🏠"
            label="Dashboard"
            active={activePage === "dashboard"}
            onClick={() => {
              onNavigate("dashboard");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />
          <NavItem
            icon="🎙️"
            label="EVI Session"
            active={activePage === "evi"}
            onClick={() => {
              onNavigate("evi");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />
          <NavItem
            icon="🔊"
            label="Octave TTS"
            active={activePage === "tts"}
            onClick={() => {
              onNavigate("tts");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />
          <NavItem
            icon="👤"
            label="Voice Clones"
            active={activePage === "voices"}
            onClick={() => {
              onNavigate("voices");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />
          <NavItem
            icon="🔗"
            label="Apps Hub"
            active={activePage === "services"}
            onClick={() => {
              onNavigate("services");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />
          <NavItem
            icon="🎙️"
            label="STT Control"
            active={activePage === "stt"}
            onClick={() => {
              onNavigate("stt");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />
          <NavItem
            icon="🔧"
            label="Tools"
            active={activePage === "tools"}
            onClick={() => {
              onNavigate("tools");
              setMobileOpen(false);
            }}
            collapsed={isCollapsed}
          />

          <div className="h-[1px] bg-white/5 my-4 mx-2" />

          <NavItem
            icon={<Brain size={20} />}
            label="Semantic"
            active={activePage === "semantic"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("semantic");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<Target size={20} />}
            label="Agentic"
            active={activePage === "agentic"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("agentic");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<History size={20} />}
            label="History"
            active={activePage === "history"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("history");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<Activity size={20} />}
            label="System Logs"
            active={activePage === "logger"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("logger");
              setMobileOpen(false);
            }}
          />

          <div className="mt-auto pt-6 border-t border-white/5">
            <NavItem
              icon={<Settings size={18} />}
              label="Settings"
              active={activePage === "settings"}
              onClick={() => {
                onNavigate("settings");
                setMobileOpen(false);
              }}
              collapsed={isCollapsed}
            />
          </div>
        </nav>

        {!isCollapsed && (
          <div className="mt-8">
            <div className="glass-card p-4 space-y-2">
              <div className="flex justify-between items-center text-xs font-black tracking-widest text-text-secondary uppercase">
                <span>Backend</span>
                <span
                  className={
                    backendOnline ? "text-emerald-400" : "text-rose-500"
                  }
                >
                  {backendOnline ? "● Online" : "● Offline"}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-text-secondary/50">Port</span>
                <span className="text-white">10918</span>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 lg:p-12 max-w-7xl mx-auto w-full transition-all duration-500 overflow-y-auto">
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-12">
          <div>
            <h1 className="text-3xl font-black tracking-tighter text-white">
              Speech MCP
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`w-2 h-2 rounded-full animate-pulse ${backendOnline ? "bg-emerald-400" : "bg-rose-500"}`}
              />
              <span className="text-xs text-text-secondary font-medium uppercase tracking-wider">
                {backendOnline ? "Backend online" : "Backend offline"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 w-full sm:w-auto">
            <button
              type="button"
              className="flex-1 sm:flex-none glass-card px-5 py-2.5 flex items-center justify-center gap-2 text-sm font-bold text-white hover:bg-white/10"
              onClick={() => onNavigate("settings")}
            >
              <Settings size={16} />
              <span>Settings</span>
            </button>
            <button
              type="button"
              className="flex-1 sm:flex-none btn-primary px-6 py-2.5 text-sm"
            >
              New Session
            </button>
          </div>
        </header>

        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          {children}
        </div>
      </main>
    </div>
  );
};

const NavItem = ({
  icon,
  label,
  active = false,
  onClick,
  collapsed = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
  collapsed?: boolean;
}) => (
  <button
    type="button"
    onClick={onClick}
    title={collapsed ? label : ""}
    className={`
            w-full flex items-center gap-4 px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 group border-none
            ${
              active
                ? "bg-accent-purple text-white shadow-lg shadow-accent-purple/20"
                : "bg-transparent text-text-secondary hover:bg-white/5 hover:text-white"
            }
            ${collapsed ? "justify-center" : ""}
        `}
  >
    <span
      className={`transition-transform duration-300 ${active ? "scale-110" : "group-hover:scale-110"}`}
    >
      {icon}
    </span>
    {!collapsed && (
      <span className="font-bold text-sm tracking-tight">{label}</span>
    )}
  </button>
);

export default AppLayout;
