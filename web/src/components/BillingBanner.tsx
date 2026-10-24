import { ExternalLink, Wallet } from "lucide-react";

export const GOOGLE_BILLING_URL = "https://ai.studio/projects";
const BILLING_DOCS_URL = "https://ai.google.dev/gemini-api/docs/billing";

/** True when an error string smells like an empty Google AI Studio wallet. */
export function isBillingError(message: string | null | undefined): boolean {
  if (!message) return false;
  return /prepayment|prepay|resource_exhausted|billing|402/.test(
    message.toLowerCase(),
  );
}

/**
 * Loud billing failure: Google 402 (prepaid credits depleted) is a wallet
 * state, not a bug. Shows what happened, links the AI Studio payment page,
 * and points at providers that still work. Never fail silently.
 */
export default function BillingBanner({ message }: { message?: string }) {
  return (
    <div className="glass-card p-5 border border-amber-500/30 bg-amber-500/[0.06]">
      <div className="flex items-center gap-3 mb-2">
        <div className="bg-amber-500/10 p-2.5 rounded-xl border border-amber-500/20 text-amber-400">
          <Wallet size={18} />
        </div>
        <h3 className="text-base font-black text-white uppercase tracking-tight">
          Google AI Studio wallet is empty (402)
        </h3>
      </div>
      <p className="text-sm text-white/60 leading-relaxed">
        Gemini speech is disabled until prepayment credits are topped up. Hume,
        ElevenLabs, and local providers still work — switch provider instead of
        retrying.
      </p>
      {message && (
        <details className="mt-3">
          <summary className="text-xs font-bold text-white/40 uppercase tracking-widest cursor-pointer hover:text-white/60">
            Provider error
          </summary>
          <p className="mt-2 text-xs font-mono text-white/50 break-words">
            {message}
          </p>
        </details>
      )}
      <div className="flex flex-wrap gap-3 mt-4">
        <a
          href={GOOGLE_BILLING_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm font-bold text-white bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 px-4 py-2 rounded-xl transition-all"
        >
          Top up at AI Studio <ExternalLink size={14} />
        </a>
        <a
          href={BILLING_DOCS_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm font-bold text-white/60 hover:text-white px-4 py-2 transition-all"
        >
          Billing docs <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}
