import {
  Activity,
  Brain,
  ChevronLeft,
  History,
  Menu,
  Settings,
  Square,
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
  const { health, error, emergencyStop } = useBackend();
  const backendOnline = !error && health?.status === "healthy";

  const sidebarWidth = isCollapsed ? "80px" : "280px";

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
        background: "#0f0f13",
      }}
    >
      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 30,
            background: "rgba(0,0,0,0.6)",
            border: "none",
            cursor: "pointer",
            padding: 0,
            margin: 0,
            width: "100%",
            height: "100%",
          }}
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar — always in flex flow on desktop */}
      <aside
        style={{
          width: sidebarWidth,
          minWidth: sidebarWidth,
          height: "100vh",
          background: "#1a1a24",
          borderRight: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          flexDirection: "column",
          padding: "24px 16px",
          transition: "width 0.3s, min-width 0.3s",
          overflowY: "auto",
          overflowX: "hidden",
          flexShrink: 0,
          zIndex: 40,
        }}
        className="sidebar-desktop"
        data-testid="sidebar-nav"
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 32,
          }}
        >
          {!isCollapsed && (
            <span
              style={{
                fontWeight: 900,
                fontSize: 16,
                letterSpacing: "-0.05em",
                color: "white",
              }}
            >
              SPEECH-MCP
            </span>
          )}
          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            style={{
              marginLeft: isCollapsed ? "auto" : 0,
              padding: 6,
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "#cbd5e1",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
            }}
          >
            <ChevronLeft
              size={15}
              style={{
                transform: isCollapsed ? "rotate(180deg)" : "none",
                transition: "transform 0.3s",
              }}
            />
          </button>
        </div>

        <nav
          style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}
        >
          <NavItem
            icon="🏠"
            label="Dashboard"
            active={activePage === "dashboard"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("dashboard");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🎙️"
            label="EVI Session"
            active={activePage === "evi"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("evi");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🗣️"
            label="Voice Chat"
            active={activePage === "voicechat"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("voicechat");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🔊"
            label="Octave TTS"
            active={activePage === "tts"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("tts");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🧪"
            label="Creative Labs"
            active={activePage === "creative"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("creative");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="👤"
            label="Voice Clones"
            active={activePage === "voices"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("voices");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🔗"
            label="Apps Hub"
            active={activePage === "services"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("services");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🎤"
            label="STT Control"
            active={activePage === "stt"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("stt");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🎬"
            label="Transcribe"
            active={activePage === "transcribe"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("transcribe");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🔧"
            label="Tools"
            active={activePage === "tools"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("tools");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="📚"
            label="Skills"
            active={activePage === "skills"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("skills");
              setMobileOpen(false);
            }}
          />
          <div
            style={{
              height: 1,
              background: "rgba(255,255,255,0.06)",
              margin: "12px 8px",
            }}
          />
          <NavItem
            icon={<Brain size={18} />}
            label="Semantic"
            active={activePage === "semantic"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("semantic");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<Target size={18} />}
            label="Agentic"
            active={activePage === "agentic"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("agentic");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<History size={18} />}
            label="History"
            active={activePage === "history"}
            collapsed={isCollapsed}
            onClick={() => {
              onNavigate("history");
              setMobileOpen(false);
            }}
          />
          <div
            style={{
              marginTop: "auto",
              paddingTop: 16,
              borderTop: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <NavItem
              icon={<Settings size={18} />}
              label="Device Settings"
              active={activePage === "settings"}
              collapsed={isCollapsed}
              onClick={() => {
                onNavigate("settings");
                setMobileOpen(false);
              }}
            />
            <NavItem
              icon={<Activity size={18} />}
              label="System Health"
              active={activePage === "health"}
              collapsed={isCollapsed}
              onClick={() => {
                onNavigate("health");
                setMobileOpen(false);
              }}
            />
          </div>
        </nav>

        {!isCollapsed && (
          <div
            style={{
              marginTop: 24,
              padding: "12px 14px",
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 11,
                fontWeight: 800,
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                color: "#cbd5e1",
              }}
            >
              <span>Backend</span>
              <span style={{ color: backendOnline ? "#34d399" : "#f87171" }}>
                {backendOnline ? "● Online" : "● Offline"}
              </span>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 11,
                marginTop: 6,
                color: "#64748b",
                fontFamily: "monospace",
              }}
            >
              <span>Port</span>
              <span style={{ color: "white" }}>10909</span>
            </div>
          </div>
        )}
      </aside>

      {/* Mobile sidebar overlay */}
      <aside
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          height: "100vh",
          width: 280,
          background: "#1a1a24",
          borderRight: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          flexDirection: "column",
          padding: "24px 16px",
          zIndex: 40,
          transform: mobileOpen ? "translateX(0)" : "translateX(-100%)",
          transition: "transform 0.3s",
          overflowY: "auto",
        }}
        className="sidebar-mobile"
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 32,
          }}
        >
          <span
            style={{
              fontWeight: 900,
              fontSize: 16,
              letterSpacing: "-0.05em",
              color: "white",
            }}
          >
            SPEECH-MCP
          </span>
          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            style={{
              background: "none",
              border: "none",
              color: "#cbd5e1",
              cursor: "pointer",
            }}
          >
            <X size={20} />
          </button>
        </div>
        <nav
          style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}
        >
          <NavItem
            icon="🏠"
            label="Dashboard"
            active={activePage === "dashboard"}
            collapsed={false}
            onClick={() => {
              onNavigate("dashboard");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🎙️"
            label="EVI Session"
            active={activePage === "evi"}
            collapsed={false}
            onClick={() => {
              onNavigate("evi");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🗣️"
            label="Voice Chat"
            active={activePage === "voicechat"}
            collapsed={false}
            onClick={() => {
              onNavigate("voicechat");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🔊"
            label="Octave TTS"
            active={activePage === "tts"}
            collapsed={false}
            onClick={() => {
              onNavigate("tts");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🧪"
            label="Creative Labs"
            active={activePage === "creative"}
            collapsed={false}
            onClick={() => {
              onNavigate("creative");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="👤"
            label="Voice Clones"
            active={activePage === "voices"}
            collapsed={false}
            onClick={() => {
              onNavigate("voices");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🔗"
            label="Apps Hub"
            active={activePage === "services"}
            collapsed={false}
            onClick={() => {
              onNavigate("services");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🎤"
            label="STT Control"
            active={activePage === "stt"}
            collapsed={false}
            onClick={() => {
              onNavigate("stt");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🎬"
            label="Transcribe"
            active={activePage === "transcribe"}
            collapsed={false}
            onClick={() => {
              onNavigate("transcribe");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="🔧"
            label="Tools"
            active={activePage === "tools"}
            collapsed={false}
            onClick={() => {
              onNavigate("tools");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon="📚"
            label="Skills"
            active={activePage === "skills"}
            collapsed={false}
            onClick={() => {
              onNavigate("skills");
              setMobileOpen(false);
            }}
          />
          <div
            style={{
              height: 1,
              background: "rgba(255,255,255,0.06)",
              margin: "12px 8px",
            }}
          />
          <NavItem
            icon={<Brain size={18} />}
            label="Semantic"
            active={activePage === "semantic"}
            collapsed={false}
            onClick={() => {
              onNavigate("semantic");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<Target size={18} />}
            label="Agentic"
            active={activePage === "agentic"}
            collapsed={false}
            onClick={() => {
              onNavigate("agentic");
              setMobileOpen(false);
            }}
          />
          <NavItem
            icon={<History size={18} />}
            label="History"
            active={activePage === "history"}
            collapsed={false}
            onClick={() => {
              onNavigate("history");
              setMobileOpen(false);
            }}
          />
          <div
            style={{
              marginTop: "auto",
              paddingTop: 16,
              borderTop: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <NavItem
              icon={<Settings size={18} />}
              label="Device Settings"
              active={activePage === "settings"}
              collapsed={false}
              onClick={() => {
                onNavigate("settings");
                setMobileOpen(false);
              }}
            />
            <NavItem
              icon={<Activity size={18} />}
              label="System Health"
              active={activePage === "health"}
              collapsed={false}
              onClick={() => {
                onNavigate("health");
                setMobileOpen(false);
              }}
            />
          </div>
        </nav>
      </aside>

      {/* Main content */}
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
        }}
      >
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "20px 32px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            flexShrink: 0,
          }}
        >
          {/* Mobile hamburger */}
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="sidebar-mobile"
            style={{
              background: "none",
              border: "none",
              color: "white",
              cursor: "pointer",
              marginRight: 12,
              display: "none",
            }}
          >
            <Menu size={22} />
          </button>
          <div>
            <h1
              style={{
                margin: 0,
                fontWeight: 900,
                fontSize: 22,
                letterSpacing: "-0.05em",
                color: "white",
              }}
            >
              Speech MCP
            </h1>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginTop: 4,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: backendOnline ? "#34d399" : "#f87171",
                  display: "inline-block",
                }}
                data-testid="topbar-status"
              />
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  color: "#cbd5e1",
                }}
              >
                {backendOnline ? "Backend online" : "Backend offline"}
              </span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              type="button"
              onClick={() => emergencyStop()}
              title="EMERGENCY STOP (Cancel All Audio & Timers)"
              data-testid="stop-button"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 20px",
                background: "#ef4444",
                border: "none",
                borderRadius: 10,
                color: "white",
                fontSize: 14,
                fontWeight: 900,
                cursor: "pointer",
                boxShadow: "0 0 15px rgba(239, 68, 68, 0.4)",
                transition: "transform 0.1s active",
              }}
              onMouseDown={(e) =>
                (e.currentTarget.style.transform = "scale(0.95)")
              }
              onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              <Square size={16} fill="white" /> STOP
            </button>
            <button
              type="button"
              onClick={() => onNavigate("settings")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "8px 16px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 10,
                color: "white",
                fontSize: 13,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              <Settings size={15} /> Settings
            </button>
          </div>
        </header>

        <div style={{ flex: 1, padding: "32px", overflowY: "auto" }}>
          {children}
        </div>
      </main>

      <style>{`
        @media (max-width: 1023px) {
          .sidebar-desktop { display: none !important; }
          .sidebar-mobile { display: flex !important; }
        }
      `}</style>
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
    style={{
      width: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: collapsed ? "center" : "flex-start",
      gap: 12,
      padding: collapsed ? "10px 0" : "10px 14px",
      borderRadius: 10,
      border: "none",
      cursor: "pointer",
      transition: "background 0.15s, color 0.15s",
      background: active ? "#a78bfa" : "transparent",
      color: active ? "white" : "#94a3b8",
      fontWeight: 700,
      fontSize: 13,
    }}
    onMouseEnter={(e) => {
      if (!active)
        (e.currentTarget as HTMLButtonElement).style.background =
          "rgba(255,255,255,0.06)";
    }}
    onMouseLeave={(e) => {
      if (!active)
        (e.currentTarget as HTMLButtonElement).style.background = "transparent";
    }}
  >
    <span style={{ fontSize: 16, lineHeight: 1, flexShrink: 0 }}>{icon}</span>
    {!collapsed && (
      <span
        style={{
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {label}
      </span>
    )}
  </button>
);

export default AppLayout;
