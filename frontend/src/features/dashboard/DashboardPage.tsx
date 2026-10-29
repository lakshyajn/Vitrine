import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Package,
  Compass,
  Users,
  Mail,
  ArrowRight,
  Plus,
  Clock,
  Sparkles,
  CheckCircle,
  X,
} from "lucide-react";
import {
  ApiError,
  getProducts,
  getResearchRuns,
  getLeads,
  getOutreachDrafts,
  type Product,
  type ResearchRun,
  type Lead,
  type OutreachDraft,
} from "@/api";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ErrorState } from "@/components/shared/ErrorState";

export function DashboardPage() {
  const navigate = useNavigate();

  const [products, setProducts] = useState<Product[]>([]);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [prodsData, runsData, leadsData, draftsData] =
        await Promise.all([
          getProducts(),
          getResearchRuns(),
          getLeads({ page_size: 10 }),
          getOutreachDrafts(),
        ]);
      setProducts(prodsData);
      setRuns(runsData);
      setLeads(leadsData.items);
      setDrafts(draftsData);
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        return;
      }
      setError(
        err instanceof Error ? err.message : "Failed to load dashboard metrics."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <LoadingSkeleton variant="detail" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <ErrorState message={error} onRetry={fetchDashboardData} />
      </div>
    );
  }

  const qualifiedLeadsCount = leads.filter((l) => l.tier === "qualified").length;
  const pendingReviewRuns = runs.filter((r) => r.status === "awaiting_review");

  // Accurate outreach pitch count (unique leads with prepared drafts, avoiding revision double-counting)
  const uniquePitchesCount = new Set(drafts.map((d) => d.lead_id)).size;

  const formatRunStatus = (status: string) => {
    switch (status) {
      case "completed":
        return "Completed";
      case "awaiting_review":
        return "Review Anchors";
      case "running":
        return "Running";
      case "failed":
        return "Failed";
      case "queued":
      default:
        return "Queued";
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8 animate-fade-in">
      {/* Toast Notification Banner */}
      {notification && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 animate-fade-in shadow-xs"
        >
          <div className="flex items-center gap-2">
            <CheckCircle className="size-4 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{notification}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="rounded p-1 text-emerald-600 hover:text-emerald-900 transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="size-3.5" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Workspace Overview
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Your products, discovered stockists, and outreach activity at a glance.
          </p>
        </div>

        {/* Quick Launch Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Link
            to="/app/products/new"
            className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface px-3.5 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors shadow-xs"
          >
            <Plus className="size-3.5" />
            <span>Add Product</span>
          </Link>
          <button
            type="button"
            onClick={() => navigate("/app/discovery")}
            data-btn-primary
            className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
          >
            <Compass className="size-3.5" />
            <span>Market Discovery</span>
          </button>
        </div>
      </div>

      {/* Empty State Banner: Prompt when no products exist */}
      {products.length === 0 && (
        <div className="rounded-2xl border border-primary/20 bg-primary-light/40 p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xs animate-fade-in">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
              <Sparkles className="size-4" />
              <span>Get Started with Vitrine</span>
            </div>
            <h2 className="font-display text-lg sm:text-xl font-bold text-ink">
              Your maker workspace has no products yet
            </h2>
            <p className="text-xs text-muted leading-relaxed">
              Create your first artisan Product Passport to begin discovering suitable boutique stockists and managing buyer leads.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/app/products/new"
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-colors"
            >
              <Plus className="size-4" />
              <span>Add First Product</span>
            </Link>
          </div>
        </div>
      )}

      {/* Action Callout if Anchor Review is pending */}
      {pendingReviewRuns.length > 0 && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50/80 p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <Clock className="size-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-display text-sm font-semibold text-amber-950">
                Action Required: Taste Anchor Review
              </h3>
              <p className="mt-0.5 text-xs text-amber-800">
                {pendingReviewRuns.length} research run{pendingReviewRuns.length !== 1 ? "s are" : " is"} awaiting your review of proposed brand anchors before completing retailer discovery.
              </p>
            </div>
          </div>
          <Link
            to={`/app/discovery/${pendingReviewRuns[0].id}`}
            data-btn-primary
            className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs whitespace-nowrap"
          >
            <span>Review Proposed Anchors</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
      )}

      {/* Data-Derived Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Products */}
        <Link
          to="/app/products"
          className="group rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
        >
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Product Catalog</span>
            <Package className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {products.length}
            </span>
            <span className="text-xs text-muted">passports</span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            Materials &amp; wholesale parameters
          </p>
        </Link>

        {/* Metric 2: Research Runs */}
        <Link
          to="/app/discovery"
          className="group rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
        >
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Discovery Runs</span>
            <Compass className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {runs.length}
            </span>
            <span className="text-xs text-muted">executed</span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            Target regions &amp; boutique matching
          </p>
        </Link>

        {/* Metric 3: Buyer Leads */}
        <Link
          to="/app/leads"
          className="group rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
        >
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Discovered Leads</span>
            <Users className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {leads.length}
            </span>
            <span className="text-xs text-emerald-700 font-medium">
              ({qualifiedLeadsCount} qualified)
            </span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            Verified stockist domains
          </p>
        </Link>

        {/* Metric 4: Outreach Drafts */}
        <Link
          to="/app/outreach"
          className="group rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
        >
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Outreach Pitches</span>
            <Mail className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {uniquePitchesCount}
            </span>
            <span className="text-xs text-muted">prepared</span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            Personalized wholesale pitches
          </p>
        </Link>
      </div>

      {/* Dual Section: Recent Qualified Leads & Active Discovery Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Buyer Leads */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-base font-semibold text-ink">
                Priority Boutique Leads
              </h2>
              <p className="text-xs text-muted">Highest alignment across category and aesthetics</p>
            </div>
            <Link
              to="/app/leads"
              className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
            >
              <span>View all ({leads.length})</span>
              <ArrowRight className="size-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {leads.length === 0 ? (
              <div className="rounded-xl border border-border bg-surface p-6 text-center text-xs text-muted">
                No stockist leads yet. Start a discovery run to populate candidates.
              </div>
            ) : (
              leads.slice(0, 3).map((lead) => (
                <div
                  key={lead.id}
                  className="flex items-center justify-between gap-4 rounded-xl border border-border bg-surface p-4 shadow-card hover:border-border-strong transition-all"
                >
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/app/leads/${lead.id}`}
                        className="font-display text-sm font-semibold text-ink hover:text-primary transition-colors truncate"
                      >
                        {lead.name}
                      </Link>
                      <span className="rounded bg-surface-subtle px-1.5 py-0.5 text-[10px] font-mono text-muted border border-border">
                        {lead.retailer_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted">
                      {lead.location && (
                        <span>{[lead.location.city, lead.location.country].filter(Boolean).join(", ")}</span>
                      )}
                    </div>
                  </div>

                  <div className="w-32 flex-shrink-0">
                    <ScoreBar label="" score={lead.scores.overall} />
                  </div>

                  <Link
                    to={`/app/outreach/${lead.id}`}
                    className="rounded-lg p-2 text-muted hover:bg-surface-subtle hover:text-primary transition-colors"
                    title="Compose outreach pitch"
                  >
                    <Mail className="size-4" />
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Discovery Runs */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-base font-semibold text-ink">
                Recent Market Discovery Runs
              </h2>
              <p className="text-xs text-muted">Status and progress across targeted regions</p>
            </div>
            <Link
              to="/app/discovery"
              className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
            >
              <span>All runs ({runs.length})</span>
              <ArrowRight className="size-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {runs.length === 0 ? (
              <div className="rounded-xl border border-border bg-surface p-6 text-center text-xs text-muted">
                No discovery runs yet. Initiate a run to research potential stockists.
              </div>
            ) : (
              runs.slice(0, 3).map((run) => {
                const runProduct = products.find((p) => p.id === run.product_id);
                const runDate = run.started_at
                  ? new Date(run.started_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                    })
                  : null;

                return (
                  <div
                    key={run.id}
                    className="flex items-center justify-between gap-4 rounded-xl border border-border bg-surface p-4 shadow-card hover:border-border-strong transition-all"
                  >
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-display text-sm font-semibold text-ink truncate">
                          {runProduct?.name || "Discovery Run"}
                        </span>
                        {runDate && (
                          <span className="text-[11px] text-muted">({runDate})</span>
                        )}
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase ${
                            run.status === "completed"
                              ? "bg-emerald-100 text-emerald-800"
                              : run.status === "awaiting_review"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-surface-subtle text-muted"
                          }`}
                        >
                          {formatRunStatus(run.status || "queued")}
                        </span>
                      </div>
                      <p className="text-xs text-muted truncate">
                        Regions: {run.inputs?.regions?.join(", ") || "Global"}
                      </p>
                    </div>

                    <Link
                      to={`/app/discovery/${run.id}`}
                      className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors shadow-xs"
                    >
                      <span>Workbench</span>
                      <ArrowRight className="size-3" />
                    </Link>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
