import { ArrowRight, Compass, Mail, Package, Users } from "lucide-react";
import { Link } from "react-router-dom";

interface PlaceholderPageProps {
  title: string;
  description?: string;
}

interface PipelineStep {
  title: string;
  path: string;
  icon: typeof Package;
  description: string;
  actionLabel: string;
  statusText: string;
}

const PIPELINE_STEPS: readonly PipelineStep[] = [
  {
    title: "Product Passport",
    path: "/app/products",
    icon: Package,
    description:
      "Catalog garment specs, fabric GSM, wholesale vs. retail pricing, size curves (XS–XL), and studio lead times.",
    actionLabel: "Configure passport",
    statusText: "0 styles cataloged",
  },
  {
    title: "Market Discovery",
    path: "/app/discovery",
    icon: Compass,
    description:
      "Scan independent boutiques across global fashion hubs (Paris, Tokyo, London, Copenhagen) with aesthetic anchors.",
    actionLabel: "Start research run",
    statusText: "No runs initiated",
  },
  {
    title: "Buyer Leads",
    path: "/app/leads",
    icon: Users,
    description:
      "Screen vetted boutique stockists with verified storefront presence, carried designer lines, and explicit evidence.",
    actionLabel: "View boutique matches",
    statusText: "0 leads collected",
  },
  {
    title: "Outreach Studio",
    path: "/app/outreach",
    icon: Mail,
    description:
      "Draft personalized wholesale letters citing verified boutique details with manual review and status tracking.",
    actionLabel: "Open studio drafts",
    statusText: "0 drafts prepared",
  },
];

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  const isDashboard = title === "Dashboard";

  return (
    <div data-ui className="mx-auto max-w-6xl px-6 py-8 sm:px-10 sm:py-10 animate-page-enter">
      {/* Page Header */}
      <header className="pb-8 border-b border-border">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
          <div>
            <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-ink">
              {title}
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted sm:text-base max-w-3xl">
              {description ||
                (isDashboard
                  ? "An evidence-led wholesale discovery workspace for independent fashion designers and apparel studios."
                  : `Manage your ${title.toLowerCase()} workflow within the Vitrine wholesale workspace.`)}
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 self-start rounded-md border border-border bg-surface px-2.5 py-1 text-xs font-medium text-muted shadow-xs">
            <span className="size-2 rounded-full bg-emerald-600" />
            Studio Workspace Active
          </span>
        </div>
      </header>

      {/* Dashboard View: 4-Stage Wholesale Pipeline Overview */}
      {isDashboard ? (
        <div className="mt-8 space-y-8">
          {/* Pipeline Grid */}
          <section aria-labelledby="pipeline-heading">
            <div className="flex items-center justify-between mb-4">
              <h2 id="pipeline-heading" className="text-xs font-medium text-muted">
                Wholesale Discovery Pipeline · 4 Stages
              </h2>
              <span className="text-xs text-subtle font-mono">
                Evidence Contract v0.2
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {PIPELINE_STEPS.map((step) => {
                const Icon = step.icon;
                return (
                  <Link
                    key={step.path}
                    to={step.path}
                    className="group relative flex flex-col justify-between rounded-xl border border-border bg-surface p-5 shadow-xs transition-[border-color,box-shadow] duration-150 hover:border-primary/40 hover:shadow-card"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="grid size-9 place-items-center rounded-lg bg-surface-subtle text-primary border border-border-subtle group-hover:border-primary/30 transition-colors">
                          <Icon size={18} strokeWidth={2} />
                        </span>
                        <span className="text-[11px] text-muted font-mono">
                          {step.statusText}
                        </span>
                      </div>
                      <p className="mt-4 font-display text-lg font-bold text-ink group-hover:text-primary transition-colors">
                        {step.title}
                      </p>
                      <p className="mt-1.5 text-xs leading-relaxed text-muted">
                        {step.description}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-xs font-semibold text-primary">
                      <span>{step.actionLabel}</span>
                      <ArrowRight size={14} className="transition-transform group-hover:translate-x-0.5" />
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>

          {/* Getting Started Guide */}
          <section
            aria-labelledby="guide-heading"
            className="rounded-xl border border-border bg-surface p-6 sm:p-8 shadow-xs"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
              <div className="max-w-2xl">
                <span className="text-xs font-semibold text-accent">
                  Recommended First Step
                </span>
                <h2 id="guide-heading" className="mt-1 font-display text-xl sm:text-2xl font-bold text-ink">
                  Configure Your First Collection Line-Sheet
                </h2>
                <p className="mt-2 text-sm text-muted leading-relaxed">
                  Wholesale discovery begins with your collection&apos;s trade specifications. Catalog your garment measurements, fabric composition, size curves, wholesale pricing, and MOQ to enable boutique discovery matching.
                </p>
              </div>
              <Link
                to="/app/products"
                data-btn-primary
                style={{ backgroundColor: "#4A154B", color: "#FFFFFF" }}
                className="btn-primary pressable inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary whitespace-nowrap"
              >
                <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                  Go to Product Passport
                </span>
                <ArrowRight size={15} style={{ color: "#FFFFFF" }} className="text-white" />
              </Link>
            </div>
          </section>
        </div>
      ) : (
        /* Specific Feature Honest Empty State */
        <div className="mt-8">
          <section
            aria-label={`${title} workspace status`}
            className="rounded-xl border border-border bg-surface p-8 sm:p-12 text-center shadow-xs"
          >
            <div className="mx-auto max-w-md">
              <span className="inline-flex size-10 items-center justify-center rounded-full bg-surface-subtle text-primary border border-border-subtle">
                <Package size={20} />
              </span>
              <h2 className="mt-4 font-display text-xl font-bold text-ink">
                No active records
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                No {title.toLowerCase()} records found. This workbench will populate as you configure your collection styles, initiate regional boutique scans, and prepare outreach letters.
              </p>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                <Link
                  to="/app"
                  className="pressable inline-flex items-center justify-center rounded-lg border border-border bg-surface px-4 py-2 text-sm font-semibold text-ink shadow-xs hover:bg-surface-subtle focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                >
                  Return to Dashboard
                </Link>
                {title !== "Product Passport" && (
                  <Link
                    to="/app/products"
                    data-btn-primary
                    style={{ backgroundColor: "#4A154B", color: "#FFFFFF" }}
                    className="btn-primary pressable inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                  >
                    <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                      Open Product Passport
                    </span>
                  </Link>
                )}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
