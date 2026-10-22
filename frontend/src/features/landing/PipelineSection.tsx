import { Compass, Mail, Package, Users } from "lucide-react";

interface PipelinePhase {
  stageNumber: string;
  name: string;
  icon: typeof Package;
  kicker: string;
  headline: string;
  description: string;
  bulletPoints: string[];
  specimen: {
    title: string;
    badge: string;
    badgeStyle: string;
    details: { label: string; value: string }[];
    footerNote: string;
  };
}

const PHASES: readonly PipelinePhase[] = [
  {
    stageNumber: "Stage 1",
    name: "Product Passport",
    icon: Package,
    kicker: "Catalog craft specifications",
    headline: "Codify trade dimensions before approaching stockists",
    description:
      "Wholesale buyers need concrete production facts, not vague marketing blurbs. Product Passport organizes your studio's physical dimensions, materials, wholesale pricing, minimum order quantities (MOQ), and monthly studio capacity into a standardized specification.",
    bulletPoints: [
      "Wholesale pricing vs. Recommended Retail Price (RRP) margin modeling",
      "Exact physical dimensions, net weights, and packaged carton sizes",
      "Material provenance, firing temperatures, and artisan production lead times",
    ],
    specimen: {
      title: "Hand-thrown Stoneware Amphora",
      badge: "Catalog record",
      badgeStyle: "bg-surface-subtle text-ink border-border",
      details: [
        { label: "Material provenance", value: "Iron-rich stoneware clay & matte ash glaze" },
        { label: "Trade pricing", value: "$48 Wholesale · $120 RRP (2.5x Markup)" },
        { label: "Minimum order / lead", value: "6 units per order · 4 weeks production" },
        { label: "Aesthetic anchors", value: "Wabi-sabi, Japanese modern, tactile minimal" },
      ],
      footerNote: "Standardized wholesale passport ready for market matching.",
    },
  },
  {
    stageNumber: "Stage 2",
    name: "Market Discovery",
    icon: Compass,
    kicker: "Automated regional research",
    headline: "Target boutique stockists aligned with your cultural aesthetic",
    description:
      "Mass-market retailer scrapers flood your workspace with generic gift shops. Vitrine runs structured discovery scans focused on independent boutiques, gallery gift shops, and architectural design stores across design capitals like Tokyo, London, Paris, and Copenhagen.",
    bulletPoints: [
      "Regional discovery scans filtered by design aesthetic and maker category",
      "Extraction of verified physical retailer addresses and online storefronts",
      "Separation of cultural affinity hypotheses from verified store facts",
    ],
    specimen: {
      title: "Discovery Run: East Asia & Northern Europe",
      badge: "Verified run",
      badgeStyle: "bg-brass-light text-brass border-brass-border",
      details: [
        { label: "Target regions", value: "Tokyo (Daikanyama/Shibuya), London (Shoreditch), Copenhagen" },
        { label: "Store types", value: "Independent homeware boutiques, gallery stores, studio stockists" },
        { label: "Category fit", value: "Ceramics, tableware, slow living textiles" },
        { label: "Anchor keywords", value: "Wabi, handmade craft, studio ceramics, contemporary design" },
      ],
      footerNote: "Identifies authentic stockists whose retail curation reflects your studio caliber.",
    },
  },
  {
    stageNumber: "Stage 3",
    name: "Buyer Leads",
    icon: Users,
    kicker: "Evidence-backed fit scoring",
    headline: "Evaluate retail viability with complete data transparency",
    description:
      "Every prospective retailer is evaluated across category alignment, store activity, and retail price tiers. If an indicator lacks verifiable evidence, Vitrine explicitly displays 'Not enough evidence'—we never coerce unknown scores to zero or invent fictional numbers.",
    bulletPoints: [
      "Category alignment score derived strictly from actual carried lines",
      "Verified physical store presence and recent curation signals",
      "Clear distinction between verified facts and preliminary hypotheses",
    ],
    specimen: {
      title: "Momonoki Lifestyle & Home · Shibuya, Tokyo",
      badge: "Score: 91%",
      badgeStyle: "bg-emerald-50 text-emerald-800 border-emerald-200",
      details: [
        { label: "Store status", value: "Physical brick-and-mortar storefront verified (Shibuya-ku)" },
        { label: "Carried aesthetic", value: "Japanese modern ceramics, handcrafted linen, slow design" },
        { label: "Price tier match", value: "Retail range $45–$220 · Aligns with $48 wholesale / $120 RRP" },
        { label: "Evidence status", value: "Active curation verified via recent gallery exhibitions" },
      ],
      footerNote: "High cultural affinity backed by verifiable stockist evidence.",
    },
  },
  {
    stageNumber: "Stage 4",
    name: "Outreach Studio",
    icon: Mail,
    kicker: "Thoughtful wholesale inquiries",
    headline: "Draft bespoke pitches citing verified stockist facts",
    description:
      "Independent boutique buyers delete automated cold email blasts. Vitrine helps you compose concise, respectful wholesale inquiries citing real store details, carried brands, and aesthetic commonalities. Outreach is manual-review only: draft, edit, copy, and track.",
    bulletPoints: [
      "Synthesizes verified stockist details into tailored opening paragraphs",
      "Embeds precise Product Passport specifications (pricing, MOQ, lead times)",
      "Strict manual workflow: zero automated bot spam, full maker discretion",
    ],
    specimen: {
      title: "Wholesale Inquiry: Momonoki Tokyo",
      badge: "Draft prepared",
      badgeStyle: "bg-surface text-ink border-border",
      details: [
        { label: "Recipient context", value: "Addressed to Home & Gallery Buyer · Tokyo showroom" },
        { label: "Cited alignment", value: "References Momonoki's recent autumn handcrafted tableware showcase" },
        { label: "Trade attachments", value: "Includes Product Passport sheet for Table Amphora (MOQ: 6)" },
        { label: "Workflow policy", value: "Draft, edit, and copy to maker's email client. No automated sending." },
      ],
      footerNote: "Respectful, evidence-backed correspondence designed to open genuine relationships.",
    },
  },
];

export function PipelineSection() {
  return (
    <section
      id="how-it-works"
      aria-labelledby="pipeline-heading"
      className="scroll-mt-16 border-b border-border bg-canvas px-6 py-20 sm:px-8 sm:py-28 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header with Typographic Rhythm */}
        <div className="max-w-3xl">
          <span className="text-xs font-medium text-primary">
            The wholesale discovery pipeline
          </span>
          <h2
            id="pipeline-heading"
            className="mt-3 font-serif text-3xl sm:text-4xl lg:text-5xl font-normal tracking-tight text-ink"
          >
            Four Disciplined Steps from Studio to Stockist
          </h2>
          <p className="mt-4 text-base sm:text-lg leading-relaxed text-muted">
            A methodical system engineered to preserve craft margins, discover culturally aligned stockists, and eliminate speculative mass-emailing.
          </p>
        </div>

        {/* 4 Phases Arranged in Deliberate Editorial Composition */}
        <div className="mt-16 sm:mt-24 space-y-20 sm:space-y-28">
          {PHASES.map((phase, idx) => {
            const Icon = phase.icon;
            const isReversed = idx % 2 === 1;

            return (
              <div
                key={phase.stageNumber}
                className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-16 pt-12 border-t border-border-subtle first:pt-0 first:border-t-0"
              >
                {/* Content Column */}
                <div
                  className={`lg:col-span-6 ${
                    isReversed ? "lg:order-2" : "lg:order-1"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-semibold text-primary">
                      {phase.stageNumber}
                    </span>
                    <span className="h-px w-8 bg-border" aria-hidden="true" />
                    <span className="text-xs font-medium text-muted">
                      {phase.kicker}
                    </span>
                  </div>

                  <h3 className="mt-4 font-serif text-2xl sm:text-3xl font-normal tracking-tight text-ink">
                    {phase.headline}
                  </h3>

                  <p className="mt-4 text-sm sm:text-base leading-relaxed text-muted">
                    {phase.description}
                  </p>

                  <ul className="mt-6 space-y-2.5 text-xs sm:text-sm text-ink">
                    {phase.bulletPoints.map((point) => (
                      <li key={point} className="flex items-start gap-2.5">
                        <span className="mt-1.5 size-1.5 rounded-full bg-primary flex-shrink-0" />
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Specimen / Working Preview Column */}
                <div
                  className={`lg:col-span-6 ${
                    isReversed ? "lg:order-1" : "lg:order-2"
                  }`}
                >
                  <div data-ui className="rounded-xl border border-border bg-surface p-5 sm:p-6 shadow-card transition-shadow hover:shadow-elevated">
                    {/* Header */}
                    <div className="flex items-center justify-between pb-4 border-b border-border">
                      <div className="flex items-center gap-2.5">
                        <span className="grid size-8 place-items-center rounded-lg bg-surface-subtle text-ink border border-border-subtle">
                          <Icon size={16} />
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-ink leading-tight">
                            {phase.specimen.title}
                          </p>
                          <p className="text-[11px] text-muted">
                            Vitrine {phase.name} Interface
                          </p>
                        </div>
                      </div>
                      <span
                        className={`rounded-md border px-2.5 py-0.5 text-[11px] font-medium ${phase.specimen.badgeStyle}`}
                      >
                        {phase.specimen.badge}
                      </span>
                    </div>

                    {/* Specimen Details Grid */}
                    <div className="mt-4 divide-y divide-border-subtle text-xs">
                      {phase.specimen.details.map((detail) => (
                        <div key={detail.label} className="py-2.5 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1">
                          <span className="text-[11px] font-medium text-muted">
                            {detail.label}
                          </span>
                          <span className="text-ink font-normal text-[12px]">
                            {detail.value}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Footer Note */}
                    <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-[11px] text-muted">
                      <span>{phase.specimen.footerNote}</span>
                      <span className="text-[10px] text-subtle">Contract specification</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
