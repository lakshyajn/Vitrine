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
  statusText: string;
}

const PIPELINE_STEPS: readonly PipelineStep[] = [
  {
    title: "Product Passport",
    path: "/products",
    icon: Package,
    description: "Catalog craft materials, dimensions, wholesale pricing, MOQ, and monthly capacity.",
    statusText: "0 products cataloged",
  },
  {
    title: "Market Discovery",
    path: "/discovery",
    icon: Compass,
    description: "Run automated retailer scans across regions and evaluate cultural taste anchors.",
    statusText: "No runs initiated",
  },
  {
    title: "Buyer Leads",
    path: "/leads",
    icon: Users,
    description: "Screen vetted stockists with category, aesthetic, and store activity evidence.",
    statusText: "0 leads collected",
  },
  {
    title: "Outreach Studio",
    path: "/outreach",
    icon: Mail,
    description: "Draft personalized wholesale pitches citing verified facts with manual status tracking.",
    statusText: "0 drafts prepared",
  },
];

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  const isDashboard = title === "Dashboard";

  return (
    <div data-ui className="mx-auto max-w-6xl px-6 py-8 sm:px-10 sm:py-10">
      {/* Page Header */}
      <header className="pb-8 border-b border-border">
        <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
          {title}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted sm:text-base max-w-3xl">
          {description ||
            (isDashboard
              ? "Wholesale stockist discovery and evidence-backed outreach for independent craft makers."
              : `Manage your ${title.toLowerCase()} workflow within the Vitrine wholesale workspace.`)}
        </p>
      </header>

      {/* Dashboard View: 4-Stage Wholesale Pipeline Overview */}
      {isDashboard ? (
        <div className="mt-8 space-y-8">
          {/* Pipeline Grid */}
          <section aria-labelledby="pipeline-heading">
            <div className="flex items-center justify-between mb-4">
              <h2 id="pipeline-heading" className="font-display text-base font-semibold text-ink">
                Wholesale Discovery Pipeline
              </h2>
              <span className="text-xs font-medium text-subtle">
                4-Stage Workflow
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {PIPELINE_STEPS.map((step) => {
                const Icon = step.icon;
                return (
                  <Link
                    key={step.path}
                    to={step.path}
                    className="group relative flex flex-col justify-between rounded-xl border border-border bg-surface p-5 transition-colors duration-150 hover:border-accent hover:bg-surface-hover"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="grid size-9 place-items-center rounded-lg bg-accent-light text-accent">
                          <Icon size={18} strokeWidth={2} />
                        </span>
                        <span className="text-[11px] font-medium text-subtle">
                          {step.statusText}
                        </span>
                      </div>
                      <p className="mt-4 font-display text-sm font-semibold text-ink group-hover:text-accent transition-colors">
                        {step.title}
                      </p>
                      <p className="mt-1.5 text-xs leading-relaxed text-muted">
                        {step.description}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-xs font-medium text-accent">
                      <span>Open section</span>
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
            className="rounded-xl border border-border bg-surface p-6 sm:p-8"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 id="guide-heading" className="font-display text-base font-semibold text-ink">
                  Getting Started in Vitrine
                </h2>
                <p className="mt-1 text-sm text-muted max-w-2xl">
                  Wholesale discovery begins with your craft profile. Configure your first product in Product Passport to establish style keywords, materials, wholesale pricing, and target retailer types.
                </p>
              </div>
              <Link
                to="/products"
                className="pressable inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent whitespace-nowrap"
              >
                Go to Product Passport
              </Link>
            </div>
          </section>
        </div>
      ) : (
        /* Specific Feature Empty State */
        <div className="mt-8">
          <section
            aria-label={`${title} workspace status`}
            className="rounded-xl border border-border bg-surface p-8 sm:p-12 text-center"
          >
            <div className="mx-auto max-w-md">
              <p className="font-display text-base font-semibold text-ink">
                No active records
              </p>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                This workspace will populate as you catalog products, run stockist searches, and prepare outreach.
              </p>
              <div className="mt-6 flex items-center justify-center gap-3">
                <Link
                  to="/"
                  className="pressable inline-flex items-center justify-center rounded-lg border border-border bg-surface px-4 py-2 text-sm font-semibold text-ink hover:bg-canvas focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                >
                  Return to Dashboard
                </Link>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
