import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Edit3, ArrowRight } from "lucide-react";
import {
  getOutreachDrafts,
  getLeads,
  getProducts,
  type OutreachDraft,
  type Lead,
  type Product,
} from "@/api";
import { DemoBadge } from "@/components/shared/DemoBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

export function OutreachListPage() {
  const navigate = useNavigate();
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [draftsData, leadsData, prodsData] = await Promise.all([
        getOutreachDrafts({ status: statusFilter !== "all" ? statusFilter : undefined }),
        getLeads({ page_size: 100 }),
        getProducts(),
      ]);
      // Deduplicate by lead_id to show strictly the latest draft per buyer lead
      const latestDraftsByLead = new Map<string, OutreachDraft>();
      for (const d of draftsData) {
        const existing = latestDraftsByLead.get(d.lead_id);
        if (
          !existing ||
          d.version > existing.version ||
          new Date(d.updated_at).getTime() > new Date(existing.updated_at).getTime()
        ) {
          latestDraftsByLead.set(d.lead_id, d);
        }
      }
      setDrafts(Array.from(latestDraftsByLead.values()));
      setLeads(leadsData.items);
      setProducts(prodsData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load outreach drafts.");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getLeadName = (leadId: string) => {
    const l = leads.find((lead) => lead.id === leadId);
    return l ? l.name : "Retail Stockist";
  };

  const getProductName = (prodId: string) => {
    const p = products.find((prod) => prod.id === prodId);
    return p ? p.name : "Catalog Item";
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Outreach Studio
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Craft, review, and organize evidence-grounded wholesale pitches. Vitrine provides draft creation, fact-checking, and status tracking (no automated mail sending).
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 rounded-xl border border-border bg-surface p-1 text-xs">
          {(["all", "draft", "ready", "contacted"] as const).map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`rounded-lg px-3 py-1.5 font-semibold capitalize transition-colors ${
                statusFilter === st
                  ? "bg-primary text-white shadow-xs"
                  : "text-muted hover:text-ink hover:bg-surface-subtle"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Drafts List */}
      {isLoading ? (
        <LoadingSkeleton variant="table" count={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : drafts.length === 0 ? (
        <EmptyState
          title="No outreach drafts available"
          description="Discover qualified buyer leads and open them in Outreach Studio to compose grounded pitches."
          icon={Mail}
          action={{
            label: "Explore Buyer Leads",
            onClick: () => navigate("/app/leads"),
            icon: Mail,
          }}
        />
      ) : (
        <div className="space-y-4">
          {drafts.map((draft) => (
            <div
              key={draft.id}
              className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
            >
              <div className="space-y-2 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${
                      draft.status === "contacted"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                        : draft.status === "ready"
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : "bg-surface-subtle text-muted border border-border"
                    }`}
                  >
                    {draft.status}
                  </span>

                  <span className="text-xs font-mono text-muted">v{draft.version}</span>
                  {draft.is_demo && <DemoBadge />}
                </div>

                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3">
                  <h3 className="font-display text-base font-semibold text-ink">
                    {getLeadName(draft.lead_id)}
                  </h3>
                  <span className="text-xs text-muted truncate">
                    Subject: <em>"{draft.subject}"</em>
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
                  <span>
                    Product: <strong className="text-ink">{getProductName(draft.product_id)}</strong>
                  </span>
                  <span>·</span>
                  <span>
                    Facts cited: <strong>{draft.facts_used.length}</strong>
                  </span>
                  {draft.warnings.length > 0 && (
                    <>
                      <span>·</span>
                      <span className="text-amber-700 font-medium">
                        {draft.warnings.length} warning(s)
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <div className="flex items-center gap-2 pt-2 lg:pt-0 border-t lg:border-t-0 border-border">
                <Link
                  to={`/app/outreach/${draft.lead_id}`}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface-subtle px-3.5 py-2 text-xs font-semibold text-ink hover:bg-surface transition-colors shadow-xs"
                >
                  <Edit3 className="size-3.5" />
                  <span>Open Pitch Workbench</span>
                  <ArrowRight className="size-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

