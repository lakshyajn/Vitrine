import { ExternalLink, CheckCircle, AlertCircle, Calendar } from "lucide-react";
import { ProvenanceTag, type ProvenanceType } from "./ProvenanceTag";
import { DemoBadge } from "./DemoBadge";

export interface EvidenceItemData {
  id: string;
  lead_id?: string;
  url: string;
  excerpt: string;
  source_type: string;
  retrieved_at: string;
  published_at?: string | null;
  domain_matches_lead: boolean;
  provenance: ProvenanceType;
  is_demo?: boolean;
}

interface EvidenceCardProps {
  evidence: EvidenceItemData;
  className?: string;
}

export function EvidenceCard({ evidence, className = "" }: EvidenceCardProps) {
  // Format dates safely
  const formattedDate = evidence.retrieved_at
    ? new Date(evidence.retrieved_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <div
      className={`rounded-xl border border-border bg-surface p-4 shadow-card transition-all hover:border-border-strong ${className}`}
    >
      {/* Top Header: Source type + Domain Match + Provenance */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded bg-surface-subtle px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-muted border border-border">
            {evidence.source_type.replace("_", " ")}
          </span>

          {evidence.domain_matches_lead ? (
            <span
              className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700"
              title="URL domain verified against retailer primary domain"
            >
              <CheckCircle className="size-3" aria-hidden="true" />
              Domain matches
            </span>
          ) : (
            <span
              className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700"
              title="Secondary or external domain mention"
            >
              <AlertCircle className="size-3" aria-hidden="true" />
              Secondary source
            </span>
          )}

          {evidence.is_demo && <DemoBadge />}
        </div>

        <ProvenanceTag provenance={evidence.provenance} />
      </div>

      {/* Excerpt: strictly plain text in pre-wrap block */}
      <div className="mt-3">
        <blockquote className="rounded-lg border-l-2 border-primary/40 bg-surface-subtle/40 p-3 text-xs leading-relaxed text-ink italic">
          "{evidence.excerpt}"
        </blockquote>
      </div>

      {/* Footer: Safe external link & Timestamp */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        <a
          href={evidence.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-mono text-[11px] text-primary hover:underline"
          title={evidence.url}
        >
          <span className="max-w-[280px] sm:max-w-md truncate">{evidence.url}</span>
          <ExternalLink className="size-3 flex-shrink-0" aria-hidden="true" />
        </a>

        {formattedDate && (
          <span className="inline-flex items-center gap-1 text-[11px] text-subtle">
            <Calendar className="size-3" aria-hidden="true" />
            Retrieved {formattedDate}
          </span>
        )}
      </div>
    </div>
  );
}
