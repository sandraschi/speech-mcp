const BACKEND =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  "http://localhost:10918";

function authHeaders(): HeadersInit {
  const token =
    typeof localStorage !== "undefined"
      ? localStorage.getItem("SPEECH_MCP_AUTH_TOKEN")
      : null;
  if (!token) return {};
  return { "X-Speech-MCP-Auth": token };
}

export async function fetchHealth(): Promise<HealthData | null> {
  const res = await fetch(`${BACKEND}/api/v1/health`, {
    headers: authHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function fetchStats(): Promise<StatsData | null> {
  const res = await fetch(`${BACKEND}/api/v1/stats`, {
    headers: authHeaders(),
  });
  if (!res.ok) return null;
  return res.json();
}

export interface HealthData {
  status: string;
  version: string;
  mcp_server: string;
  rag_sources: string[];
  active_timers: number;
  providers: { hume: boolean; elevenlabs: boolean; windows: boolean };
}

export interface StatsData {
  row_count: number;
  sources: string[];
}

export { BACKEND };
