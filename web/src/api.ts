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

export { BACKEND };
