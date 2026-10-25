import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
  AlertTriangle,
  ShieldCheck,
  Loader2,
} from "lucide-react";
import {
  getLead,
  getProduct,
  getLeadOutreachDrafts,
  getOutreachDraft,
  generateOutreachDraft,
  updateOutreachDraft,
  regenerateOutreachDraft,
  type Lead,
  type Product,
  type OutreachDraft,
  type OutreachDraftStatus,
} from "@/api";
import { DemoBadge } from "@/components/shared/DemoBadge";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

export function OutreachWorkspacePage() {
  const { leadId } = useParams<{ leadId: string }>();

  const [lead, setLead] = useState<Lead | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [draft, setDraft] = useState<OutreachDraft | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form Fields
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<OutreachDraftStatus>("draft");
  const [followupNotes, setFollowupNotes] = useState("");

  // Copy Feedback Toasts
  const [copiedType, setCopiedType] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchWorkspace = useCallback(async () => {
    if (!leadId) return;
    setIsLoading(true);
    setError(null);
    try {
      let resolvedLeadId = leadId;
      let initialDraft: OutreachDraft | null = null;

      if (leadId.startsWith("draft-")) {
        try {
          initialDraft = await getOutreachDraft(leadId);
          resolvedLeadId = initialDraft.lead_id;
        } catch {
          // Fall through to regular lead lookup
        }
      }

      const leadData = await getLead(resolvedLeadId);
      setLead(leadData);

      if (leadData.product_id) {
        getProduct(leadData.product_id)
          .then((p) => setProduct(p))
          .catch(() => null);
      }

      // If we already loaded the draft directly, use it
      if (initialDraft) {
        setDraft(initialDraft);
        setSubject(initialDraft.subject);
        setBody(initialDraft.body);
        setStatus(initialDraft.status);
        setFollowupNotes(initialDraft.followup_notes || "");
      } else {
        // Check existing drafts for this lead
        const drafts = await getLeadOutreachDrafts(resolvedLeadId);
        if (drafts.length > 0) {
          const active = drafts[0];
          setDraft(active);
          setSubject(active.subject);
          setBody(active.body);
          setStatus(active.status);
          setFollowupNotes(active.followup_notes || "");
        } else {
          // Automatically generate initial grounded draft
          const generated = await generateOutreachDraft(resolvedLeadId);
          setDraft(generated);
          setSubject(generated.subject);
          setBody(generated.body);
          setStatus(generated.status);
          setFollowupNotes(generated.followup_notes || "");
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load outreach workspace.");
    } finally {
      setIsLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    fetchWorkspace();
  }, [fetchWorkspace]);

  // Save changes
  const handleSave = async (newStatus?: OutreachDraftStatus) => {
    if (!draft) return;
    setIsSaving(true);
    try {
      const updated = await updateOutreachDraft(draft.id, {
        subject,
        body,
        status: newStatus || status,
        followup_notes: followupNotes.trim() || null,
      });
      setDraft(updated);
      if (newStatus) setStatus(newStatus);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save draft");
    } finally {
      setIsSaving(false);
    }
  };

  // Regenerate draft
  const handleRegenerate = async () => {
    if (!draft) return;
    if (!window.confirm("Regenerate draft? This will create a revised version grounded in the latest evidence.")) {
      return;
    }
    setIsRegenerating(true);
    try {
      const regenerated = await regenerateOutreachDraft(draft.id);
      setDraft(regenerated);
      setSubject(regenerated.subject);
      setBody(regenerated.body);
      setStatus(regenerated.status);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to regenerate draft");
    } finally {
      setIsRegenerating(false);
    }
  };

  // Copy helper
  const handleCopy = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 2500);
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <LoadingSkeleton variant="detail" />
      </div>
    );
  }

  if (error || !lead || !draft) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ErrorState
          message={error || "Outreach draft unavailable"}
          onRetry={fetchWorkspace}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <Link
            to="/app/outreach"
            className="flex size-9 items-center justify-center rounded-xl border border-border bg-surface text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
                Pitch Workbench: {lead.name}
              </h1>
              <span className="text-xs font-mono text-muted">v{draft.version}</span>
              {draft.is_demo && <DemoBadge />}
            </div>
            <p className="text-xs text-muted">
              Grounded wholesale correspondence for {product?.name || "Product Passport"}.
            </p>
          </div>
        </div>

        {/* Copy Complete Pitch CTA */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() =>
              handleCopy(
                `Subject: ${subject}\n\n${body}`,
                "all"
              )
            }
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
          >
            {copiedType === "all" ? (
              <>
                <Check className="size-4" />
                <span>Pitch Copied to Clipboard!</span>
              </>
            ) : (
              <>
                <Copy className="size-4" />
                <span>Copy Full Email Pitch</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Workbench Grid: Editor on Left, Facts & Verification on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Draft Editor */}
        <div className="lg:col-span-2 space-y-5">
          {/* Status Tracker & Versioning Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface p-4 shadow-card">
            <div className="flex items-center gap-2 text-xs">
              <span className="font-semibold text-ink">Workflow Status:</span>
              {(["draft", "ready", "contacted"] as const).map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => handleSave(st)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-semibold capitalize transition-colors ${
                    status === st
                      ? st === "contacted"
                        ? "bg-emerald-600 text-white shadow-xs"
                        : "bg-primary text-white shadow-xs"
                      : "bg-surface-subtle text-muted hover:text-ink"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={isRegenerating}
                onClick={handleRegenerate}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-2.5 py-1 text-xs font-semibold text-muted hover:text-ink hover:bg-surface-subtle transition-colors"
                title="Regenerate revised draft with AI"
              >
                <RefreshCw className={`size-3 ${isRegenerating ? "animate-spin" : ""}`} />
                <span>Regenerate (v{draft.version + 1})</span>
              </button>
            </div>
          </div>

          {/* Model Warnings Callout */}
          {draft.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 space-y-1.5 text-xs text-amber-900">
              <div className="flex items-center gap-1.5 font-semibold">
                <AlertTriangle className="size-4 text-amber-700" />
                <span>Model Fact-Check Alerts:</span>
              </div>
              <ul className="list-disc pl-5 space-y-0.5 text-[11px] text-amber-800">
                {draft.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Editor Form Card */}
          <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
            {/* Subject Line */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="outreach-subject" className="block text-xs font-semibold text-ink">Subject Line</label>
                <button
                  type="button"
                  onClick={() => handleCopy(subject, "subject")}
                  className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline"
                >
                  {copiedType === "subject" ? (
                    <span className="text-emerald-700 font-medium">✓ Copied</span>
                  ) : (
                    <>
                      <Copy className="size-3" />
                      <span>Copy Subject</span>
                    </>
                  )}
                </button>
              </div>
              <input
                id="outreach-subject"
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2.5 text-xs sm:text-sm font-medium text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            {/* Email Body */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="outreach-body" className="block text-xs font-semibold text-ink">Pitch Content</label>
                <button
                  type="button"
                  onClick={() => handleCopy(body, "body")}
                  className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline"
                >
                  {copiedType === "body" ? (
                    <span className="text-emerald-700 font-medium">✓ Copied</span>
                  ) : (
                    <>
                      <Copy className="size-3" />
                      <span>Copy Body</span>
                    </>
                  )}
                </button>
              </div>
              <textarea
                id="outreach-body"
                rows={12}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="w-full rounded-xl border border-border bg-canvas p-3.5 font-sans text-xs sm:text-sm leading-relaxed text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            {/* Followup Notes */}
            <div className="space-y-1.5 pt-2 border-t border-border">
              <label htmlFor="outreach-notes" className="block text-xs font-semibold text-ink">
                Follow-up Schedule & Private Outreach Notes
              </label>
              <input
                id="outreach-notes"
                type="text"
                value={followupNotes}
                onChange={(e) => setFollowupNotes(e.target.value)}
                placeholder="e.g. Swatch card dispatched via Royal Mail on Tuesday; follow up in 10 days"
                className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2 text-xs text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            {/* Save Button */}
            <div className="flex items-center justify-between pt-3 border-t border-border">
              {saveSuccess ? (
                <span className="text-xs font-semibold text-emerald-700 animate-fade-in">
                  ✓ Draft saved
                </span>
              ) : <span />}

              <button
                type="button"
                disabled={isSaving}
                onClick={() => handleSave()}
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors shadow-xs"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="size-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save Draft Edits</span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Grounding Inspector & Facts Used */}
        <div className="space-y-5">
          {/* Retailer Context Card */}
          <div className="rounded-2xl border border-border bg-surface p-5 shadow-card space-y-3">
            <h3 className="font-display text-sm font-semibold uppercase tracking-wider text-muted">
              Stockist Context
            </h3>
            <div>
              <Link
                to={`/app/leads/${lead.id}`}
                className="font-display text-base font-semibold text-ink hover:text-primary transition-colors truncate block"
              >
                {lead.name}
              </Link>
              <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                <a
                  href={lead.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-mono text-primary hover:underline"
                >
                  <span>{lead.canonical_domain}</span>
                  <ExternalLink className="size-3" />
                </a>
              </div>
            </div>

            <div className="text-xs text-muted space-y-1 pt-2 border-t border-border-subtle">
              <div>
                <span className="text-subtle font-medium">Location:</span>{" "}
                <span className="text-ink font-semibold">
                  {[lead.location?.city, lead.location?.country].filter(Boolean).join(", ") || "Unconfirmed"}
                </span>
              </div>
              <div>
                <span className="text-subtle font-medium">Priority Score:</span>{" "}
                <strong className="text-ink">
                  {lead.scores.overall !== null ? `${Math.round(lead.scores.overall)}%` : "Not enough evidence"}
                </strong>
              </div>
            </div>
          </div>

          {/* Facts Used Inspector */}
          <div className="rounded-2xl border border-border bg-surface p-5 shadow-card space-y-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-emerald-600" />
              <h3 className="font-display text-sm font-semibold uppercase tracking-wider text-muted">
                Facts Grounded in Pitch ({draft.facts_used.length})
              </h3>
            </div>
            <p className="text-[11px] text-muted">
              Each statement in this pitch was corroborated by real web evidence or Product Passport data.
            </p>

            <div className="space-y-2.5 pt-2">
              {draft.facts_used.map((fact, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-border-subtle bg-canvas p-3 text-xs space-y-1"
                >
                  <p className="text-xs text-ink font-medium">"{fact.text}"</p>
                  {fact.source_url ? (
                    <a
                      href={fact.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-mono text-[10px] text-primary hover:underline truncate max-w-full"
                    >
                      <span>{fact.source_url}</span>
                      <ExternalLink className="size-2.5 flex-shrink-0" />
                    </a>
                  ) : (
                    <span className="text-[10px] text-subtle font-mono">
                      Source: Product Passport Specifications
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Hard Rule Reminder Notice */}
          <div className="rounded-2xl border border-border bg-surface-subtle/50 p-4 text-xs text-muted space-y-1">
            <span className="font-semibold text-ink">Maker-Controlled Outreach:</span>
            <p className="text-[11px] leading-relaxed">
              Vitrine is an evidence and drafting workspace. We deliberately omit automated email sending so you maintain complete control over direct relationships with boutique buyers.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

