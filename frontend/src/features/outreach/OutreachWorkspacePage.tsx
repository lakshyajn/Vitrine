import { useState, useEffect, useCallback, useRef } from "react";
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
  Sparkles,
  WifiOff,
  CheckCircle,
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

  // Split loading state: lead loads in ~50ms, draft synthesis may take ~15s
  const [isLoadingLead, setIsLoadingLead] = useState(true);
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form Fields
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<OutreachDraftStatus>("draft");
  const [followupNotes, setFollowupNotes] = useState("");

  // Copy Feedback Toasts & Network Resilience
  const [copiedType, setCopiedType] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true
  );
  const [hasOfflineBackup, setHasOfflineBackup] = useState(false);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  // Refs for debouncing or auto-sync
  const activeLeadIdRef = useRef<string | null>(null);

  const getStorageKey = (id: string) => `vitrine_outreach_draft_${id}`;

  // Helper to persist edits into local storage for offline resilience
  const persistLocalEdits = useCallback(
    (newSub: string, newBody: string, newNotes: string, newStatus: OutreachDraftStatus) => {
      const targetId = activeLeadIdRef.current;
      if (!targetId) return;
      try {
        localStorage.setItem(
          getStorageKey(targetId),
          JSON.stringify({
            subject: newSub,
            body: newBody,
            followup_notes: newNotes,
            status: newStatus,
            updated_at: Date.now(),
          })
        );
        setHasOfflineBackup(true);
      } catch (e) {
        console.warn("Could not save offline backup to localStorage", e);
      }
    },
    []
  );

  const fetchWorkspace = useCallback(async () => {
    if (!leadId) return;
    setIsLoadingLead(true);
    setError(null);

    let resolvedLeadId = leadId;
    let initialDraft: OutreachDraft | null = null;

    try {
      if (leadId.startsWith("draft-")) {
        try {
          initialDraft = await getOutreachDraft(leadId);
          resolvedLeadId = initialDraft.lead_id;
        } catch {
          // Fall through to regular lead lookup
        }
      }

      activeLeadIdRef.current = resolvedLeadId;

      // 1. Immediately fetch Lead and Product (<100ms)
      const leadData = await getLead(resolvedLeadId);
      setLead(leadData);
      setIsLoadingLead(false);

      if (leadData.product_id) {
        getProduct(leadData.product_id)
          .then((p) => setProduct(p))
          .catch(() => null);
      }

      // Check if local backup exists
      let localBackup: {
        subject?: string;
        body?: string;
        followup_notes?: string;
        status?: OutreachDraftStatus;
        updated_at?: number;
      } | null = null;
      try {
        const raw = localStorage.getItem(getStorageKey(resolvedLeadId));
        if (raw) localBackup = JSON.parse(raw);
      } catch {
        // ignore
      }

      // 2. Load or generate draft
      if (initialDraft) {
        setDraft(initialDraft);
        const serverTime = new Date(initialDraft.updated_at).getTime();
        if (localBackup?.updated_at && localBackup.updated_at > serverTime) {
          setSubject(localBackup.subject ?? initialDraft.subject);
          setBody(localBackup.body ?? initialDraft.body);
          setStatus(localBackup.status ?? initialDraft.status);
          setFollowupNotes(localBackup.followup_notes ?? initialDraft.followup_notes ?? "");
          setHasOfflineBackup(true);
          setSyncNotice("Restored offline draft edits from local device.");
        } else {
          setSubject(initialDraft.subject);
          setBody(initialDraft.body);
          setStatus(initialDraft.status);
          setFollowupNotes(initialDraft.followup_notes || "");
        }
      } else {
        // Check existing drafts for this lead
        const drafts = await getLeadOutreachDrafts(resolvedLeadId);
        if (drafts.length > 0) {
          const active = drafts[0];
          setDraft(active);
          const serverTime = new Date(active.updated_at).getTime();
          if (localBackup?.updated_at && localBackup.updated_at > serverTime) {
            setSubject(localBackup.subject ?? active.subject);
            setBody(localBackup.body ?? active.body);
            setStatus(localBackup.status ?? active.status);
            setFollowupNotes(localBackup.followup_notes ?? active.followup_notes ?? "");
            setHasOfflineBackup(true);
            setSyncNotice("Restored offline draft edits from local device.");
          } else {
            setSubject(active.subject);
            setBody(active.body);
            setStatus(active.status);
            setFollowupNotes(active.followup_notes || "");
          }
        } else {
          // Trigger dynamic generation by Nemotron Ultra with spinner
          setIsGeneratingDraft(true);
          try {
            const generated = await generateOutreachDraft(resolvedLeadId);
            setDraft(generated);
            setSubject(generated.subject);
            setBody(generated.body);
            setStatus(generated.status);
            setFollowupNotes(generated.followup_notes || "");
          } finally {
            setIsGeneratingDraft(false);
          }
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load outreach workspace.");
      setIsLoadingLead(false);
      setIsGeneratingDraft(false);
    }
  }, [leadId]);

  useEffect(() => {
    fetchWorkspace();
  }, [fetchWorkspace]);

  // Online / Offline Detection and Auto-Sync
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (hasOfflineBackup && draft) {
        setSyncNotice("Back online. Syncing local draft edits to server...");
        handleSave();
      }
    };
    const handleOffline = () => {
      setIsOnline(false);
      setSyncNotice("Working offline: edits are safely saved to local storage.");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [hasOfflineBackup, draft, subject, body, followupNotes, status]);

  // Save changes
  const handleSave = async (newStatus?: OutreachDraftStatus) => {
    if (!draft) return;
    setIsSaving(true);
    const targetStatus = newStatus || status;

    // Save locally first
    persistLocalEdits(subject, body, followupNotes, targetStatus);

    // If offline, preserve locally and notify
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      if (newStatus) setStatus(newStatus);
      setIsSaving(false);
      setSaveSuccess(true);
      setSyncNotice("Saved offline: changes stored locally on device.");
      setTimeout(() => setSaveSuccess(false), 2500);
      return;
    }

    try {
      const updated = await updateOutreachDraft(draft.id, {
        subject,
        body,
        status: targetStatus,
        followup_notes: followupNotes.trim() || null,
      });
      setDraft(updated);
      if (newStatus) setStatus(newStatus);
      setSaveSuccess(true);
      setHasOfflineBackup(false);
      setSyncNotice(null);

      // Clean storage after successful sync
      if (activeLeadIdRef.current) {
        try {
          localStorage.removeItem(getStorageKey(activeLeadIdRef.current));
        } catch {
          // ignore
        }
      }

      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err: unknown) {
      console.warn("Server save failed, kept in local backup", err);
      setSyncNotice("Connection interrupted. Edits are preserved locally and will sync when reconnected.");
    } finally {
      setIsSaving(false);
    }
  };

  // Field change handlers with automatic local persistence
  const handleSubjectChange = (val: string) => {
    setSubject(val);
    persistLocalEdits(val, body, followupNotes, status);
  };

  const handleBodyChange = (val: string) => {
    setBody(val);
    persistLocalEdits(subject, val, followupNotes, status);
  };

  const handleNotesChange = (val: string) => {
    setFollowupNotes(val);
    persistLocalEdits(subject, body, val, status);
  };

  // Regenerate draft
  const handleRegenerate = async () => {
    if (!draft) return;
    if (
      !window.confirm(
        "Regenerate pitch draft? Nemotron-3-Ultra-550B will craft a fresh version grounded in the latest evidence."
      )
    ) {
      return;
    }
    setIsRegenerating(true);
    try {
      const regenerated = await regenerateOutreachDraft(draft.id);
      setDraft(regenerated);
      setSubject(regenerated.subject);
      setBody(regenerated.body);
      setStatus(regenerated.status);
      setHasOfflineBackup(false);
      if (activeLeadIdRef.current) {
        try {
          localStorage.removeItem(getStorageKey(activeLeadIdRef.current));
        } catch {
          // ignore
        }
      }
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

  if (isLoadingLead) {
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
          message={error || "Outreach workspace unavailable for this lead"}
          onRetry={fetchWorkspace}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Top Header with Selected Brand Name Immediately Visible */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <Link
            to="/app/outreach"
            className="flex size-9 items-center justify-center rounded-xl border border-border bg-surface text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
                Pitch Workbench: {lead.name}
              </h1>
              {draft ? (
                <span className="text-xs font-mono text-muted">v{draft.version}</span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-primary-light px-2.5 py-0.5 text-[10px] font-semibold text-primary border border-primary/20">
                  <Sparkles className="size-3" />
                  <span>Synthesizing Pitch</span>
                </span>
              )}
              {draft?.is_demo && <DemoBadge />}
            </div>
            <p className="mt-0.5 text-xs text-muted">
              Grounded wholesale correspondence for {product?.name || "Product Passport"}.
            </p>
          </div>
        </div>

        {/* Copy Complete Pitch CTA & Connectivity Status */}
        <div className="flex flex-wrap items-center gap-2.5">
          {!isOnline ? (
            <span className="inline-flex items-center gap-1 rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-900">
              <WifiOff className="size-3 text-amber-700" />
              <span>Offline Mode</span>
            </span>
          ) : hasOfflineBackup ? (
            <span className="inline-flex items-center gap-1 rounded-lg border border-primary/20 bg-primary-light px-2.5 py-1 text-xs font-medium text-primary">
              <CheckCircle className="size-3 text-primary" />
              <span>Local Edits Saved</span>
            </span>
          ) : null}

          <button
            type="button"
            disabled={!draft || isGeneratingDraft}
            onClick={() =>
              handleCopy(
                `Subject: ${subject}\n\n${body}`,
                "all"
              )
            }
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs disabled:opacity-50 transition-colors"
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

      {/* Sync/Offline Notification Banner */}
      {syncNotice && (
        <div className="rounded-xl border border-primary/20 bg-primary-light/60 px-4 py-2.5 text-xs text-primary flex items-center justify-between animate-fade-in">
          <span>{syncNotice}</span>
          {hasOfflineBackup && isOnline && draft && (
            <button
              type="button"
              onClick={() => handleSave()}
              className="font-semibold underline hover:text-ink transition-colors"
            >
              Sync Now
            </button>
          )}
        </div>
      )}

      {/* Main Workbench Grid: Editor on Left, Facts & Verification on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Draft Editor or Dynamic AI Generation State */}
        <div className="lg:col-span-2 space-y-5">
          {isGeneratingDraft || !draft ? (
            /* Dedicated Dynamic Generation Spinner for Nemotron Ultra */
            <div className="rounded-2xl border border-primary/20 bg-surface p-8 shadow-card text-center space-y-5 animate-fade-in">
              <div className="flex size-14 items-center justify-center rounded-2xl bg-primary-light text-primary mx-auto animate-pulse">
                <Sparkles className="size-7" />
              </div>
              <div className="space-y-1.5 max-w-md mx-auto">
                <h3 className="font-display text-lg font-semibold text-ink">
                  Composing Wholesale Pitch for {lead.name}
                </h3>
                <p className="text-xs text-muted leading-relaxed">
                  Nemotron-3-Ultra-550B is analyzing verified evidence from {lead.canonical_domain} and your Product Passport specifications to draft authentic, human B2B correspondence.
                </p>
              </div>

              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary-light/70 px-4 py-1.5 text-xs font-semibold text-primary">
                <Loader2 className="size-3.5 animate-spin" />
                <span>Synthesizing brand pitch (typically ~15s)...</span>
              </div>
            </div>
          ) : (
            <>
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
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-2.5 py-1 text-xs font-semibold text-muted hover:text-ink hover:bg-surface-subtle disabled:opacity-50 transition-colors"
                    title="Regenerate revised draft with AI"
                  >
                    <RefreshCw className={`size-3 ${isRegenerating ? "animate-spin" : ""}`} />
                    <span>Regenerate (v{draft.version + 1})</span>
                  </button>
                </div>
              </div>

              {/* Model Warnings Callout if uncorroborated claims */}
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
                    <label htmlFor="outreach-subject" className="block text-xs font-semibold text-ink">
                      Subject Line
                    </label>
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
                    onChange={(e) => handleSubjectChange(e.target.value)}
                    className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2.5 text-xs sm:text-sm font-medium text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                  />
                </div>

                {/* Email Body */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label htmlFor="outreach-body" className="block text-xs font-semibold text-ink">
                      Pitch Content
                    </label>
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
                    onChange={(e) => handleBodyChange(e.target.value)}
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
                    onChange={(e) => handleNotesChange(e.target.value)}
                    placeholder="e.g. Swatch card dispatched via Royal Mail on Tuesday; follow up in 10 days"
                    className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2 text-xs text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                  />
                </div>

                {/* Save Button */}
                <div className="flex items-center justify-between pt-3 border-t border-border">
                  {saveSuccess ? (
                    <span className="text-xs font-semibold text-emerald-700 animate-fade-in flex items-center gap-1">
                      <Check className="size-3.5" />
                      <span>{isOnline ? "Draft saved to server" : "Saved locally on device"}</span>
                    </span>
                  ) : hasOfflineBackup ? (
                    <span className="text-xs text-muted flex items-center gap-1">
                      <span className="size-1.5 rounded-full bg-amber-500" />
                      <span>Unsynced local edits</span>
                    </span>
                  ) : (
                    <span />
                  )}

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
            </>
          )}
        </div>

        {/* Right Column: Grounding Inspector & Brand Context (Visible Immediately) */}
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
                <span className="text-subtle font-medium">Format:</span>{" "}
                <span className="text-ink font-semibold">{lead.retailer_type}</span>
              </div>
              <div>
                <span className="text-subtle font-medium">Priority Score:</span>{" "}
                <strong className="text-ink">
                  {lead.scores.overall !== null ? `${Math.round(lead.scores.overall)}%` : "Not enough evidence"}
                </strong>
              </div>
            </div>
          </div>

          {/* Product Passport Summary */}
          {product && (
            <div className="rounded-2xl border border-border bg-surface p-5 shadow-card space-y-2">
              <h3 className="font-display text-sm font-semibold uppercase tracking-wider text-muted">
                Artisan Product
              </h3>
              <p className="font-display text-sm font-semibold text-ink truncate">
                {product.name}
              </p>
              <div className="text-xs text-muted space-y-1">
                <div>
                  <span className="text-subtle">Category:</span>{" "}
                  <span className="text-ink font-medium">{product.category}</span>
                </div>
                <div>
                  <span className="text-subtle">Wholesale MOQ:</span>{" "}
                  <span className="text-ink font-medium">{product.moq} sets</span>
                </div>
                {product.materials.length > 0 && (
                  <div>
                    <span className="text-subtle">Materials:</span>{" "}
                    <span className="text-ink font-medium">{product.materials.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Facts Used Inspector (if draft exists) */}
          {draft && draft.facts_used.length > 0 && (
            <div className="rounded-2xl border border-border bg-surface p-5 shadow-card space-y-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-emerald-600" />
                <h3 className="font-display text-sm font-semibold uppercase tracking-wider text-muted">
                  Corroborated Facts ({draft.facts_used.length})
                </h3>
              </div>
              <p className="text-[11px] text-muted">
                Statements substantiated by retailer web evidence or Product Passport data.
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
          )}

          {/* Maker-Controlled Outreach Notice */}
          <div className="rounded-2xl border border-border bg-surface-subtle/50 p-4 text-xs text-muted space-y-1">
            <span className="font-semibold text-ink">Maker-Controlled Direct Outreach:</span>
            <p className="text-[11px] leading-relaxed">
              Vitrine assists with evidence synthesis and high-touch B2B pitch drafting. All email dispatching is performed directly by you so your buyer relationships remain personal.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
