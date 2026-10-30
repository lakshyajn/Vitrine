import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Check,
  X,
  Plus,
  RefreshCw,
  Users,
  Compass,
  Sparkles,
  Loader2,
  RotateCcw,
} from "lucide-react";
import {
  getResearchRun,
  rerunResearchRun,
  getAnchors,
  createAnchor,
  updateAnchor,
  confirmAnchors,
  getHypotheses,
  getProduct,
  type ResearchRun,
  type TasteAnchor,
  type MarketHypothesis,
  type Product,
} from "@/api";
import { StatusStepper } from "@/components/shared/StatusStepper";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();

  const [run, setRun] = useState<ResearchRun | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [anchors, setAnchors] = useState<TasteAnchor[]>([]);
  const [hypotheses, setHypotheses] = useState<MarketHypothesis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Custom Anchor addition state
  const [newAnchorLabel, setNewAnchorLabel] = useState("");
  const [newAnchorRationale, setNewAnchorRationale] = useState("");
  const [isAddingAnchor, setIsAddingAnchor] = useState(false);
  const [isConfirmingAnchors, setIsConfirmingAnchors] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);

  // Accessible undo recovery for anchor actions
  const [lastAction, setLastAction] = useState<{
    anchorId: string;
    prevStatus: TasteAnchor["status"];
    label: string;
    newStatus: TasteAnchor["status"];
  } | null>(null);

  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchRunDetails = useCallback(async (isPolling = false) => {
    if (!runId) return;
    if (!isPolling) setIsLoading(true);
    setError(null);
    try {
      const runData = await getResearchRun(runId);
      setRun(runData);

      // Load associated product
      if (runData.product_id) {
        getProduct(runData.product_id)
          .then((p) => setProduct(p))
          .catch(() => null);
      }

      // Load anchors and hypotheses in parallel
      const [anchorsData, hypothesesData] = await Promise.all([
        getAnchors(runId),
        getHypotheses(runId),
      ]);
      setAnchors(anchorsData);
      setHypotheses(hypothesesData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load research run.");
    } finally {
      if (!isPolling) setIsLoading(false);
    }
  }, [runId]);

  // Initial load
  useEffect(() => {
    fetchRunDetails();
  }, [fetchRunDetails]);

  // Polling logic: Poll every 2.5s ONLY while queued or running
  useEffect(() => {
    if (run && (run.status === "queued" || run.status === "running")) {
      pollingTimerRef.current = setTimeout(() => {
        fetchRunDetails(true);
      }, 2500);
    }
    return () => {
      if (pollingTimerRef.current) clearTimeout(pollingTimerRef.current);
    };
  }, [run, fetchRunDetails]);

  // Anchor Status Update with reversible tracking
  const handleAnchorStatus = async (
    anchorId: string,
    status: "confirmed" | "rejected" | "proposed"
  ) => {
    const existing = anchors.find((a) => a.id === anchorId);
    if (!existing) return;
    const prevStatus = existing.status;
    try {
      const updated = await updateAnchor(anchorId, { status });
      setAnchors((prev) => prev.map((a) => (a.id === anchorId ? updated : a)));
      if (status !== "proposed") {
        setLastAction({
          anchorId,
          prevStatus,
          label: existing.label,
          newStatus: status,
        });
      } else {
        setLastAction(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update anchor");
    }
  };

  const handleUndoLastAction = async () => {
    if (!lastAction) return;
    try {
      const updated = await updateAnchor(lastAction.anchorId, {
        status: lastAction.prevStatus,
      });
      setAnchors((prev) =>
        prev.map((a) => (a.id === lastAction.anchorId ? updated : a))
      );
      setLastAction(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to undo anchor action");
    }
  };

  // Add Custom Anchor
  const handleAddCustomAnchor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!runId || !newAnchorLabel.trim()) return;
    setIsAddingAnchor(true);
    try {
      const created = await createAnchor(runId, {
        label: newAnchorLabel.trim(),
        entity_type: "brand",
        rationale: newAnchorRationale.trim() || undefined,
      });
      setAnchors((prev) => [...prev, created]);
      setNewAnchorLabel("");
      setNewAnchorRationale("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add custom anchor");
    } finally {
      setIsAddingAnchor(false);
    }
  };

  // Confirm Anchors & Resume Pipeline
  const handleConfirmAndResume = async () => {
    if (!runId) return;
    setIsConfirmingAnchors(true);
    try {
      await confirmAnchors(runId, { proceed_without_anchors: false });
      await fetchRunDetails();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to confirm anchors");
    } finally {
      setIsConfirmingAnchors(false);
    }
  };

  // Rerun Trigger
  const handleRerun = async () => {
    if (!runId) return;
    setIsRerunning(true);
    try {
      await rerunResearchRun(runId);
      await fetchRunDetails();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to rerun discovery");
    } finally {
      setIsRerunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <LoadingSkeleton variant="detail" />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ErrorState
          message={error || "Research run not found"}
          onRetry={() => fetchRunDetails()}
        />
      </div>
    );
  }

  const confirmedAnchorsCount = anchors.filter((a) => a.status === "confirmed").length;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <Link
            to="/app/discovery"
            className="flex size-9 items-center justify-center rounded-xl border border-border bg-surface text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
              Discovery Run Workbench
            </h1>
            <p className="text-xs text-muted">
              Grounded research for:{" "}
              <strong className="text-ink">{product?.name || "Product Passport"}</strong>
            </p>
          </div>
        </div>

        {/* Header Action: View Leads if completed or rerun */}
        <div className="flex items-center gap-2">
          {run.status === "completed" && (
            <Link
              to={`/app/leads?run_id=${run.id}`}
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
            >
              <Users className="size-4" />
              <span>Review Discovered Leads</span>
            </Link>
          )}

          {run.status === "failed" && (
            <button
              type="button"
              disabled={isRerunning}
              onClick={handleRerun}
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
            >
              <RefreshCw className={`size-3.5 ${isRerunning ? "animate-spin" : ""}`} />
              <span>Rerun Pipeline</span>
            </button>
          )}
        </div>
      </div>

      {/* Stepper Status Card */}
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
        <StatusStepper status={run.status} stage={run.stage} />
      </div>

      {/* Run Inputs & Context Card */}
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wider text-muted">
          Research Inputs & Target Parameters
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-subtle font-medium">Target Regions:</span>
            <p className="mt-0.5 font-semibold text-ink">
              {run.inputs?.regions?.join(", ") || "Global"}
            </p>
          </div>
          <div>
            <span className="text-subtle font-medium">Retailer Formats:</span>
            <p className="mt-0.5 font-semibold text-ink">
              {run.inputs?.retailer_types?.join(", ") || "All Independent Boutiques"}
            </p>
          </div>
          <div>
            <span className="text-subtle font-medium">Execution Status:</span>
            <p className="mt-0.5 font-semibold text-ink capitalize">
              {(run.status || "queued").replace("_", " ")} ({(run.stage || "queued").replace("_", " ")})
            </p>
          </div>
        </div>

        {run.inputs?.notes && (
          <div className="mt-2 rounded-xl border border-border-subtle bg-surface-subtle/40 p-3 text-xs text-muted italic">
            "{run.inputs.notes}"
          </div>
        )}
      </div>

      {/* Anchor Review Panel (Crucial Milestone for awaiting_review) */}
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-display text-base font-semibold text-ink">
                Taste Anchors & Aesthetic Grounding
              </h2>
              {run.status === "awaiting_review" && (
                <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900 border border-amber-300">
                  Seller Action Required
                </span>
              )}
            </div>
            <p className="mt-0.5 text-xs text-muted">
              Brand and boutique taste anchors inform discovery search queries and shopper affinity matching.
            </p>
          </div>

          {/* Confirm & Resume action button (available in review or to expand leads on completed run) */}
          {(run.status === "awaiting_review" || run.status === "completed") && (
            <button
              type="button"
              disabled={isConfirmingAnchors || confirmedAnchorsCount === 0}
              onClick={handleConfirmAndResume}
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs disabled:opacity-50 transition-colors"
            >
              {isConfirmingAnchors ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  <span>{run.status === "completed" ? "Searching More Leads..." : "Resuming Pipeline..."}</span>
                </>
              ) : (
                <>
                  <Check className="size-3.5" />
                  <span>
                    {run.status === "completed"
                      ? `Confirm (${confirmedAnchorsCount}) & Discover More Leads`
                      : `Confirm (${confirmedAnchorsCount}) & Resume Discovery`}
                  </span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Completed Run Expansion Guidance */}
        {run.status === "completed" && (
          <div className="rounded-xl border border-primary/20 bg-primary-light/40 p-3.5 text-xs text-ink flex items-start gap-2.5 animate-fade-in">
            <Sparkles className="size-4 text-primary flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-ink">Want to discover more buyer leads from this run?</p>
              <p className="text-muted mt-0.5 leading-relaxed">
                You can confirm additional taste anchors below or add your own custom brand references, then click <strong>"Confirm & Discover More Leads"</strong>. Vitrine will search for complementary retailers and add them to your discovered leads without losing existing results.
              </p>
            </div>
          </div>
        )}

        {/* Accessible Undo Notification */}
        {lastAction && (
          <div className="flex items-center justify-between rounded-xl border border-primary/20 bg-primary-light/60 px-4 py-2.5 text-xs text-primary animate-fade-in">
            <span>
              Anchor <strong>{lastAction.label}</strong> updated to{" "}
              <strong className="capitalize">{lastAction.newStatus}</strong>.
            </span>
            <button
              type="button"
              onClick={handleUndoLastAction}
              className="inline-flex items-center gap-1 font-semibold underline hover:text-ink transition-colors"
            >
              <RotateCcw className="size-3" />
              <span>Undo Action</span>
            </button>
          </div>
        )}

        {/* Anchors List */}
        <div className="space-y-3">
          {anchors.map((anchor) => (
            <div
              key={anchor.id}
              className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border p-4 transition-colors ${
                anchor.status === "confirmed"
                  ? "border-emerald-200 bg-emerald-50/40"
                  : anchor.status === "rejected"
                  ? "border-rose-200 bg-rose-50/40 opacity-70"
                  : "border-border bg-surface"
              }`}
            >
              <div className="space-y-1 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-display text-sm font-semibold text-ink">
                    {anchor.label}
                  </span>
                  <span className="rounded bg-surface-subtle px-2 py-0.5 text-[10px] font-semibold uppercase text-muted border border-border">
                    {(anchor.source || "proposed").replace("_", " ")}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase ${
                      anchor.status === "confirmed"
                        ? "bg-emerald-100 text-emerald-800"
                        : anchor.status === "rejected"
                        ? "bg-rose-100 text-rose-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {anchor.status}
                  </span>
                </div>
                {anchor.rationale && (
                  <p className="text-xs text-muted leading-relaxed">
                    {anchor.rationale}
                  </p>
                )}
              </div>

              {/* Status Toggle Actions */}
              <div className="flex items-center gap-1.5 flex-shrink-0">
                {anchor.status !== "confirmed" && (
                  <button
                    type="button"
                    onClick={() => handleAnchorStatus(anchor.id, "confirmed")}
                    className="inline-flex items-center gap-1 rounded-lg border border-emerald-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-50 transition-colors shadow-xs"
                    title="Confirm this anchor"
                  >
                    <Check className="size-3" />
                    <span>Confirm</span>
                  </button>
                )}
                {anchor.status !== "rejected" && (
                  <button
                    type="button"
                    onClick={() => handleAnchorStatus(anchor.id, "rejected")}
                    className="inline-flex items-center gap-1 rounded-lg border border-rose-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-rose-800 hover:bg-rose-50 transition-colors shadow-xs"
                    title="Reject this anchor"
                  >
                    <X className="size-3" />
                    <span>Reject</span>
                  </button>
                )}
                {anchor.status !== "proposed" && (
                  <button
                    type="button"
                    onClick={() => handleAnchorStatus(anchor.id, "proposed")}
                    className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs font-semibold text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
                    title="Reset to proposed state"
                  >
                    <RotateCcw className="size-3" />
                    <span>Reset</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Add User-Defined Custom Anchor Form */}
        <form onSubmit={handleAddCustomAnchor} className="rounded-xl border border-dashed border-border bg-surface-subtle/30 p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-ink">
            <Plus className="size-3.5 text-primary" />
            <span>Add Custom Brand Taste Reference</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input
              type="text"
              required
              value={newAnchorLabel}
              onChange={(e) => setNewAnchorLabel(e.target.value)}
              placeholder="Brand or Boutique Name (e.g. Margaret Howell)"
              className="rounded-lg border border-border bg-surface px-3 py-1.5 text-xs text-ink focus:border-primary focus:outline-none"
            />
            <input
              type="text"
              value={newAnchorRationale}
              onChange={(e) => setNewAnchorRationale(e.target.value)}
              placeholder="Why this aligns with your product"
              className="sm:col-span-2 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs text-ink focus:border-primary focus:outline-none"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isAddingAnchor || !newAnchorLabel.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-ink hover:bg-surface-subtle disabled:opacity-50 transition-colors shadow-xs"
            >
              <Plus className="size-3" />
              <span>{isAddingAnchor ? "Adding..." : "Add Reference Anchor"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Market Hypotheses Card */}
      {hypotheses.length > 0 && (
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <h2 className="font-display text-base font-semibold text-ink">
              Synthesized Market Hypotheses & Cultural Signals
            </h2>
          </div>

          <div className="space-y-4">
            {hypotheses.map((hyp) => (
              <div key={hyp.id} className="rounded-xl border border-border bg-canvas p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-display text-sm font-semibold text-ink">
                    {hyp.title}
                  </h3>
                  <span className="rounded bg-surface-subtle px-2 py-0.5 text-[10px] font-mono text-muted border border-border">
                    {hyp.region_hint || "Regional Vector"}
                  </span>
                </div>
                {hyp.rationale && (
                  <p className="text-xs text-muted leading-relaxed">
                    {hyp.rationale}
                  </p>
                )}

                {/* Signals list */}
                {hyp.signals.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-border">
                    <span className="text-[11px] font-semibold text-ink uppercase tracking-wider">
                      Grounding Signals:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {hyp.signals.map((sig, i) => (
                        <div key={i} className="rounded-lg border border-border bg-surface p-2.5 text-xs space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-muted">
                            <span className="font-semibold uppercase">{(sig.source || sig.type || "signal").replace("_", " ")}</span>
                          </div>
                          <p className="text-xs text-ink">{sig.text}</p>
                          {sig.source_ref && (
                            <span className="block font-mono text-[10px] text-primary truncate">
                              Ref: {sig.source_ref}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completion Banner */}
      {run.status === "completed" && (
        <div className="rounded-2xl border border-emerald-300 bg-emerald-50/70 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="font-display text-base font-semibold text-emerald-950">
              Discovery Run Completed
            </h3>
            <p className="text-xs text-emerald-800">
              Web evidence extraction, official domain verification, and dimensional fit scoring have concluded.
            </p>
          </div>
          <Link
            to={`/app/leads?run_id=${run.id}`}
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-semibold text-white shadow-xs transition-colors whitespace-nowrap"
          >
            <Compass className="size-4" />
            <span>View Discovered Buyer Leads</span>
          </Link>
        </div>
      )}
    </div>
  );
}

