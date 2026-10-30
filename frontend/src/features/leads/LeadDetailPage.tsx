import { useState, useEffect, useCallback, useRef } from "react";
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
  Copy,
} from "lucide-react";
import {
  getLead,
  updateLead,
  getLeadEvidence,
  scrapeLeadContact,
  type Lead,
  type EvidenceItem,
} from "@/api";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { EvidenceCard } from "@/components/shared/EvidenceCard";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ConfirmationModal } from "@/components/shared/Modal";

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
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [isScrapingContact, setIsScrapingContact] = useState(false);

  const handleScrapeContact = async () => {
    if (!id || !lead) return;
    setIsScrapingContact(true);
    try {
      const res = await scrapeLeadContact(id);
      if (res.email) {
        setLead({ ...lead, contact_email: res.email });
      }
    } catch (e) {
      console.warn("Scraping contact failed", e);
    } finally {
      setIsScrapingContact(false);
    }
  };

  // Reject confirmation modal
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchLeadData = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [leadData, evData] = await Promise.all([
        getLead(id),
        getLeadEvidence(id),
      ]);
      if (!isMountedRef.current) return;
      setLead(leadData);
      setNotes(leadData.notes || "");
      setEvidence(evData);
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      setError(err instanceof Error ? err.message : "Failed to load lead details.");
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
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
      setError(err instanceof Error ? err.message : "Failed to update review status");
    }
  };

  const handleConfirmReject = async () => {
    if (!id || !lead || isRejecting) return;
    setIsRejecting(true);
    try {
      const updated = await updateLead(id, { review_status: "rejected" });
      setLead(updated);
      setShowRejectModal(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reject lead.");
    } finally {
      setIsRejecting(false);
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
      setError(err instanceof Error ? err.message : "Failed to save notes");
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
              {(lead.retailer_kind && lead.retailer_kind !== "unknown") ? (
                <span className="rounded bg-surface-subtle px-2 py-0.5 text-xs font-semibold capitalize tracking-wider text-muted border border-border">
                  {lead.retailer_kind.replace("_", " ")}
                </span>
              ) : (lead.retailer_type && lead.retailer_type !== "unknown" && lead.retailer_type !== "boutique") ? (
                <span className="rounded bg-surface-subtle px-2 py-0.5 text-xs font-semibold capitalize tracking-wider text-muted border border-border">
                  {lead.retailer_type}
                </span>
              ) : null}
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
              <span>·</span>
              {lead.contact_email ? (
                <div className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface-subtle px-2 py-0.5 text-xs font-mono text-ink">
                  <Mail className="size-3 text-primary" />
                  <a
                    href={`mailto:${lead.contact_email}`}
                    className="hover:underline text-primary"
                    title="Draft email in default mail client"
                  >
                    {lead.contact_email}
                  </a>
                  <span className="rounded bg-emerald-100 px-1.5 py-0.2 text-[10px] font-sans font-semibold text-emerald-800">
                    Tavily Verified
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(lead.contact_email!);
                      setCopiedEmail(true);
                      setTimeout(() => setCopiedEmail(false), 2000);
                    }}
                    className="ml-1 text-primary hover:underline flex items-center gap-0.5 text-[11px]"
                    title="Copy contact email"
                  >
                    {copiedEmail ? <span className="text-emerald-700 font-sans">Copied!</span> : <Copy className="size-3" />}
                  </button>
                  <button
                    type="button"
                    disabled={isScrapingContact}
                    onClick={handleScrapeContact}
                    className="ml-1 text-primary hover:underline text-[11px] font-sans font-semibold flex items-center gap-1"
                    title="Re-scrape official recipient email with Tavily"
                  >
                    <Sparkles className={`size-3 text-purple-600 ${isScrapingContact ? "animate-spin" : ""}`} />
                    <span>{isScrapingContact ? "Scraping..." : "Re-scrape (Tavily)"}</span>
                  </button>
                </div>
              ) : (
                <div className="inline-flex items-center gap-2">
                  <span className="text-xs text-muted italic">No contact email found</span>
                  <button
                    type="button"
                    disabled={isScrapingContact}
                    onClick={handleScrapeContact}
                    className="rounded border border-border bg-surface px-2 py-0.5 text-xs font-medium text-primary hover:bg-surface-subtle flex items-center gap-1"
                    title="Scrape official recipient email with Tavily"
                  >
                    <Sparkles className={`size-3 text-purple-600 ${isScrapingContact ? "animate-spin" : ""}`} />
                    <span>{isScrapingContact ? "Scraping..." : "Scrape Email (Tavily)"}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Contacted status toggle */}
          {lead.review_status === "contacted" ? (
            <button
              type="button"
              onClick={() => handleUpdateStatus("new")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition-colors shadow-xs"
              title="Currently marked as Contacted. Click to reset."
            >
              <CheckCircle className="size-3.5 text-emerald-600" />
              <span>Contacted ✓</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleUpdateStatus("contacted")}
              className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50/60 px-3 py-2 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition-colors shadow-xs"
              title="Mark as Contacted"
            >
              <CheckCircle className="size-3.5 text-emerald-600" />
              <span>Mark as Contacted</span>
            </button>
          )}

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
              onClick={() => setShowRejectModal(true)}
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
              {(lead.tier || "needs_review").replace("_", " ")}
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
            description="Alignment with maker's aesthetic candidates and design vocabulary."
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
            <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-800 border border-emerald-200">
              <Sparkles className="size-3 text-emerald-600" />
              <span>NVIDIA Nemotron 3.5 Super VL • Nebius Token Factory</span>
            </span>
          </div>

          <p className="text-xs leading-relaxed text-ink bg-canvas p-3.5 rounded-xl border border-border">
            {lead.assessment.summary}
          </p>

          {/* Dimension Details: Only show dimensions that have verified findings */}
          {(() => {
            const hasCat = lead.assessment.category_fit.reasons.length > 0;
            const hasAes = lead.assessment.aesthetic_fit.reasons.length > 0;
            const hasWho = lead.assessment.seller_compat.reasons.length > 0;
            const activeCount = [hasCat, hasAes, hasWho].filter(Boolean).length;

            if (activeCount === 0) return null;

            return (
              <div
                className={`grid grid-cols-1 ${
                  activeCount === 3
                    ? "sm:grid-cols-3"
                    : activeCount === 2
                    ? "sm:grid-cols-2"
                    : ""
                } gap-4 pt-2`}
              >
                {hasCat && (
                  <div className="rounded-xl border border-border p-3 space-y-1.5">
                    <span className="text-[11px] font-semibold uppercase text-muted">Category Alignment</span>
                    <ul className="text-xs space-y-1 text-muted">
                      {lead.assessment.category_fit.reasons.map((r, i) => (
                        <li key={i}>• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {hasAes && (
                  <div className="rounded-xl border border-border p-3 space-y-1.5">
                    <span className="text-[11px] font-semibold uppercase text-muted">Aesthetic Vector</span>
                    <ul className="text-xs space-y-1 text-muted">
                      {lead.assessment.aesthetic_fit.reasons.map((r, i) => (
                        <li key={i}>• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {hasWho && (
                  <div className="rounded-xl border border-border p-3 space-y-1.5">
                    <span className="text-[11px] font-semibold uppercase text-muted">Wholesale Fit</span>
                    <ul className="text-xs space-y-1 text-muted">
                      {lead.assessment.seller_compat.reasons.map((r, i) => (
                        <li key={i}>• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })()}

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

      {/* Cultural Affinity Signals (Qloo Integration): Deduplicated and capped to top unique signals */}
      {(() => {
        const rawSignals = (lead.cultural_affinity?.signals || []) as Array<{
          type?: string;
          text?: string;
          entity_name?: string;
          affinity_score?: number;
          source_ref?: string;
          correlated_categories?: string[];
          [key: string]: unknown;
        }>;

        if (!rawSignals.length) return null;

        // Deduplicate signals by text or label to prevent repetitive wall of identical cards
        const uniqueSignals = Array.from(
          new Map(
            rawSignals.map((s) => [
              (s.text || s.entity_name || s.type || "").trim(),
              s,
            ])
          ).values()
        )
          .filter((s) => (s.text && s.text.trim().length > 0) || Boolean(s.entity_name))
          .slice(0, 3);

        if (uniqueSignals.length === 0) return null;

        return (
          <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="size-4 text-purple-600" />
                <h2 className="font-display text-base font-semibold text-ink">
                  Audience Taste & Shopper Affinity
                </h2>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {uniqueSignals.map((sig, idx) => {
                const title: string =
                  sig.entity_name ||
                  (sig.type ? String(sig.type).replace(/_/g, " ") : "Taste Insight");
                const bodyText: string =
                  sig.text ||
                  "Consumer affinity overlap with confirmed boutique taste anchor.";

                return (
                  <div
                    key={idx}
                    className="rounded-xl border border-purple-100 bg-purple-50/50 p-3.5 text-xs space-y-1.5 flex flex-col justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-purple-950 capitalize truncate">
                          {title}
                        </span>
                        {sig.affinity_score !== undefined ? (
                          <span className="rounded bg-purple-200/70 px-2 py-0.5 text-[10px] font-bold text-purple-900 flex-shrink-0">
                            {Math.round(Number(sig.affinity_score) * 100)}% Affinity
                          </span>
                        ) : sig.source_ref ? (
                          <span className="font-mono text-[10px] text-purple-700 truncate">
                            {String(sig.source_ref)}
                          </span>
                        ) : null}
                      </div>
                      <p className="text-xs text-purple-900/90 leading-relaxed">
                        {bodyText}
                      </p>
                    </div>

                    {Array.isArray(sig.correlated_categories) &&
                      sig.correlated_categories.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1.5 border-t border-purple-200/40">
                          {sig.correlated_categories.map((cat, i) => (
                            <span
                              key={i}
                              className="rounded bg-white px-2 py-0.5 text-[10px] text-purple-800 border border-purple-200"
                            >
                              {String(cat)}
                            </span>
                          ))}
                        </div>
                      )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

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

      {/* Accessible Lead Rejection Confirmation Modal */}
      {showRejectModal && (
        <ConfirmationModal
          isOpen={showRejectModal}
          onClose={() => setShowRejectModal(false)}
          onConfirm={handleConfirmReject}
          title="Reject Stockist Lead"
          subtitle="Mark this lead as rejected."
          variant="danger"
          isLoading={isRejecting}
          confirmText="Reject Lead"
          cancelText="Keep Lead"
          icon={XCircle}
          description={
            <p>
              Are you sure you want to reject <strong className="text-ink font-semibold">&ldquo;{lead.name}&rdquo;</strong>? This will update its status to rejected.
            </p>
          }
        />
      )}
    </div>
  );
}

