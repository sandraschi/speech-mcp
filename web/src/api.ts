const BACKEND =
  (typeof import.meta !== "undefined" &&
    ((import.meta.env?.VITE_API_BASE as string | undefined) ||
      (import.meta.env?.VITE_API_URL as string | undefined))) ||
  "";

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

export interface VoiceProvider {
  name: string;
  status: string;
  voices: string[];
}

export interface HistoryItem {
  id: string;
  type: string;
  content: string;
  provider: string;
  timestamp: string;
}

export async function fetchVoices(): Promise<{ providers: VoiceProvider[] }> {
  const res = await fetch(`${BACKEND}/api/v1/voices`, {
    headers: authHeaders(),
  });
  if (!res.ok) return { providers: [] };
  return res.json();
}

export async function fetchHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${BACKEND}/api/v1/history`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function runDemo(
  demo: string,
): Promise<{ success: boolean; error?: string; output?: string }> {
  const res = await fetch(`${BACKEND}/api/v1/demos/run`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ demo }),
  });
  return res.json();
}

export async function controlWakeWord(
  action: string,
  keyword = "hey_jarvis",
  sensitivity = 0.5,
  sleepKeyword?: string,
): Promise<{ success: boolean; error?: string; status?: string }> {
  const res = await fetch(`${BACKEND}/api/v1/wake_word`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      keyword,
      sleep_keyword: sleepKeyword,
      sensitivity,
    }),
  });
  return res.json();
}

export interface RuntimeStatus {
  funasr: string;
  sherpa: string;
  gpu?: { available: boolean; name?: string; device?: string; torch?: string };
}

export async function getRuntime(): Promise<RuntimeStatus> {
  const res = await fetch(`${BACKEND}/api/v1/runtime`, {
    headers: authHeaders(),
  });
  return res.json();
}

export async function setRuntime(
  target: "funasr" | "sherpa",
  device: string,
): Promise<{ success: boolean; error?: string; device?: string }> {
  const res = await fetch(`${BACKEND}/api/v1/runtime`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ target, device }),
  });
  return res.json();
}

export interface TranscriptSegment {
  start_s: number;
  end_s: number;
  text: string;
  speaker?: number;
}

export interface BatchTranscribeResult {
  filename: string;
  success: boolean;
  error?: string;
  text: string;
  segments: TranscriptSegment[];
}

export async function transcribeBatch(
  files: File[],
  language = "auto",
): Promise<{
  success: boolean;
  results: BatchTranscribeResult[];
  count: number;
}> {
  const form = new FormData();
  for (const f of files) form.append("files", f, f.name);
  const res = await fetch(
    `${BACKEND}/api/v1/transcribe/batch?language=${encodeURIComponent(language)}`,
    { method: "POST", headers: authHeaders(), body: form },
  );
  if (!res.ok) throw new Error(`Batch transcription failed: ${res.statusText}`);
  return res.json();
}

export interface HealthData {
  status: string;
  version: string;
  mcp_server: string;
  rag_sources: string[];
  active_timers: number;
  wake_word_active: boolean;
  tokens: {
    google_api_key: boolean;
    hume_api_key: boolean;
    hume_config_id: boolean;
    elevenlabs_api_key: boolean;
  };
  providers: {
    hume: boolean;
    elevenlabs: boolean;
    gemini: boolean;
    gemma?: boolean;
    funasr?: boolean;
    sherpa_streaming?: boolean;
    windows: boolean;
  };
}

export async function request(
  path: string,
  options: RequestInit = {},
): Promise<any> {
  const res = await fetch(`${BACKEND}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.statusText}`);
  return res.json();
}

export interface StatsData {
  row_count: number;
  sources: string[];
}

export { BACKEND };
