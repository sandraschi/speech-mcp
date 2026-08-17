import {
  Activity,
  AlertCircle,
  Brain,
  Database,
  FileText,
  Search,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { BACKEND } from "../api";

interface SearchResult {
  id: string;
  filename: string;
  score: number;
  content: string;
}

interface RagStats {
  row_count: number;
  sources: string[];
}

const SemanticSearch: React.FC = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [stats, setStats] = useState<RagStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [askMode, setAskMode] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(
    null,
  );

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND}/api/v1/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch RAG stats:", err);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${BACKEND}/api/v1/search?q=${encodeURIComponent(query)}`,
      );
      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setAskMode(true);
    setError(null);
    setAnswer(null);

    try {
      const localProvider = localStorage.getItem("LOCAL_PROVIDER") || "ollama";
      const ollamaUrl =
        localStorage.getItem("OLLAMA_URL") || "http://localhost:11434";
      const lmstudioUrl =
        localStorage.getItem("LMSTUDIO_URL") || "http://localhost:1234";
      const localModel = localStorage.getItem("LOCAL_MODEL") || "llama3.1:8b";

      const api_url = localProvider === "ollama" ? ollamaUrl : lmstudioUrl;

      const response = await fetch(`${BACKEND}/api/v1/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: query,
          model: localModel,
          provider: localProvider,
          api_url: api_url,
        }),
      });

      if (!response.ok) throw new Error("AI Query failed");
      const data = await response.json();
      setAnswer(data.answer);

      // Results are still shown as grounded context
      const contextResults = data.context
        .split("\n")
        .map((c: string, i: number) => ({
          id: `context-${i}`,
          filename: "Grounded Context",
          score: 1.0,
          content: c,
        }));
      setResults(contextResults);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
    } finally {
      setLoading(false);
      setAskMode(false);
    }
  };

  return (
    <div className="h-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-8">
        <div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
            Memory Hub
          </h1>
          <p className="text-text-secondary text-sm font-bold uppercase tracking-widest opacity-60 text-accent-blue/80">
            Semantic Fragment Retrieval
          </p>
        </div>

        {stats && (
          <div className="flex gap-4">
            <div className="glass-card px-6 py-4 flex items-center gap-4 bg-accent-blue/5 border-accent-blue/10">
              <div className="bg-accent-blue/10 p-2 rounded-lg text-accent-blue border border-accent-blue/20">
                <Database size={16} />
              </div>
              <div>
                <div className="text-lg font-black text-white leading-tight tabular-nums">
                  {stats.row_count}
                </div>
                <div className="text-xs text-text-secondary uppercase tracking-widest font-black opacity-40">
                  Fragments
                </div>
              </div>
            </div>
            <div className="glass-card px-6 py-4 flex items-center gap-4 bg-accent-purple/5 border-accent-purple/10">
              <div className="bg-accent-purple/10 p-2 rounded-lg text-accent-purple border border-accent-purple/20">
                <FileText size={16} />
              </div>
              <div>
                <div className="text-lg font-black text-white leading-tight tabular-nums">
                  {stats.sources.length}
                </div>
                <div className="text-xs text-text-secondary uppercase tracking-widest font-black opacity-40">
                  Sources
                </div>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Search Interface */}
      <div className="glass-card p-10 shadow-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-accent-blue/5 opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />

        <form onSubmit={handleSearch} className="relative group/form">
          <div className="absolute inset-0 bg-accent-blue/5 blur-3xl opacity-0 group-focus-within/form:opacity-100 transition-opacity" />
          <div className="relative flex items-center gap-6 bg-white/[0.03] border border-white/10 rounded-3xl px-8 py-6 focus-within:border-accent-blue/50 focus-within:bg-white/[0.05] transition-all">
            <label htmlFor="semantic-query-input" className="sr-only">
              Semantic Query
            </label>
            <Search className="w-8 h-8 text-text-secondary opacity-20 group-focus-within/form:text-accent-blue group-focus-within/form:opacity-100 transition-all" />
            <input
              id="semantic-query-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Query semantic history..."
              title="Semantic Query"
              className="flex-1 bg-transparent border-none outline-none text-2xl font-black text-white placeholder-white/5 tracking-tight"
            />
            <button
              type="submit"
              disabled={loading}
              title="Execute Retrieval"
              className="bg-accent-blue hover:bg-accent-blue-hover text-white px-10 py-5 rounded-2xl font-black text-xs tracking-widest uppercase transition-all disabled:opacity-20 flex items-center gap-3 shadow-xl hover:scale-105 active:scale-95"
            >
              {loading && !askMode ? (
                <Activity className="w-5 h-5 animate-spin" />
              ) : (
                "Retrieve"
              )}
            </button>
            <button
              type="button"
              disabled={loading}
              title="Grounded AI Query"
              onClick={handleAsk}
              className="bg-accent-purple hover:bg-accent-purple-hover text-white px-10 py-5 rounded-2xl font-black text-xs tracking-widest uppercase transition-all disabled:opacity-20 flex items-center gap-3 shadow-xl hover:scale-105 active:scale-95 border border-accent-purple/30"
            >
              {loading && askMode ? (
                <Activity className="w-5 h-5 animate-spin" />
              ) : (
                "Ask AI"
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl flex items-center gap-3 text-rose-500 text-[10px] font-black uppercase tracking-widest animate-in slide-in-from-top-2 duration-300">
            <AlertCircle size={14} />
            {error}
          </div>
        )}
      </div>

      {answer && (
        <div className="glass-card p-10 bg-accent-purple/10 border-accent-purple/20 animate-in fade-in zoom-in-95 duration-500">
          <header className="flex items-center gap-4 mb-6">
            <div className="bg-accent-purple/20 p-2.5 rounded-xl border border-accent-purple/30 text-accent-purple">
              <Brain size={20} />
            </div>
            <div>
              <h3 className="text-white font-black text-lg tracking-tight uppercase">
                AI Response
              </h3>
              <div className="text-[10px] text-text-secondary font-black uppercase tracking-[0.2em] opacity-40">
                Grounded Synthesis
              </div>
            </div>
          </header>
          <div className="text-white text-xl font-medium leading-relaxed italic border-l-4 border-accent-purple/30 pl-8 py-2">
            {answer}
          </div>
        </div>
      )}

      {/* Results Matrix */}
      <div className="grid grid-cols-1 gap-6">
        {results.length > 0 ? (
          results.map((result, idx) => (
            <button
              type="button"
              key={result.id}
              className="w-full text-left bg-transparent border-none glass-card p-8 hover:border-white/20 hover:bg-white/[0.04] transition-all animate-in slide-in-from-bottom-4 duration-500 group/item cursor-pointer"
              style={{ animationDelay: `${idx * 0.05}s` }}
              onClick={() => setSelectedResult(result)}
            >
              <header className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="bg-accent-blue/10 p-2.5 rounded-xl border border-accent-blue/20 text-accent-blue group-hover/item:scale-110 transition-transform">
                    <FileText size={18} />
                  </div>
                  <div>
                    <span className="text-white font-black text-base tracking-tight">
                      {result.filename}
                    </span>
                    <div className="text-xs text-text-secondary uppercase tracking-[0.2em] opacity-40">
                      Document Node
                    </div>
                  </div>
                </div>
                <div className="bg-white/5 px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3">
                  <span className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                    Relevance
                  </span>
                  <span className="text-xs font-black text-accent-blue/60 tabular-nums">
                    {(result.score * 100).toFixed(0)}%
                  </span>
                </div>
              </header>
              <div className="bg-black/20 rounded-2xl p-6 border border-white/5">
                <div className="text-text-secondary leading-relaxed font-medium text-lg italic opacity-80 group-hover/item:opacity-100 transition-opacity">
                  {result.content.split("\n").map((line) => (
                    <p key={line.slice(0, 50)} className="mt-4 first:mt-0">
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            </button>
          ))
        ) : query && !loading ? (
          <div className="py-32 flex flex-col items-center justify-center glass-card border-dashed opacity-50">
            <Activity size={48} className="text-white/5 mb-6" />
            <p className="text-text-secondary font-black uppercase tracking-[0.3em] text-xs">
              No fragments retrieved
            </p>
          </div>
        ) : (
          !loading && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {["History of TTS", "Hume Prosody", "FastEmbed Optimization"].map(
                (sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => setQuery(sample)}
                    className="glass-card p-10 group text-left hover:bg-accent-blue/5 hover:border-accent-blue/30 transition-all hover:-translate-y-1 shadow-lg"
                  >
                    <div className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40 mb-1 group-hover:text-accent-blue transition-colors">
                      Suggested Query
                    </div>
                    <div className="text-white font-black text-xl tracking-tighter group-hover:translate-x-1 transition-transform">
                      {sample}
                    </div>
                  </button>
                ),
              )}
            </div>
          )
        )}
      </div>

      {/* Reader Modal */}
      {selectedResult && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="glass-card w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
            <header className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-4">
                <div className="bg-accent-blue/10 p-3 rounded-2xl border border-accent-blue/20 text-accent-blue">
                  <FileText size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-white tracking-tighter">
                    {selectedResult.filename}
                  </h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-text-secondary font-black uppercase tracking-widest opacity-40">
                      Full Fragment Reader
                    </span>
                    <span className="w-1 h-1 rounded-full bg-accent-blue" />
                    <span className="text-xs text-accent-blue font-black tracking-widest uppercase">
                      {(selectedResult.score * 100).toFixed(1)}% Match
                    </span>
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedResult(null)}
                className="p-3 bg-white/5 border border-white/10 rounded-2xl text-text-secondary hover:text-white hover:bg-rose-500/20 hover:border-rose-500/30 transition-all active:scale-95"
              >
                <AlertCircle size={20} className="rotate-45" />
              </button>
            </header>

            <div className="flex-1 overflow-y-auto p-12 bg-black/40 custom-scrollbar">
              <div className="max-w-3xl mx-auto">
                <div className="text-text-secondary leading-relaxed font-medium text-xl whitespace-pre-wrap selection:bg-accent-blue/30 selection:text-white">
                  {selectedResult.content}
                </div>
              </div>
            </div>

            <footer className="p-6 border-t border-white/5 bg-white/[0.02] flex items-center justify-between">
              <div className="text-xs font-black text-text-secondary uppercase tracking-widest opacity-40">
                Semantic Retrieval
              </div>
              <button
                type="button"
                onClick={() => setSelectedResult(null)}
                className="bg-accent-blue hover:bg-accent-blue-hover text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest uppercase transition-all shadow-xl hover:scale-105 active:scale-95"
              >
                Close Reader
              </button>
            </footer>
          </div>
        </div>
      )}
    </div>
  );
};

export default SemanticSearch;
