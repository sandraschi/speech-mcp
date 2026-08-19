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

export interface RevisionChange {
  index: number;
  original: string;
  revised: string;
  reading?: string;
  reason?: string;
  confidence?: number;
  review?: boolean;
  applied?: boolean;
}

export interface ReviseResult {
  success: boolean;
  error?: string;
  revised_srt: string;
  changes: RevisionChange[];
  applied_count: number;
  flagged_count: number;
  language: string;
  model?: string;
}

export async function reviseSubtitles(
  srt: string,
  series = "",
  glossary = "",
  language = "ja",
): Promise<ReviseResult> {
  const res = await fetch(`${BACKEND}/api/v1/subtitles/revise`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ srt, series, glossary, language }),
  });
  return res.json();
}

export interface TranscriptEntry {
  id: number;
  series: string;
  season: number | null;
  episode: number | null;
  title: string;
  source: string;
  source_media_key: string;
  language: string;
  status: string;
  model: string;
  raw_srt_path: string;
  revised_srt_path: string;
  created_at: string;
  updated_at: string;
  raw_srt?: string;
  revised_srt?: string;
  changes?: RevisionChange[];
}

export async function transcribePlex(payload: {
  media_key: string;
  plex_mcp_url?: string;
  series?: string;
  season?: number | null;
  episode?: number | null;
  language?: string;
}): Promise<{
  success: boolean;
  transcript?: TranscriptEntry;
  info?: Record<string, unknown>;
}> {
  const res = await fetch(`${BACKEND}/api/v1/transcribe/plex`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Plex transcribe failed: ${res.statusText}`);
  return res.json();
}

export async function fetchTranscripts(limit = 50): Promise<{
  success: boolean;
  transcripts: TranscriptEntry[];
  count: number;
}> {
  const res = await fetch(`${BACKEND}/api/v1/transcripts?limit=${limit}`, {
    headers: authHeaders(),
  });
  return res.json();
}

export async function setTranscriptStatus(
  id: number,
  status: string,
): Promise<{ success: boolean; transcript?: TranscriptEntry }> {
  const res = await fetch(`${BACKEND}/api/v1/transcripts/${id}/status`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  return res.json();
}

export async function reviseTranscript(
  id: number,
  glossary = "",
): Promise<{
  success: boolean;
  transcript?: TranscriptEntry;
  applied_count?: number;
  flagged_count?: number;
}> {
  const res = await fetch(`${BACKEND}/api/v1/transcripts/${id}/revise`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ glossary }),
  });
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

export async function request<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.statusText}`);
  return res.json() as Promise<T>;
}

export interface StatsData {
  row_count: number;
  sources: string[];
}

export interface Persona {
  name: string;
  description: string;
  system: string;
}

export interface ChatResponse {
  success: boolean;
  reply: string;
  personality: string;
  skill?: string | null;
}

export async function fetchPersonas(): Promise<Persona[]> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/personas`, {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.personas ?? [];
  } catch {
    return [];
  }
}

export async function chatMessage(payload: {
  message: string;
  personality: string;
  skill?: string | null;
  provider: string;
  model?: string | null;
  base_url?: string | null;
  remember?: boolean;
}): Promise<ChatResponse> {
  const res = await fetch(`${BACKEND}/api/v1/chat`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Chat failed: ${res.statusText}`);
  }
  return res.json();
}

export interface MemoryEpisode {
  id: number;
  ts: string;
  kind: string;
  speaker: string;
  text: string;
  topic: string;
  provider: string;
}

export async function fetchMemory(limit = 20): Promise<MemoryEpisode[]> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/memory?limit=${limit}`, {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.episodes ?? [];
  } catch {
    return [];
  }
}

export async function storeMemory(payload: {
  text: string;
  kind?: string;
  speaker?: string;
  topic?: string;
  provider?: string;
}): Promise<{ success: boolean; episode?: MemoryEpisode }> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/memory`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  } catch {
    return { success: false };
  }
}

export async function fetchMemoryStats(): Promise<{
  total: number;
  by_kind: Record<string, number>;
}> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/memory/stats`, {
      headers: authHeaders(),
    });
    if (!res.ok) return { total: 0, by_kind: {} };
    return res.json();
  } catch {
    return { total: 0, by_kind: {} };
  }
}

export interface AnalyticsSummary {
  window_hours: number;
  total_calls: number;
  providers: Record<
    string,
    {
      calls: number;
      errors: number;
      success_rate: number;
      avg_latency_ms: number | null;
      p95_latency_ms: number | null;
    }
  >;
}

export async function fetchAnalytics(
  hours = 24,
): Promise<AnalyticsSummary | null> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/analytics?hours=${hours}`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export { BACKEND };
