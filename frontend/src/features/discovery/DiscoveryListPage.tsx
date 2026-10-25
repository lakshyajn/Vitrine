import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Compass, Plus, ArrowRight, Clock, CheckCircle2, AlertTriangle, Loader2, RotateCcw } from "lucide-react";
import {
  getResearchRuns,
  getProducts,
  type ResearchRun,
  type Product,
} from "@/api";
import { NewRunModal } from "./NewRunModal";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { DemoBadge } from "@/components/shared/DemoBadge";

export function DiscoveryListPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const productFilterParam = searchParams.get("product_id");

  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isNewRunModalOpen, setIsNewRunModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [runsData, prodsData] = await Promise.all([
        getResearchRuns(productFilterParam || undefined),
        getProducts(),
      ]);
      setRuns(runsData);
      setProducts(prodsData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load discovery runs.");
    } finally {
      setIsLoading(false);
    }
  }, [productFilterParam]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getProductName = (prodId: string) => {
    const p = products.find((prod) => prod.id === prodId);
    return p ? p.name : "Product Catalog Item";
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "awaiting_review":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900 animate-pulse">
            <Clock className="size-3.5" />
            Action: Review Anchors
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary-light px-2.5 py-1 text-xs font-semibold text-primary">
            <Loader2 className="size-3.5 animate-spin" />
            Running Pipeline
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-900">
            <CheckCircle2 className="size-3.5" />
            Completed
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-300 bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-900">
            <AlertTriangle className="size-3.5" />
            Failed
          </span>
        );
      case "queued":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-subtle px-2.5 py-1 text-xs font-semibold text-muted">
            <Clock className="size-3.5" />
            Queued
          </span>
        );
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Market Discovery
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Evidence-backed research runs combining web extraction, taste anchors, and boutique retailer verification.
          </p>
        </div>
        <div>
          <button
            type="button"
            onClick={() => setIsNewRunModalOpen(true)}
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            <Plus className="size-4" />
            <span>New Discovery Run</span>
          </button>
        </div>
      </div>

      {/* Filter Callout if filtered by product */}
      {productFilterParam && (
        <div className="flex items-center justify-between rounded-xl border border-primary/20 bg-primary-light/40 px-4 py-2.5 text-xs">
          <span className="font-medium text-ink">
            Showing runs filtered for: <span className="font-semibold">{getProductName(productFilterParam)}</span>
          </span>
          <button
            type="button"
            onClick={() => navigate("/app/discovery")}
            className="text-xs font-semibold text-primary hover:underline"
          >
            View All Runs
          </button>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <LoadingSkeleton variant="table" count={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : runs.length === 0 ? (
        productFilterParam ? (
          <EmptyState
            title="No discovery runs found for this product"
            description="Clear the active product filter to view all discovery runs or initiate a new run for this product."
            icon={Compass}
            action={{
              label: "Clear Product Filter",
              onClick: () => navigate("/app/discovery"),
              icon: RotateCcw,
            }}
          />
        ) : (
          <EmptyState
            title="No discovery runs initiated yet"
            description="Launch your first research run to uncover qualified boutique stockists grounded in authentic web evidence."
            icon={Compass}
            action={{
              label: "Start First Run",
              onClick: () => setIsNewRunModalOpen(true),
              icon: Plus,
            }}
          />
        )
      ) : (
        <div className="space-y-4">
          {runs.map((run) => (
            <div
              key={run.id}
              className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
            >
              {/* Left Details */}
              <div className="space-y-2 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  {getStatusBadge(run.status)}
                  <span className="rounded bg-surface-subtle px-2 py-0.5 text-[11px] font-mono text-muted border border-border">
                    Stage: {run.stage.replace("_", " ")}
                  </span>
                  <DemoBadge />
                </div>

                <h3 className="font-display text-base font-semibold text-ink truncate">
                  {getProductName(run.product_id)}
                </h3>

                <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-muted">
                  <span>
                    Regions:{" "}
                    <strong className="text-ink">
                      {run.inputs.regions.join(", ") || "Global"}
                    </strong>
                  </span>
                  <span>·</span>
                  <span>
                    Started:{" "}
                    {run.started_at
                      ? new Date(run.started_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "Recently"}
                  </span>
                </div>

                {run.inputs.notes && (
                  <p className="text-xs text-muted italic line-clamp-1">
                    "{run.inputs.notes}"
                  </p>
                )}
              </div>

              {/* Right Action Buttons */}
              <div className="flex flex-wrap items-center gap-2.5 pt-2 lg:pt-0 border-t lg:border-t-0 border-border">
                {run.status === "awaiting_review" ? (
                  <Link
                    to={`/app/discovery/${run.id}`}
                    data-btn-primary
                    className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
                  >
                    <span>Review Anchors</span>
                    <ArrowRight className="size-3.5" />
                  </Link>
                ) : (
                  <Link
                    to={`/app/discovery/${run.id}`}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface-subtle px-3.5 py-2 text-xs font-semibold text-ink hover:bg-surface transition-colors shadow-xs"
                  >
                    <span>View Workbench</span>
                    <ArrowRight className="size-3.5" />
                  </Link>
                )}

                {run.status === "completed" && (
                  <Link
                    to={`/app/leads?run_id=${run.id}`}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-primary/20 bg-primary-light px-3.5 py-2 text-xs font-semibold text-primary hover:bg-primary-light/80 transition-colors"
                  >
                    <span>View Discovered Leads</span>
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Run Modal */}
      <NewRunModal
        isOpen={isNewRunModalOpen}
        onClose={() => setIsNewRunModalOpen(false)}
        products={products}
        initialProductId={productFilterParam || undefined}
        onRunCreated={(runId) => navigate(`/app/discovery/${runId}`)}
      />
    </div>
  );
}

