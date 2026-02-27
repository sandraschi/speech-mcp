import React, { useState, useEffect } from 'react';
import { Search, Database, FileText, Activity, AlertCircle } from 'lucide-react';

interface SearchResult {
  filename: string;
  score: number;
  content: string;
}

interface RagStats {
  row_count: number;
  sources: string[];
}

const SemanticSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [stats, setStats] = useState<RagStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:10760/api/v1/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch RAG stats:', err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:10760/api/v1/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header & Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Semantic Memory Hub
          </h1>
          <p className="text-slate-400 mt-2">
            Deep-context retrieval across speech history and SOTA documentation.
          </p>
        </div>

        {stats && (
          <div className="flex gap-4">
            <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 p-4 rounded-2xl flex items-center gap-4">
              <div className="bg-blue-500/20 p-2 rounded-lg">
                <Database className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats.row_count}</div>
                <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Fragments</div>
              </div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 p-4 rounded-2xl flex items-center gap-4">
              <div className="bg-indigo-500/20 p-2 rounded-lg">
                <FileText className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats.sources.length}</div>
                <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Sources</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearch} className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 blur-xl group-focus-within:opacity-100 opacity-0 transition-opacity duration-500" />
        <div className="relative flex items-center bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden focus-within:border-blue-500/50 transition-all duration-300">
          <div className="pl-6 text-slate-500">
            <Search className="w-6 h-6" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about speech history, prosody, or modern AI patterns..."
            className="flex-1 bg-transparent border-none focus:ring-0 text-xl px-10 py-8 text-white placeholder-slate-600"
          />
          <button
            type="submit"
            disabled={loading}
            className="mr-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-12 py-5 rounded-xl font-bold transition-all duration-300 disabled:opacity-50 flex items-center gap-2 text-lg shadow-lg"
          >
            {loading ? <Activity className="w-6 h-6 animate-spin" /> : 'RETRIEVE'}
          </button>
        </div>
      </form>

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Results */}
      <div className="grid grid-cols-1 gap-6">
        {results.length > 0 ? (
          results.map((result, idx) => (
            <div
              key={idx}
              className="group bg-slate-900/50 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 transition-all duration-300 animate-slide-up"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="bg-slate-800 p-2 rounded-lg">
                    <FileText className="w-4 h-4 text-blue-400" />
                  </div>
                  <span className="text-sm font-medium text-slate-300">{result.filename}</span>
                </div>
                <div className="bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700">
                  <span className="text-xs font-bold text-slate-500 uppercase mr-2">Relevance</span>
                  <span className="text-sm font-mono text-blue-400">{(result.score * 100).toFixed(1)}%</span>
                </div>
              </div>
              <div className="text-slate-400 leading-relaxed font-light">
                {result.content.split('\n').map((line, i) => (
                  <p key={i} className={i > 0 ? 'mt-2' : ''}>
                    {line}
                  </p>
                ))}
              </div>
            </div>
          ))
        ) : query && !loading ? (
          <div className="text-center py-20 bg-slate-900/30 rounded-3xl border border-dashed border-slate-800">
            <p className="text-slate-500">No fragments found for this query.</p>
          </div>
        ) : !loading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['History of TTS', 'Hume Prosody', 'FastEmbed Optimization'].map((sample) => (
              <button
                key={sample}
                onClick={() => {
                  setQuery(sample);
                  // Trigger search manually since we're just updating state here
                }}
                className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl text-left hover:bg-slate-800 transition-colors group"
              >
                <div className="text-xs font-bold text-slate-500 uppercase mb-2 group-hover:text-blue-400">Suggested</div>
                <div className="text-slate-400 font-medium">{sample}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SemanticSearch;
