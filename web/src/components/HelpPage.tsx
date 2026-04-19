import {
  ChevronDown,
  ChevronRight,
  Cloud,
  ExternalLink,
  HelpCircle,
  Mic,
  Monitor,
} from "lucide-react";
import type React from "react";
import { useState } from "react";

const HelpPage: React.FC = () => {
  return (
    <div className="max-w-4xl space-y-8 animate-in fade-in duration-500">
      <header>
        <h2 className="text-3xl font-black text-white tracking-tighter">
          Documentation & Help
        </h2>
        <p className="text-slate-400">
          Speech MCP: EVI, TTS, RAG, and MCP tools. Use the sections below to
          expand details.
        </p>
      </header>

      <Section title="Speech service providers" defaultOpen>
        <p className="text-slate-400 text-sm mb-4">
          All three providers are supported by the{" "}
          <code className="text-accent-purple">text_to_speech</code> and stream
          endpoints. Configure API keys in Settings.
        </p>
        <ProviderDoc
          name="Hume AI"
          envKey="HUME_API_KEY"
          docsUrl="https://www.hume.ai/docs"
          features={[
            "EVI (Empathic Voice Interface) real-time conversation",
            "Octave TTS with emotional prosody",
            "Streaming audio",
            "Voice IDs: ito, kora (and config-dependent)",
          ]}
          notes="Required for EVI sessions and Hume TTS. Get keys at beta.hume.ai. HUME_CONFIG_ID is needed for EVI."
        />
        <ProviderDoc
          name="Gemini 3.1 Flash"
          envKey="GOOGLE_API_KEY"
          docsUrl="https://ai.google.dev/gemini-api/docs"
          features={[
            "Powerful Emotional Synthesis (Natural Language Tags)",
            "Dozens of supported languages (Kiswahili, Hindi, etc.)",
            "Native Barge-in (Server-side VAD)",
          ]}
          notes="Recommended for emotional performance. Wipes the floor with competition in prosody. Get API key at aistudio.google.com."
        />
        <ProviderDoc
          name="ElevenLabs"
          envKey="ELEVENLABS_API_KEY"
          docsUrl="https://elevenlabs.io/docs"
          features={[
            "High-fidelity TTS and professional voice cloning",
            "Turbo v2.5 for 2026 conversations",
            "Elite stability",
          ]}
          notes="Optional. Use for best audio quality and PVC. Key from elevenlabs.io."
        />
        <ProviderDoc
          name="Windows (SAPI5)"
          envKey="—"
          docsUrl=""
          features={[
            "Built-in OS TTS, no key required",
            "Works offline",
            "Single default system voice",
          ]}
          notes="Always available. Use when no API keys are set or for local fallback."
        />
      </Section>

      <Section title="Quick start">
        <ul className="list-disc list-inside text-slate-400 text-sm space-y-1">
          <li>
            Set API keys in Settings (Hume, ElevenLabs) if you want cloud TTS.
          </li>
          <li>
            Start an EVI session from EVI Session or use Octave TTS from the TTS
            page.
          </li>
          <li>
            Use Semantic Search to query the RAG knowledge base (ingest via MCP
            tools).
          </li>
          <li>
            System Logs shows real-time backend telemetry; filter by level or
            export.
          </li>
        </ul>
      </Section>

      <Section title="API reference">
        <p className="text-slate-400 text-sm mb-2">
          REST: <code className="text-accent-purple">GET /api/v1/health</code>,{" "}
          <code className="text-accent-purple">/api/v1/voices</code>,{" "}
          <code className="text-accent-purple">/api/v1/stats</code>,{" "}
          <code className="text-accent-purple">/api/v1/search</code>,{" "}
          <code className="text-accent-purple">POST /api/v1/tts/wav</code>,{" "}
          <code className="text-accent-purple">/api/v1/utility</code>,{" "}
          <code className="text-accent-purple">/api/v1/agentic</code>.
        </p>
        <p className="text-slate-400 text-sm">
          WebSockets: <code className="text-accent-purple">/ws/stream</code>{" "}
          (TTS stream), <code className="text-accent-purple">/ws/logs</code>{" "}
          (log viewer). Auth via{" "}
          <code className="text-accent-purple">X-Speech-MCP-Auth</code> header
          or <code className="text-accent-purple">token</code> query param when{" "}
          <code className="text-accent-purple">SPEECH_MCP_AUTH_TOKEN</code> is
          set.
        </p>
      </Section>

      <Section title="Semantic memory (RAG)">
        <p className="text-slate-400 text-sm">
          Use the Semantic page to search the LanceDB vector store. Documents
          are indexed via MCP tools. Default embedding: BAAI/bge-small-en-v1.5.
          Data path: <code className="text-accent-purple">data/lancedb/</code>.
        </p>
      </Section>

      <Section title="Gemini audio tags (Emotion Cheat Sheet)">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <TagItem tag="[whispers]" desc="Breathiness & intimacy" />
          <TagItem tag="[happy]" desc="Bright & energetic" />
          <TagItem tag="[shouts]" desc="Loud & proyecting" />
          <TagItem tag="[sad]" desc="Downward & empathetic" />
          <TagItem tag="[serious]" desc="Flattened & authoritative" />
          <TagItem tag="[confused]" desc="Hesitant & inquisitive" />
        </div>
        <p className="mt-4 text-xs text-slate-500 italic">
          Example: "[happy] Hello! [whispers] Let's keep this quiet..."
        </p>
      </Section>

      <Section title="Barge-in & Interrupts">
        <p className="text-slate-400 text-sm mb-3">
          Refined conversational flow requires immediate feedback. Speech-MCP
          implements two levels of interruption:
        </p>
        <ul className="list-disc list-inside text-slate-400 text-sm space-y-2">
          <li>
            <strong>Native Barge-in (Gemini)</strong>: The server automatically
            stops generating if it detects yours voice (Server-side VAD).
          </li>
          <li>
            <strong>Global Interrupt</strong>: Clicking the Stop button in the
            playback widget sends a{" "}
            <code className="text-accent-purple">
              {'{"type": "interrupt"}'}
            </code>{" "}
            signal to kill the active stream instantly.
          </li>
        </ul>
      </Section>

      <Section title="Prosody and emotion">
        <p className="text-slate-400 text-sm">
          Gemini leads the fleet with Natural Language Tags and excellent
          emotional mastery. Hume supports configuration-based emotional hints.
          ElevenLabs uses stability/similarity sliders.
        </p>
      </Section>

      <Section title="Log viewer">
        <p className="text-slate-400 text-sm">
          System Logs (sidebar) shows live entries from the backend over{" "}
          <code className="text-accent-purple">/ws/logs</code>. Filter by level
          (INFO, WARN, ERROR, DEBUG), search text, and export to file. Entries
          are kept in memory (last N) and are not persisted to disk by the UI.
        </p>
      </Section>

      <Section title="Testing and logging (backend)">
        <p className="text-slate-400 text-sm mb-2">
          Tests: <code className="text-accent-purple">pytest tests/</code> (see{" "}
          <code className="text-accent-purple">docs/TESTING.md</code>). Logging:
          Python logging to stdout and to the in-memory queue broadcast via
          WebSocket; see{" "}
          <code className="text-accent-purple">docs/LOGGING.md</code> for levels
          and structure.
        </p>
      </Section>

      <section className="glass-card p-8 space-y-6">
        <h3 className="text-xl font-bold flex items-center gap-3">
          <HelpCircle className="text-indigo-500" />
          Frequently asked questions
        </h3>
        <div className="space-y-4">
          <FaqItem
            q="Why is the EVI session returning 'simulated'?"
            a="Check HUME_API_KEY and HUME_CONFIG_ID in Settings. If missing or invalid, the substrate falls back to simulation."
          />
          <FaqItem
            q="How do I use local LLMs like Ollama?"
            a="Ensure Ollama is running (e.g. port 11434). Configure in Settings if the app supports an Ollama provider."
          />
          <FaqItem
            q="Is my voice data stored?"
            a="By default voice tokens are transient. Only interactions saved to Semantic Memory are persisted in LanceDB."
          />
          <FaqItem
            q="Backend shows offline?"
            a="Ensure the backend is running on the port the frontend expects (default 10918). Set VITE_API_URL in web/.env if you use a different port."
          />
        </div>
      </section>

      <footer className="flex justify-center gap-8 py-8 opacity-40 text-sm">
        <a
          href="https://github.com/sandraschi/speech-mcp"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 hover:opacity-100 transition-opacity"
        >
          <ExternalLink size={14} /> Repo
        </a>
        <span className="text-slate-500">Speech MCP</span>
      </footer>
    </div>
  );
};

function Section({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="glass-card overflow-hidden">
      <button
        type="button"
        className="w-full p-6 flex items-center justify-between text-left hover:bg-white/[0.03] transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="font-bold text-lg text-white">{title}</span>
        {open ? (
          <ChevronDown size={20} className="text-slate-400" />
        ) : (
          <ChevronRight size={20} className="text-slate-400" />
        )}
      </button>
      {open && (
        <div className="px-6 pb-6 pt-0 border-t border-white/5">{children}</div>
      )}
    </div>
  );
}

function ProviderDoc({
  name,
  envKey,
  docsUrl,
  features,
  notes,
}: {
  name: string;
  envKey: string;
  docsUrl: string;
  features: string[];
  notes: string;
}) {
  const Icon = name.startsWith("Hume")
    ? Mic
    : name.startsWith("Eleven")
      ? Cloud
      : Monitor;
  return (
    <div className="mb-6 p-4 rounded-xl bg-white/[0.03] border border-white/5">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={18} className="text-accent-purple" />
        <h4 className="font-bold text-white">{name}</h4>
        {envKey !== "—" && (
          <span className="text-xs text-slate-500 font-mono">{envKey}</span>
        )}
        {docsUrl && (
          <a
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-accent-blue flex items-center gap-1 ml-auto"
          >
            Docs <ExternalLink size={12} />
          </a>
        )}
      </div>
      <ul className="list-disc list-inside text-slate-400 text-sm mb-2">
        {features.map((f) => (
          <li key={`${name}-${f.replace(/\s+/g, "-")}`}>{f}</li>
        ))}
      </ul>
      <p className="text-slate-500 text-xs">{notes}</p>
    </div>
  );
}

const FaqItem = ({ q, a }: { q: string; a: string }) => (
  <div className="border-b border-slate-800 pb-4 last:border-0 last:pb-0">
    <h4 className="text-indigo-400 font-bold mb-2 text-sm">Q: {q}</h4>
    <p className="text-slate-400 text-sm leading-relaxed">{a}</p>
  </div>
);

const TagItem = ({ tag, desc }: { tag: string; desc: string }) => (
  <div className="bg-white/[0.02] border border-white/5 p-3 rounded-lg">
    <code className="text-accent-blue text-xs font-black block mb-1">
      {tag}
    </code>
    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
      {desc}
    </span>
  </div>
);

export default HelpPage;
