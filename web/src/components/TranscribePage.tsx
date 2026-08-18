import { Download, FileAudio, Loader2, Upload } from "lucide-react";
import { useRef, useState } from "react";
import type { BatchTranscribeResult, TranscriptSegment } from "../api";
import { transcribeBatch } from "../api";

function srtTime(seconds: number): string {
  const ms = Math.round(seconds * 1000);
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  const rest = ms % 1000;
  const pad = (n: number, w = 2) => String(n).padStart(w, "0");
  return `${pad(h)}:${pad(m)}:${pad(s)},${pad(rest, 3)}`;
}

function vttTime(seconds: number): string {
  const ms = Math.round(seconds * 1000);
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  const rest = ms % 1000;
  const pad = (n: number, w = 2) => String(n).padStart(w, "0");
  return `${pad(m)}:${pad(s)}.${pad(rest, 3)}`;
}

function toSrt(segments: TranscriptSegment[]): string {
  return segments
    .map(
      (seg, i) =>
        `${i + 1}\n${srtTime(seg.start_s)} --> ${srtTime(seg.end_s)}\n${seg.text.trim()}`,
    )
    .join("\n\n");
}

function toVtt(segments: TranscriptSegment[]): string {
  return (
    "WEBVTT\n\n" +
    segments
      .map(
        (seg) =>
          `${vttTime(seg.start_s)} --> ${vttTime(seg.end_s)}\n${seg.text.trim()}`,
      )
      .join("\n\n")
  );
}

function toTxt(segments: TranscriptSegment[]): string {
  return segments
    .map((seg) => seg.text.trim())
    .filter(Boolean)
    .join("\n");
}

function download(
  filename: string,
  content: string,
  mime = "text/plain;charset=utf-8",
) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function baseName(name: string): string {
  return name.replace(/\.[^.]+$/, "");
}

export default function TranscribePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<BatchTranscribeResult[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState("auto");
  const inputRef = useRef<HTMLInputElement>(null);

  const run = async () => {
    if (!files.length) return;
    setBusy(true);
    setError(null);
    try {
      const res = await transcribeBatch(files, language);
      setResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setResults(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="transcribe-page">
      <header>
        <h1 className="text-2xl font-black mb-1">Batch Transcription</h1>
        <p className="text-sm text-text-secondary">
          Upload one or more audio files; FunASR transcribes each with
          timestamps. Download per-file transcripts as SRT, VTT, or TXT.
        </p>
      </header>

      <section className="glass-card p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[260px]">
            <label
              htmlFor="transcribe-files"
              className="text-xs font-bold uppercase tracking-wider text-text-secondary block mb-2"
            >
              Audio files
            </label>
            <input
              id="transcribe-files"
              ref={inputRef}
              type="file"
              multiple
              accept="audio/*,.mp3,.wav,.m4a,.flac,.ogg,.aac,.opus"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-white/10 file:px-4 file:py-2 file:text-sm file:font-bold file:text-white hover:file:bg-white/20"
            />
          </div>
          <div>
            <label
              htmlFor="transcribe-lang"
              className="text-xs font-bold uppercase tracking-wider text-text-secondary block mb-2"
            >
              Language
            </label>
            <select
              id="transcribe-lang"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="auto">Auto-detect</option>
              <option value="en">English</option>
              <option value="de">German</option>
              <option value="ja">Japanese</option>
              <option value="zh">Chinese</option>
              <option value="fr">French</option>
              <option value="es">Spanish</option>
            </select>
          </div>
          <button
            type="button"
            onClick={run}
            disabled={busy || files.length === 0}
            data-testid="transcribe-run"
            className="inline-flex items-center gap-2 text-sm font-bold text-white bg-accent-purple/80 hover:bg-accent-purple px-4 py-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {busy ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Upload size={16} />
            )}
            {busy ? "Transcribing…" : "Transcribe"}
          </button>
        </div>
        {files.length > 0 && !busy && (
          <p className="mt-3 text-xs text-text-secondary">
            {files.length} file{files.length > 1 ? "s" : ""} selected —{" "}
            {files.map((f) => f.name).join(", ")}
          </p>
        )}
        {error && (
          <p
            className="mt-3 text-sm text-rose-400"
            data-testid="transcribe-error"
          >
            {error}
          </p>
        )}
      </section>

      {results && (
        <section className="space-y-6" data-testid="transcribe-results">
          {results.map((r) => (
            <div key={r.filename} className="glass-card p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold flex items-center gap-2">
                  <FileAudio size={16} />
                  {r.filename}
                  <span
                    className={`text-xs font-black uppercase ${
                      r.success ? "text-emerald-500" : "text-rose-400"
                    }`}
                  >
                    {r.success ? "Done" : "Failed"}
                  </span>
                </h3>
                {r.success && r.segments.length > 0 && (
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        download(
                          `${baseName(r.filename)}.srt`,
                          toSrt(r.segments),
                        )
                      }
                      className="text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                    >
                      <Download size={13} /> SRT
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        download(
                          `${baseName(r.filename)}.vtt`,
                          toVtt(r.segments),
                        )
                      }
                      className="text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                    >
                      <Download size={13} /> VTT
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        download(
                          `${baseName(r.filename)}.txt`,
                          toTxt(r.segments),
                        )
                      }
                      className="text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                    >
                      <Download size={13} /> TXT
                    </button>
                  </div>
                )}
              </div>
              {r.error && <p className="text-sm text-rose-400">{r.error}</p>}
              {r.segments.length > 0 ? (
                <div className="space-y-1.5 max-h-72 overflow-y-auto pr-2">
                  {r.segments.map((seg) => (
                    <div
                      key={`${seg.start_s}-${seg.text.slice(0, 12)}`}
                      className="text-sm flex gap-3"
                    >
                      <span className="font-mono text-text-secondary shrink-0 whitespace-nowrap">
                        {srtTime(seg.start_s).slice(0, 8)} →{" "}
                        {srtTime(seg.end_s).slice(0, 8)}
                      </span>
                      <span className="text-white">{seg.text}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-text-secondary">
                  No speech detected.
                </p>
              )}
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
