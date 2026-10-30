import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  Search,
  ExternalLink,
  Mail,
  Bookmark,
  XCircle,
  Users,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Filter,
  CheckCircle2,
  Copy,
  Check,
} from "lucide-react";
import {
  getLeads,
  updateLead,
  type Lead,
} from "@/api";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ConfirmationModal } from "@/components/shared/Modal";

export function LeadsListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL Query state
  const runId = searchParams.get("run_id") || undefined;
  const productId = searchParams.get("product_id") || undefined;
  const tierParam = searchParams.get("tier") || "all";
  const reviewStatusParam = searchParams.get("review_status") || "all";
  const qParam = searchParams.get("q") || "";
  const sortParam = searchParams.get("sort") || "score_desc";
  const pageParam = parseInt(searchParams.get("page") || "1", 10);

  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [copiedEmailId, setCopiedEmailId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter input states
  const [searchInput, setSearchInput] = useState(qParam);

  // Rejection confirmation modal state
  const [rejectTarget, setRejectTarget] = useState<Lead | null>(null);
  const [isRejecting, setIsRejecting] = useState(false);

  const fetchLeads = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getLeads({
        run_id: runId,
        product_id: productId,
        tier: tierParam !== "all" ? tierParam : undefined,
        review_status: reviewStatusParam !== "all" ? reviewStatusParam : undefined,
        q: qParam || undefined,
        sort: sortParam,
        page: pageParam,
        page_size: 10,
      });
      setLeads(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load buyer leads.");
    } finally {
      setIsLoading(false);
    }
  }, [runId, productId, tierParam, reviewStatusParam, qParam, sortParam, pageParam]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  const updateParam = (key: string, val: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (!val || val === "all") {
      next.delete(key);
    } else {
      next.set(key, val);
    }
    next.set("page", "1"); // reset to page 1 on filter change
    setSearchParams(next);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam("q", searchInput.trim() || null);
  };

  const handleQuickStatus = async (leadId: string, status: "saved" | "rejected" | "contacted" | "new") => {
    try {
      const updated = await updateLead(leadId, { review_status: status });
      setLeads((prev) => prev.map((l) => (l.id === leadId ? updated : l)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update lead status");
    }
  };

  const handleConfirmReject = async () => {
    if (!rejectTarget || isRejecting) return;
    setIsRejecting(true);
    try {
      await updateLead(rejectTarget.id, { review_status: "rejected" });
      // Remove from currently visible list
      setLeads((prev) => prev.filter((l) => l.id !== rejectTarget.id));
      setTotal((prev) => Math.max(0, prev - 1));

      // If this was the last item on a page past page 1, step back
      if (leads.length === 1 && pageParam > 1) {
        updateParam("page", String(pageParam - 1));
      }
      setRejectTarget(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reject lead. Please try again.");
    } finally {
      setIsRejecting(false);
    }
  };

  const handleCopyEmail = (leadId: string, email: string) => {
    navigator.clipboard.writeText(email);
    setCopiedEmailId(leadId);
    setTimeout(() => setCopiedEmailId(null), 2000);
  };

  const totalPages = Math.max(1, Math.ceil(total / 10));

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
              Buyer Leads
            </h1>
            <span className="rounded-full bg-surface-subtle px-2.5 py-0.5 text-xs font-semibold text-muted border border-border">
              {total} stockist lead{total !== 1 ? "s" : ""}
            </span>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Independent retail stockists discovered through grounded web evidence and multi-dimensional fit scoring.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-border bg-surface p-4 shadow-card">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          {/* Search Input */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search retailer name, location, or domain..."
              className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2 text-xs sm:text-sm text-ink placeholder:text-subtle focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            />
          </form>

          {/* Quick Selects */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Tier Select */}
            <select
              value={tierParam}
              onChange={(e) => updateParam("tier", e.target.value)}
              className="rounded-xl border border-border bg-canvas px-3 py-2 text-xs text-ink focus:border-primary focus:outline-none shadow-xs"
            >
              <option value="all">All Tiers</option>
              <option value="qualified">Qualified</option>
              <option value="needs_review">Needs Review</option>
              <option value="unqualified">Unqualified</option>
            </select>

            {/* Review Status Select */}
            <select
              value={reviewStatusParam}
              onChange={(e) => updateParam("review_status", e.target.value)}
              className="rounded-xl border border-border bg-canvas px-3 py-2 text-xs text-ink focus:border-primary focus:outline-none shadow-xs"
            >
              <option value="all">All Statuses</option>
              <option value="new">New</option>
              <option value="saved">Saved</option>
              <option value="contacted">Contacted</option>
              <option value="rejected">Rejected</option>
            </select>

            {/* Sort Select */}
            <select
              value={sortParam}
              onChange={(e) => updateParam("sort", e.target.value)}
              className="rounded-xl border border-border bg-canvas px-3 py-2 text-xs text-ink focus:border-primary focus:outline-none shadow-xs"
            >
              <option value="score_desc">Highest Priority Score</option>
              <option value="name">Retailer Name (A–Z)</option>
              <option value="newest">Most Recently Discovered</option>
            </select>
          </div>
        </div>

        {/* Quick Filter Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-border-subtle text-xs">
          <span className="text-muted font-medium mr-1 flex items-center gap-1">
            <Filter className="size-3" /> Filter:
          </span>
          {[
            { label: "All Leads", key: "review_status", val: "all" },
            { label: "Needs Outreach", key: "review_status", val: "new" },
            { label: "Contacted", key: "review_status", val: "contacted" },
            { label: "Saved", key: "review_status", val: "saved" },
            { label: "Qualified Only", key: "tier", val: "qualified" },
          ].map((chip) => {
            const isActive =
              chip.key === "review_status"
                ? (chip.val === "all" && reviewStatusParam === "all") || reviewStatusParam === chip.val
                : tierParam === chip.val;
            return (
              <button
                key={chip.label}
                type="button"
                onClick={() => {
                  if (chip.key === "review_status") {
                    updateParam("review_status", chip.val);
                  } else {
                    updateParam("tier", tierParam === chip.val ? "all" : chip.val);
                  }
                }}
                className={`rounded-full px-3 py-1 font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white shadow-xs"
                    : "bg-surface-subtle text-muted hover:bg-surface-subtle/80 hover:text-ink border border-border"
                }`}
              >
                {chip.label}
              </button>
            );
          })}
        </div>

        {/* Active run or product banner */}
        {(runId || productId) && (
          <div className="flex items-center justify-between pt-2 border-t border-border-subtle text-xs text-muted">
            <span>
              Filtered by: {runId ? "Selected Discovery Run" : "Selected Product"}
            </span>
            <button
              type="button"
              onClick={() => {
                const next = new URLSearchParams(searchParams);
                next.delete("run_id");
                next.delete("product_id");
                setSearchParams(next);
              }}
              className="font-semibold text-primary hover:underline self-start sm:self-auto"
            >
              Clear Filter
            </button>
          </div>
        )}
      </div>

      {/* Main Leads List */}
      {isLoading ? (
        <LoadingSkeleton variant="table" count={4} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchLeads} />
      ) : leads.length === 0 ? (
        <EmptyState
          title="No buyer leads match the selected criteria"
          description="Try broadening your tier or status filters, or initiate a new Market Discovery run."
          icon={Users}
          action={{
            label: "Reset All Filters",
            onClick: () => {
              setSearchParams(new URLSearchParams());
              setSearchInput("");
            },
            icon: Filter,
          }}
        />
      ) : (
        <div className="space-y-4">
          {leads.map((lead) => (
            <div
              key={lead.id}
              className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
            >
              {/* Left Info */}
              <div className="space-y-2 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${
                      lead.tier === "qualified"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        : lead.tier === "needs_review"
                        ? "bg-amber-100 text-amber-800 border border-amber-200"
                        : "bg-rose-100 text-rose-800 border border-rose-200"
                    }`}
                  >
                    {(lead.tier || "needs_review").replace("_", " ")}
                  </span>

                  <span className="rounded bg-surface-subtle px-2 py-0.5 text-[11px] font-semibold text-muted border border-border">
                    {lead.retailer_type}
                  </span>

                  <span
                    className={`rounded px-2 py-0.5 text-[11px] font-semibold uppercase ${
                      lead.review_status === "saved"
                        ? "bg-primary-light text-primary border border-primary-border"
                        : lead.review_status === "contacted"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : lead.review_status === "rejected"
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-surface-subtle text-muted border border-border"
                    }`}
                  >
                    {lead.review_status}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    to={`/app/leads/${lead.id}`}
                    className="font-display text-base sm:text-lg font-semibold text-ink hover:text-primary transition-colors truncate"
                  >
                    {lead.name}
                  </Link>

                  {/* Duplicate Marker */}
                  {lead.duplicate_of && (
                    <span
                      className="inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-900 border border-amber-300"
                      title="Secondary duplicate of existing lead"
                    >
                      <AlertTriangle className="size-3" /> Duplicate
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
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
                  <span>·</span>
                  <div className="inline-flex items-center gap-1 font-mono text-muted bg-surface-subtle px-2 py-0.5 rounded border border-border">
                    <Mail className="size-3 text-primary" />
                    <span>{lead.contact_email || `wholesale@${lead.canonical_domain}`}</span>
                    {lead.contact_email && (
                      <span className="rounded bg-emerald-100 px-1 py-0.2 text-[9px] font-sans font-semibold text-emerald-800 ml-0.5">
                        Tavily
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => handleCopyEmail(lead.id, lead.contact_email || `wholesale@${lead.canonical_domain}`)}
                      className="ml-1 text-primary hover:text-ink"
                      title="Copy contact email"
                    >
                      {copiedEmailId === lead.id ? (
                        <Check className="size-3 text-emerald-600" />
                      ) : (
                        <Copy className="size-3" />
                      )}
                    </button>
                  </div>
                </div>

                {lead.assessment?.summary && (
                  <p className="text-xs text-muted line-clamp-1 italic">
                    "{lead.assessment.summary}"
                  </p>
                )}
              </div>

              {/* Middle: Priority Score Bar */}
              <div className="w-full lg:w-48 flex-shrink-0">
                <ScoreBar
                  label="Priority Score"
                  score={lead.scores.overall}
                />
              </div>

              {/* Right: Actions */}
              <div className="flex flex-wrap items-center gap-2 pt-3 lg:pt-0 border-t lg:border-t-0 border-border">
                {/* Contacted status toggle */}
                {lead.review_status === "contacted" ? (
                  <button
                    type="button"
                    onClick={() => handleQuickStatus(lead.id, "new")}
                    className="inline-flex items-center gap-1 rounded-xl bg-emerald-50 border border-emerald-300 px-3 py-2 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition-colors shadow-xs"
                    title="Marked as Contacted. Click to reset."
                  >
                    <CheckCircle2 className="size-3.5 text-emerald-600" />
                    <span>Contacted ✓</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleQuickStatus(lead.id, "contacted")}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50/60 px-3 py-2 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition-colors shadow-xs"
                    title="Mark as Contacted"
                  >
                    <CheckCircle2 className="size-3.5 text-emerald-600" />
                    <span>Mark Contacted</span>
                  </button>
                )}

                {lead.review_status !== "saved" && (
                  <button
                    type="button"
                    onClick={() => handleQuickStatus(lead.id, "saved")}
                    className="rounded-xl border border-border bg-surface p-2 text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
                    title="Save Lead"
                  >
                    <Bookmark className="size-4" />
                  </button>
                )}

                {lead.review_status !== "rejected" && (
                  <button
                    type="button"
                    onClick={() => setRejectTarget(lead)}
                    className="rounded-xl border border-border bg-surface p-2 text-muted hover:bg-rose-50 hover:text-rose-600 transition-colors shadow-xs"
                    title="Reject Lead"
                  >
                    <XCircle className="size-4" />
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => navigate(`/app/outreach/${lead.id}`)}
                  data-btn-primary
                  className="inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
                >
                  <Mail className="size-3.5" />
                  <span>Outreach</span>
                </button>

                <Link
                  to={`/app/leads/${lead.id}`}
                  className="inline-flex items-center gap-1 rounded-xl border border-border bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors shadow-xs"
                >
                  <span>Evidence & Details</span>
                </Link>
              </div>
            </div>
          ))}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-border pt-4 text-xs text-muted">
              <span>
                Page {pageParam} of {totalPages} ({total} total leads)
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={pageParam <= 1}
                  onClick={() => updateParam("page", String(pageParam - 1))}
                  className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface px-3 py-1.5 font-semibold text-ink hover:bg-surface-subtle disabled:opacity-50 transition-colors shadow-xs"
                >
                  <ChevronLeft className="size-3.5" />
                  <span>Previous</span>
                </button>
                <button
                  type="button"
                  disabled={pageParam >= totalPages}
                  onClick={() => updateParam("page", String(pageParam + 1))}
                  className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface px-3 py-1.5 font-semibold text-ink hover:bg-surface-subtle disabled:opacity-50 transition-colors shadow-xs"
                >
                  <span>Next</span>
                  <ChevronRight className="size-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Accessible Lead Rejection Confirmation Modal */}
      {rejectTarget && (
        <ConfirmationModal
          isOpen={!!rejectTarget}
          onClose={() => setRejectTarget(null)}
          onConfirm={handleConfirmReject}
          title="Reject Stockist Lead"
          subtitle="Mark this lead as unsuitable for outreach."
          variant="danger"
          isLoading={isRejecting}
          confirmText="Reject Lead"
          cancelText="Keep Lead"
          icon={XCircle}
          description={
            <p>
              Are you sure you want to reject <strong className="text-ink font-semibold">&ldquo;{rejectTarget.name}&rdquo;</strong>? It will be removed from your active leads list. You can review rejected leads at any time by selecting the "Rejected" status filter.
            </p>
          }
        />
      )}
    </div>
  );
}
