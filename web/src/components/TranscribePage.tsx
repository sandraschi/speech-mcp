import {
  Clapperboard,
  Download,
  FileAudio,
  Loader2,
  RefreshCw,
  Upload,
  Wand2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  BatchTranscribeResult,
  ReviseResult,
  RevisionChange,
  TranscriptEntry,
  TranscriptSegment,
} from "../api";
import {
  fetchTranscripts,
  reviseSubtitles,
  reviseTranscript,
  setTranscriptStatus,
  transcribeBatch,
  transcribePlex,
} from "../api";

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

  // revision state per result filename
  const [revising, setRevising] = useState<string | null>(null);
  const [revisions, setRevisions] = useState<Record<string, ReviseResult>>({});

  // plex fetch state
  const [plexKey, setPlexKey] = useState("");
  const [plexSeries, setPlexSeries] = useState("");
  const [plexSeason, setPlexSeason] = useState("");
  const [plexEpisode, setPlexEpisode] = useState("");
  const [plexBusy, setPlexBusy] = useState(false);
  const [plexMsg, setPlexMsg] = useState<string | null>(null);

  // depot listing
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);
  const [depotBusy, setDepotBusy] = useState(false);
  const [revisingDepot, setRevisingDepot] = useState<number | null>(null);

  const loadTranscripts = useCallback(async () => {
    setDepotBusy(true);
    try {
      const res = await fetchTranscripts(50);
      setTranscripts(res.transcripts ?? []);
    } catch {
      setTranscripts([]);
    } finally {
      setDepotBusy(false);
    }
  }, []);

  useEffect(() => {
    loadTranscripts();
  }, [loadTranscripts]);

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

  const reviseFile = async (filename: string, segs: TranscriptSegment[]) => {
    setRevising(filename);
    try {
      const res = await reviseSubtitles(toSrt(segs), "", "", language);
      setRevisions((prev) => ({ ...prev, [filename]: res }));
      if (res.success && res.revised_srt) {
        download(`${baseName(filename)}.revised.srt`, res.revised_srt);
      }
    } catch (e) {
      setRevisions((prev) => ({
        ...prev,
        [filename]: {
          success: false,
          revised_srt: "",
          changes: [],
          applied_count: 0,
          flagged_count: 0,
          language,
          error: e instanceof Error ? e.message : String(e),
        },
      }));
    } finally {
      setRevising(null);
    }
  };

  const fetchFromPlex = async () => {
    if (!plexKey.trim()) return;
    setPlexBusy(true);
    setPlexMsg(null);
    try {
      const res = await transcribePlex({
        media_key: plexKey.trim(),
        series: plexSeries.trim(),
        season: plexSeason.trim() ? Number(plexSeason) : null,
        episode: plexEpisode.trim() ? Number(plexEpisode) : null,
        language,
      });
      setPlexMsg(
        res.success && res.transcript
          ? `Transcribed #${res.transcript.id} "${res.transcript.title}" (${res.info?.segment_count ?? "?"} segments) - ${res.transcript.status}`
          : "Plex fetch failed",
      );
      await loadTranscripts();
    } catch (e) {
      setPlexMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setPlexBusy(false);
    }
  };

  const reviseDepotEntry = async (id: number) => {
    setRevisingDepot(id);
    try {
      const res = await reviseTranscript(id);
      if (res.success) {
        setPlexMsg(
          `Transcript #${id}: ${res.applied_count ?? 0} applied, ${res.flagged_count ?? 0} flagged`,
        );
      } else {
        setPlexMsg(`Revise #${id} failed`);
      }
      await loadTranscripts();
    } catch (e) {
      setPlexMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setRevisingDepot(null);
    }
  };

  const setDepotStatus = async (id: number, status: string) => {
    try {
      await setTranscriptStatus(id, status);
      await loadTranscripts();
    } catch (e) {
      setPlexMsg(e instanceof Error ? e.message : String(e));
    }
  };

  const revisionDiff = (changes: RevisionChange[]) =>
    changes.map((c) => (
      <div key={`chg-${c.index}`} className="text-sm flex gap-2 items-baseline">
        <span className="font-mono text-text-secondary shrink-0">
          #{c.index}
        </span>
        <span
          className={
            c.applied ? "line-through text-rose-400" : "text-text-secondary"
          }
        >
          {c.original}
        </span>
        <span className="text-white">→</span>
        <span className="text-emerald-400">{c.revised}</span>
        {c.reading && (
          <span className="text-[10px] font-mono text-text-secondary uppercase">
            ({c.reading})
          </span>
        )}
      </div>
    ));

  return (
    <div className="space-y-6" data-testid="transcribe-page">
      <header>
        <h1 className="text-2xl font-black mb-1">Batch Transcription</h1>
        <p className="text-sm text-text-secondary">
          Upload one or more audio files; FunASR transcribes each with
          timestamps. Download per-file transcripts as SRT, VTT, or TXT, then
          run the homophone revision pass (Japanese jukugo) or pull an episode
          straight from Plex.
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
                  <div className="flex flex-wrap gap-2">
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
                    {language === "ja" && r.segments.length > 0 && (
                      <button
                        type="button"
                        onClick={() => reviseFile(r.filename, r.segments)}
                        disabled={revising === r.filename}
                        className="text-xs font-bold text-white bg-amber-500/20 hover:bg-amber-500/30 px-3 py-1.5 rounded-lg flex items-center gap-1.5 disabled:opacity-50"
                      >
                        {revising === r.filename ? (
                          <Loader2 size={13} className="animate-spin" />
                        ) : (
                          <Wand2 size={13} />
                        )}
                        {revising === r.filename ? "Revising…" : "Revise"}
                      </button>
                    )}
                  </div>
                )}
              </div>
              {r.error && <p className="text-sm text-rose-400">{r.error}</p>}
              {revisions[r.filename] &&
                (revisions[r.filename].success === false ? (
                  <p className="text-sm text-rose-400">
                    {revisions[r.filename].error}
                  </p>
                ) : (
                  <div className="mt-3 p-3 rounded-lg bg-white/[0.03] border border-amber-500/20">
                    <div className="text-xs font-black uppercase tracking-wider text-amber-400 mb-2">
                      Homophone check: {revisions[r.filename].applied_count}{" "}
                      applied, {revisions[r.filename].flagged_count} flagged
                    </div>
                    {revisions[r.filename].changes.length > 0 ? (
                      <div className="space-y-1">
                        {revisionDiff(revisions[r.filename].changes)}
                      </div>
                    ) : (
                      <p className="text-sm text-text-secondary">
                        No homophone issues found.
                      </p>
                    )}
                    {revisions[r.filename].revised_srt && (
                      <button
                        type="button"
                        onClick={() =>
                          download(
                            `${baseName(r.filename)}.revised.srt`,
                            revisions[r.filename].revised_srt,
                          )
                        }
                        className="mt-3 text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                      >
                        <Download size={13} /> Revised SRT
                      </button>
                    )}
                  </div>
                ))}
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

      {/* Plex fetch */}
      <section className="glass-card p-6" data-testid="plex-fetch">
        <div className="flex items-center gap-2 mb-4">
          <Clapperboard size={18} className="text-amber-400" />
          <h2 className="font-bold">Fetch from Plex</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="col-span-2 md:col-span-1">
            <label
              htmlFor="plex-media-key"
              className="text-xs font-bold uppercase tracking-wider text-text-secondary block mb-1"
            >
              Plex media key
            </label>
            <input
              id="plex-media-key"
              type="text"
              value={plexKey}
              onChange={(e) => setPlexKey(e.target.value)}
              placeholder="ratingKey (e.g. 300482)"
              className="w-full bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label
              htmlFor="plex-series"
              className="text-xs font-bold uppercase tracking-wider text-text-secondary block mb-1"
            >
              Series
            </label>
            <input
              id="plex-series"
              type="text"
              value={plexSeries}
              onChange={(e) => setPlexSeries(e.target.value)}
              placeholder="show name"
              className="w-full bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label
              htmlFor="plex-season"
              className="text-xs font-bold uppercase tracking-wider text-text-secondary block mb-1"
            >
              Season
            </label>
            <input
              id="plex-season"
              type="text"
              value={plexSeason}
              onChange={(e) => setPlexSeason(e.target.value)}
              placeholder="1"
              className="w-full bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label
              htmlFor="plex-episode"
              className="text-xs font-bold uppercase tracking-wider text-text-secondary block mb-1"
            >
              Episode
            </label>
            <input
              id="plex-episode"
              type="text"
              value={plexEpisode}
              onChange={(e) => setPlexEpisode(e.target.value)}
              placeholder="1"
              className="w-full bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={fetchFromPlex}
              disabled={plexBusy || !plexKey.trim()}
              data-testid="plex-fetch-run"
              className="w-full inline-flex items-center justify-center gap-2 text-sm font-bold text-white bg-amber-500/20 hover:bg-amber-500/30 px-4 py-2 rounded-lg transition-colors disabled:opacity-40"
            >
              {plexBusy ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <Clapperboard size={15} />
              )}
              {plexBusy ? "Fetching…" : "Fetch & Transcribe"}
            </button>
          </div>
        </div>
        <p className="text-[11px] text-text-secondary mt-2">
          Downloads the episode from Plex, extracts audio, transcribes with
          FunASR, and stores a draft SRT in the transcript depot. Requires
          plex-mcp running on :10740.
        </p>
        {plexMsg && (
          <p
            className={`mt-3 text-sm ${
              plexMsg.startsWith("Transcribed")
                ? "text-emerald-400"
                : "text-rose-400"
            }`}
          >
            {plexMsg}
          </p>
        )}
      </section>

      {/* Depot */}
      <section className="glass-card p-6" data-testid="transcript-depot">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileAudio size={18} className="text-accent-purple" />
            <h2 className="font-bold">Transcript depot</h2>
          </div>
          <button
            type="button"
            onClick={loadTranscripts}
            disabled={depotBusy}
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg disabled:opacity-50"
          >
            <RefreshCw size={13} className={depotBusy ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
        {transcripts.length === 0 ? (
          <p className="text-sm text-text-secondary">
            No transcripts yet. Upload files above or fetch from Plex.
          </p>
        ) : (
          <div className="space-y-2">
            {transcripts.map((t) => (
              <div
                key={t.id}
                className="flex flex-wrap items-center gap-3 p-3 bg-white/[0.03] border border-white/5 rounded-xl"
              >
                <span className="text-sm font-mono text-text-secondary">
                  #{t.id}
                </span>
                <span className="text-sm font-bold text-white flex-1 min-w-[140px] truncate">
                  {t.series ||
                    t.title ||
                    t.source_media_key ||
                    `transcript ${t.id}`}
                </span>
                {t.season != null && (
                  <span className="text-xs font-mono text-text-secondary">
                    S{t.season}E{t.episode ?? "?"}
                  </span>
                )}
                <span className="text-[10px] font-mono text-text-secondary uppercase">
                  {t.source}
                </span>
                <span
                  className={`text-[10px] font-black uppercase rounded-full px-2 py-0.5 ${
                    t.status === "reviewed"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : t.status === "revised"
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-white/10 text-white/50"
                  }`}
                >
                  {t.status}
                </span>
                {t.language === "ja" && (
                  <button
                    type="button"
                    onClick={() => reviseDepotEntry(t.id)}
                    disabled={revisingDepot === t.id}
                    className="text-xs font-bold text-white bg-amber-500/20 hover:bg-amber-500/30 px-2.5 py-1 rounded-lg disabled:opacity-50 flex items-center gap-1"
                  >
                    {revisingDepot === t.id ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Wand2 size={12} />
                    )}
                    Revise
                  </button>
                )}
                <select
                  value={t.status}
                  onChange={(e) => setDepotStatus(t.id, e.target.value)}
                  className="text-xs bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-2 py-1"
                >
                  <option value="draft">draft</option>
                  <option value="revised">revised</option>
                  <option value="reviewed">reviewed</option>
                </select>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
