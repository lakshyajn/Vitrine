import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  Globe,
  Store,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  LayoutDashboard,
} from "lucide-react";
import {
  getLeads,
  getOutreachDrafts,
  getProducts,
  getResearchRuns,
  type Lead,
  type OutreachDraft,
  type Product,
  type ResearchRun,
} from "@/api";
import { DemoBadge } from "@/components/shared/DemoBadge";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ErrorState } from "@/components/shared/ErrorState";
import { AgStudioInsights } from "./AgStudioInsights";

export function InsightsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"studio" | "breakdown">("studio");

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [leadsData, draftsData, productsData, runsData] = await Promise.all([
          getLeads({ page_size: 100 }),
          getOutreachDrafts(),
          getProducts().catch(() => []),
          getResearchRuns().catch(() => []),
        ]);
        setLeads(leadsData.items);
        setDrafts(draftsData);
        setProducts(productsData);
        setRuns(runsData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load insights data.");
      } finally {
        setIsLoading(false);
      }
    };
    load();
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
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  // Analytics Computations
  const totalLeads = leads.length;
  const qualifiedCount = leads.filter((l) => l.tier === "qualified").length;
  const needsReviewCount = leads.filter((l) => l.tier === "needs_review").length;
  const unqualifiedCount = leads.filter((l) => l.tier === "unqualified").length;

  const qualifiedRatio = totalLeads > 0 ? Math.round((qualifiedCount / totalLeads) * 100) : 0;

  // Geographic Distribution
  const countryCounts: Record<string, number> = {};
  leads.forEach((l) => {
    const c = l.location?.country || "International";
    countryCounts[c] = (countryCounts[c] || 0) + 1;
  });

  // Retailer Format Breakdown
  const formatCounts: Record<string, number> = {};
  leads.forEach((l) => {
    const fmt = l.retailer_type || "Independent Boutique";
    formatCounts[fmt] = (formatCounts[fmt] || 0) + 1;
  });

  // Average Priority Score across non-null leads
  const scoredLeads = leads.filter((l) => l.scores.overall !== null);
  const avgScore =
    scoredLeads.length > 0
      ? Math.round(
          scoredLeads.reduce((acc, curr) => acc + (curr.scores.overall || 0), 0) /
            scoredLeads.length
        )
      : null;

  const territoryList = Object.keys(countryCounts);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
              AG Studio Insights
            </h1>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200">
              <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
              AG Studio Active
            </span>
            <DemoBadge />
          </div>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Embedded analytics powered by AG Studio v3.0, cross-filtering data engine, and the official Agent Framework.
          </p>
        </div>

        {/* Tab Switching */}
        <div className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-subtle p-1 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab("studio")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === "studio"
                ? "bg-surface text-ink shadow-xs"
                : "text-muted hover:text-ink"
            }`}
          >
            <Sparkles className="size-3.5 text-primary" />
            <span>Interactive Studio</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("breakdown")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === "breakdown"
                ? "bg-surface text-ink shadow-xs"
                : "text-muted hover:text-ink"
            }`}
          >
            <LayoutDashboard className="size-3.5 text-muted" />
            <span>Pipeline Breakdown</span>
          </button>
        </div>
      </div>

      {/* Top Stat Cards — High-Level Telemetry */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat 1: Lead Qualification Yield */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Qualification Yield</span>
            <ShieldCheck className="size-4 text-emerald-600" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {qualifiedRatio}%
            </span>
            <span className="text-xs text-muted">of candidates</span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            {qualifiedCount} of {totalLeads} retailers passed evidence verification
          </p>
        </div>

        {/* Stat 2: Average Priority Fit */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Priority Fit</span>
            <TrendingUp className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {avgScore !== null ? `${avgScore}%` : "Not enough evidence"}
            </span>
            <span className="text-xs text-muted">{avgScore !== null ? "composite score" : "pending"}</span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            {scoredLeads.length} of {totalLeads} scored across category and aesthetic alignment
          </p>
        </div>

        {/* Stat 3: Target Regions */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Geographic Footprint</span>
            <Globe className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {territoryList.length}
            </span>
            <span className="text-xs text-muted">territories</span>
          </div>
          <p className="mt-1 text-[11px] text-muted truncate">
            {territoryList.join(", ") || "International"}
          </p>
        </div>

        {/* Stat 4: Outreach Conversion */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Pitches Formulated</span>
            <Store className="size-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-ink">
              {drafts.length}
            </span>
            <span className="text-xs text-muted">drafts</span>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            {drafts.filter((d) => d.status === "contacted").length} marked contacted
          </p>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === "studio" ? (
        <AgStudioInsights
          leads={leads}
          drafts={drafts}
          products={products}
          runs={runs}
        />
      ) : (
        <div className="space-y-8 animate-fade-in">
          {/* Analytics Breakdown Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Geographic Distribution */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-display text-base font-semibold text-ink">
                    Boutique Geography by Territory
                  </h2>
                  <p className="text-xs text-muted">Discovered retail stockists across mapped markets</p>
                </div>
                <Globe className="size-4 text-muted" />
              </div>

              <div className="space-y-3 pt-2">
                {Object.entries(countryCounts).map(([country, count]) => {
                  const pct = totalLeads > 0 ? Math.round((count / totalLeads) * 100) : 0;
                  return (
                    <div key={country} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-ink">{country}</span>
                        <span className="text-muted">{count} stockists ({pct}%)</span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-border-subtle">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Retailer Channel Formats */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-display text-base font-semibold text-ink">
                    Retailer Channel Formats
                  </h2>
                  <p className="text-xs text-muted">Distribution of retail formats in catalog</p>
                </div>
                <Store className="size-4 text-muted" />
              </div>

              <div className="space-y-3 pt-2">
                {Object.entries(formatCounts).map(([format, count]) => {
                  const pct = totalLeads > 0 ? Math.round((count / totalLeads) * 100) : 0;
                  return (
                    <div key={format} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-ink">{format}</span>
                        <span className="text-muted">{count} retailers ({pct}%)</span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-border-subtle">
                        <div
                          className="h-full bg-emerald-600 rounded-full transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Discovery Pipeline Yield Table */}
          <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-display text-base font-semibold text-ink">
                  Discovery Candidate Pipeline Tiers
                </h2>
                <p className="text-xs text-muted">
                  Quality triage: candidates with complete domain evidence vs items requiring seller review
                </p>
              </div>
              <Link
                to="/app/leads"
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
              >
                <span>Explore Buyer Leads</span>
                <ArrowRight className="size-3" />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              {/* Qualified Tier */}
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase text-emerald-900">Qualified</span>
                  <span className="font-display text-2xl font-bold text-emerald-950">{qualifiedCount}</span>
                </div>
                <p className="text-[11px] text-emerald-800 leading-relaxed">
                  Verified official boutique domains with retail activity evidence and price compatibility.
                </p>
              </div>

              {/* Needs Review Tier */}
              <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase text-amber-900">Needs Review</span>
                  <span className="font-display text-2xl font-bold text-amber-950">{needsReviewCount}</span>
                </div>
                <p className="text-[11px] text-amber-800 leading-relaxed">
                  Partial evidence or adjacent aesthetic requiring maker discernment before wholesale outreach.
                </p>
              </div>

              {/* Unqualified Tier */}
              <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase text-rose-900">Unqualified</span>
                  <span className="font-display text-2xl font-bold text-rose-950">{unqualifiedCount}</span>
                </div>
                <p className="text-[11px] text-rose-800 leading-relaxed">
                  Unverified domains, missing retail activity, or commercial mismatch.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
