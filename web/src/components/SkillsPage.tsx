import { BookOpen, ChevronRight, FileText } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { BACKEND } from "../api";

interface SkillMeta {
  name: string;
  description: string;
}

const SkillsPage: React.FC = () => {
  const [skills, setSkills] = useState<SkillMeta[] | null>(null);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string | null>(null);
  const [contentError, setContentError] = useState(false);

  useEffect(() => {
    fetch(`${BACKEND}/api/skills`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          setSkills(data.skills);
          if (data.skills.length > 0) setSelected(data.skills[0].name);
        } else {
          setError(true);
        }
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setContent(null);
    setContentError(false);
    fetch(`${BACKEND}/api/skills/${selected}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success) setContent(data.content);
        else setContentError(true);
      })
      .catch(() => setContentError(true));
  }, [selected]);

  return (
    <div className="space-y-6" data-testid="skills-page">
      <header>
        <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
          Skills
        </h1>
        <p className="text-sm text-white/50 uppercase tracking-widest mt-1">
          How to use this server — skill documents for agents and humans
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-4 space-y-2 lg:col-span-1">
          {error ? (
            <div className="text-xs text-rose-400 font-bold">
              Could not load skills.
            </div>
          ) : skills === null ? (
            <div className="text-xs text-white/30 animate-pulse">Loading…</div>
          ) : skills.length === 0 ? (
            <div className="text-xs text-white/40">
              No skills installed yet.
            </div>
          ) : (
            skills.map((s) => (
              <button
                key={s.name}
                type="button"
                onClick={() => setSelected(s.name)}
                className={`w-full text-left flex items-start gap-3 p-3 rounded-xl border transition-all ${
                  selected === s.name
                    ? "bg-accent-purple/10 border-accent-purple/30"
                    : "bg-white/[0.02] border-white/5 hover:bg-white/[0.05]"
                }`}
              >
                <BookOpen
                  size={16}
                  className="mt-0.5 text-accent-purple flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-mono font-bold text-sm text-white truncate">
                    {s.name}
                  </div>
                  <div className="text-xs text-white/50 mt-0.5 leading-snug">
                    {s.description}
                  </div>
                </div>
                <ChevronRight
                  size={14}
                  className="text-white/20 flex-shrink-0 mt-1"
                />
              </button>
            ))
          )}
        </div>

        <div className="lg:col-span-2 glass-card p-6 overflow-hidden">
          {selected === null ? (
            <div className="text-xs text-white/30">
              Select a skill to read it.
            </div>
          ) : contentError ? (
            <div className="text-xs text-rose-400 font-bold">
              Failed to load skill content.
            </div>
          ) : content === null ? (
            <div className="text-xs text-white/30 animate-pulse">Loading…</div>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-4 text-xs text-white/40 uppercase tracking-widest">
                <FileText size={13} />
                <span className="font-mono">{selected}</span>
              </div>
              <article className="prose prose-invert prose-sm max-w-none text-slate-300">
                <ReactMarkdown>{content}</ReactMarkdown>
              </article>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SkillsPage;
