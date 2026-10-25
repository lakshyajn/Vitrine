import { useState, useEffect, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ExternalLink,
  Mail,
  CheckCircle,
  XCircle,
  Sparkles,
  HelpCircle,
  AlertTriangle,
  Bookmark,
} from "lucide-react";
import {
  getLead,
  updateLead,
  getLeadEvidence,
  type Lead,
  type EvidenceItem,
} from "@/api";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { EvidenceCard } from "@/components/shared/EvidenceCard";
import { DemoBadge } from "@/components/shared/DemoBadge";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [lead, setLead] = useState<Lead | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Seller notes
  const [notes, setNotes] = useState("");
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [notesSavedAlert, setNotesSavedAlert] = useState(false);

  const fetchLeadData = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [leadData, evData] = await Promise.all([
        getLead(id),
        getLeadEvidence(id),
      ]);
      setLead(leadData);
      setNotes(leadData.notes || "");
      setEvidence(evData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load lead details.");
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchLeadData();
  }, [fetchLeadData]);

  const handleUpdateStatus = async (status: "saved" | "rejected" | "contacted" | "new") => {
    if (!id || !lead) return;
    try {
      const updated = await updateLead(id, { review_status: status });
      setLead(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update review status");
    }
  };

  const handleSaveNotes = async () => {
    if (!id || !lead) return;
    setIsSavingNotes(true);
    try {
      const updated = await updateLead(id, { notes: notes.trim() });
      setLead(updated);
      setNotesSavedAlert(true);
      setTimeout(() => setNotesSavedAlert(false), 2000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save notes");
    } finally {
      setIsSavingNotes(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <LoadingSkeleton variant="detail" />
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ErrorState
          message={error || "Lead not found"}
          onRetry={fetchLeadData}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Top Navigation */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <Link
            to="/app/leads"
            className="flex size-9 items-center justify-center rounded-xl border border-border bg-surface text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
                {lead.name}
              </h1>
              <span className="rounded bg-surface-subtle px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-muted border border-border">
                {lead.retailer_type}
              </span>
              {lead.is_demo && <DemoBadge />}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted">
              {lead.location && (
                <span>
                  {[lead.location.city, lead.location.country].filter(Boolean).join(", ")}
                </span>
              )}
              <span>·</span>
              <a
                href={lead.website}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-mono text-primary hover:underline"
              >
                <span>{lead.canonical_domain}</span>
                <ExternalLink className="size-3" />
              </a>
              {lead.website_verified ? (
                <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                  <CheckCircle className="size-3" /> Verified Domain
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
                  <AlertTriangle className="size-3" /> Unverified Website
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Status buttons */}
          {lead.review_status !== "saved" && (
            <button
              type="button"
              onClick={() => handleUpdateStatus("saved")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors shadow-xs"
            >
              <Bookmark className="size-3.5" />
              <span>Save Lead</span>
            </button>
          )}

          {lead.review_status !== "rejected" && (
            <button
              type="button"
              onClick={() => handleUpdateStatus("rejected")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-white px-3 py-2 text-xs font-semibold text-rose-800 hover:bg-rose-50 transition-colors shadow-xs"
            >
              <XCircle className="size-3.5" />
              <span>Reject</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => navigate(`/app/outreach/${lead.id}`)}
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
          >
            <Mail className="size-4" />
            <span>Open in Outreach Studio</span>
          </button>
        </div>
      </div>

      {/* Duplicate Alert (DECISION-D9) */}
      {lead.duplicate_of && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-4 text-amber-700 flex-shrink-0" />
            <span>
              This retailer domain was detected as a secondary branch or duplicate of an existing primary lead.
            </span>
          </div>
          <Link
            to={`/app/leads/${lead.duplicate_of}`}
            className="font-semibold underline text-amber-950 hover:text-amber-800"
          >
            View Primary Lead
          </Link>
        </div>
      )}

      {/* Priority Score Overview Card */}
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
          <div>
            <h2 className="font-display text-base font-semibold text-ink">
              Priority Fit Score Breakdown
            </h2>
            <p className="text-xs text-muted">
              Evidence-based dimensional scoring evaluating catalog, aesthetic, and commercial compatibility.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Tier:</span>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                lead.tier === "qualified"
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : lead.tier === "needs_review"
                  ? "bg-amber-100 text-amber-800 border border-amber-300"
                  : "bg-rose-100 text-rose-800 border border-rose-300"
              }`}
            >
              {lead.tier.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Score Bars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <ScoreBar
            label="Overall Priority Score"
            score={lead.scores.overall}
            description="Composite weighting across category alignment, aesthetic affinity, and seller terms."
          />
          <ScoreBar
            label="Category Fit"
            score={lead.scores.category_fit}
            dimensionLabel={lead.assessment?.category_fit.label}
            description="Inventory alignment with maker's product category and accessories department."
          />
          <ScoreBar
            label="Aesthetic Fit"
            score={lead.scores.aesthetic_fit}
            dimensionLabel={lead.assessment?.aesthetic_fit.label}
            description="Alignment with maker's botanical, artisanal, and slow-craft aesthetic."
          />
          <ScoreBar
            label="Seller Compatibility"
            score={lead.scores.seller_compat}
            dimensionLabel={lead.assessment?.seller_compat.label}
            description="Match on minimum order quantity (MOQ), wholesale pricing, and lead times."
          />
        </div>

        {/* Tier Reasons list */}
        {lead.scores.tier_reasons.length > 0 && (
          <div className="mt-4 rounded-xl border border-border-subtle bg-surface-subtle/40 p-4 space-y-1.5">
            <span className="text-xs font-semibold text-ink">Tier Justification & Findings:</span>
            <ul className="list-disc pl-4 space-y-1 text-xs text-muted">
              {lead.scores.tier_reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* AI Assessment & Unknowns */}
      {lead.assessment && (
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <h2 className="font-display text-base font-semibold text-ink">
              Retailer Synthesis & Assessment
            </h2>
          </div>

          <p className="text-xs leading-relaxed text-ink bg-canvas p-3.5 rounded-xl border border-border">
            {lead.assessment.summary}
          </p>

          {/* Dimension Details */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="rounded-xl border border-border p-3 space-y-1.5">
              <span className="text-[11px] font-semibold uppercase text-muted">Category Alignment</span>
              <ul className="text-xs space-y-1 text-muted">
                {lead.assessment.category_fit.reasons.map((r, i) => (
                  <li key={i}>• {r}</li>
                ))}
              </ul>
            </div>

            <div className="rounded-xl border border-border p-3 space-y-1.5">
              <span className="text-[11px] font-semibold uppercase text-muted">Aesthetic Vector</span>
              <ul className="text-xs space-y-1 text-muted">
                {lead.assessment.aesthetic_fit.reasons.map((r, i) => (
                  <li key={i}>• {r}</li>
                ))}
              </ul>
            </div>

            <div className="rounded-xl border border-border p-3 space-y-1.5">
              <span className="text-[11px] font-semibold uppercase text-muted">Wholesale Fit</span>
              <ul className="text-xs space-y-1 text-muted">
                {lead.assessment.seller_compat.reasons.map((r, i) => (
                  <li key={i}>• {r}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Missing evidence / Unknowns callout */}
          {lead.assessment.unknowns.length > 0 && (
            <div className="rounded-xl border border-border bg-surface-subtle/50 p-3.5 space-y-1 text-xs">
              <div className="flex items-center gap-1.5 text-muted font-semibold">
                <HelpCircle className="size-3.5" />
                <span>Unverified Fields & Information Gaps:</span>
              </div>
              <ul className="list-disc pl-4 space-y-0.5 text-muted text-[11px]">
                {lead.assessment.unknowns.map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Cultural Affinity Signals (Qloo Integration) */}
      {lead.cultural_affinity && (
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-purple-600" />
              <h2 className="font-display text-base font-semibold text-ink">
                Qloo Cultural Taste Affinity
              </h2>
            </div>
            {lead.cultural_affinity.is_demo && <DemoBadge />}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {lead.cultural_affinity.signals.map((sig, idx) => (
              <div key={idx} className="rounded-xl border border-purple-100 bg-purple-50/50 p-3.5 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-purple-950">
                    {String(sig.entity_name || "Boutique Affinity")}
                  </span>
                  {sig.affinity_score !== undefined && (
                    <span className="rounded bg-purple-200/70 px-2 py-0.5 text-[10px] font-bold text-purple-900">
                      {Math.round(Number(sig.affinity_score) * 100)}% Affinity
                    </span>
                  )}
                </div>
                {Array.isArray(sig.correlated_categories) && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {sig.correlated_categories.map((cat, i) => (
                      <span key={i} className="rounded bg-white px-2 py-0.5 text-[10px] text-purple-800 border border-purple-200">
                        {String(cat)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verified Web Evidence Section */}
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div>
            <h2 className="font-display text-base font-semibold text-ink">
              Verified Web Evidence ({evidence.length})
            </h2>
            <p className="text-xs text-muted">
              Direct citations extracted from official stockist web pages and catalogs.
            </p>
          </div>
        </div>

        {evidence.length === 0 ? (
          <p className="text-xs text-muted italic">No external web citations logged for this record.</p>
        ) : (
          <div className="space-y-3">
            {evidence.map((ev) => (
              <EvidenceCard key={ev.id} evidence={ev} />
            ))}
          </div>
        )}
      </div>

      {/* Seller Private Notes */}
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
        <h2 className="font-display text-base font-semibold text-ink">Internal Seller Notes</h2>
        <textarea
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Record buyer names, upcoming trunk show dates, or showroom visit impressions..."
          className="w-full rounded-xl border border-border bg-canvas p-3.5 text-xs text-ink placeholder:text-subtle focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
        />
        <div className="flex items-center justify-between">
          {notesSavedAlert ? (
            <span className="text-xs font-semibold text-emerald-700 animate-fade-in">
              ✓ Notes saved successfully
            </span>
          ) : <span />}
          <button
            type="button"
            disabled={isSavingNotes}
            onClick={handleSaveNotes}
            className="rounded-xl border border-border bg-surface px-4 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors shadow-xs"
          >
            {isSavingNotes ? "Saving..." : "Save Notes"}
          </button>
        </div>
      </div>
    </div>
  );
}

