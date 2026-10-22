import { Compass, Mail, Package, Users } from "lucide-react";

interface WorkflowStep {
  stageNumber: string;
  name: string;
  icon: typeof Package;
  kicker: string;
  headline: string;
  problem: string;
  solution: string;
  bulletPoints: string[];
  specimen: {
    title: string;
    badge: string;
    badgeStyle: string;
    details: { label: string; value: string }[];
    footerNote: string;
  };
}

const WORKFLOW_STEPS: readonly WorkflowStep[] = [
  {
    stageNumber: "Stage 01",
    name: "Product Passport",
    icon: Package,
    kicker: "Catalog Garment Specs & Wholesale Pricing",
    headline: "Codify collection line-sheets before approaching stockists",
    problem:
      "Boutique buyers immediately discard collection lookbooks that lack clear wholesale wholesale margins, fabric compositions, size scales, and production lead times.",
    solution:
      "Product Passport translates your apparel designs into a standardized wholesale trade sheet. Codify garment dimensions, fabric GSM, size curves (XS–XL), unit wholesale vs. RRP margins, minimum order quantities (MOQ), and studio seasonal cut capacity.",
    bulletPoints: [
      "Standardized wholesale margin modeling: Wholesale vs. RRP (2.5× to 2.8×)",
      "Fabric provenance: 340gsm European flax linen, horn button trims, French seams",
      "Production lead times, size curves, and minimum run quantities per style/colorway",
    ],
    specimen: {
      title: "Double-Breasted Linen Blazer · Look 04",
      badge: "Line-Sheet Specification",
      badgeStyle: "bg-surface-subtle text-ink border-border",
      details: [
        { label: "Fabric & Construction", value: "340gsm Belgian linen, unlined, French seams" },
        { label: "Trade Pricing", value: "$145 Wholesale · $360 RRP (2.48× markup)" },
        { label: "Size Curve & MOQ", value: "12 units minimum · Size breakdown: 2-XS, 4-S, 4-M, 2-L" },
        { label: "Production Cycle", value: "6 weeks cut-and-sew · Atelier Lisbon/London" },
      ],
      footerNote: "Standardized apparel passport ready for automated boutique matching.",
    },
  },
  {
    stageNumber: "Stage 02",
    name: "Market Discovery",
    icon: Compass,
    kicker: "Automated Regional Boutique Research",
    headline: "Target independent boutiques aligned with your collection aesthetic",
    problem:
      "Mass retail scrapers flood your database with generic tourist souvenir shops and fast-fashion stores that will never carry independent designer labels.",
    solution:
      "Vitrine runs focused discovery runs across global fashion capitals (Tokyo, Paris, London, Copenhagen, New York), identifying independent multi-brand boutiques, designer concept stores, and curated fashion spaces whose existing curation matches your silhouette, price tier, and ethos.",
    bulletPoints: [
      "Targeted boutique discovery across global design districts (Le Marais, Daikanyama, Shoreditch)",
      "Discovery filtered by aesthetic keywords: relaxed tailoring, Japanese minimal, quiet luxury",
      "Strict separation of cultural aesthetic affinity from verified store operations",
    ],
    specimen: {
      title: "Discovery Run: Paris (Le Marais) & Tokyo (Daikanyama)",
      badge: "Discovery Scan Active",
      badgeStyle: "bg-primary-light text-primary border-primary-border",
      details: [
        { label: "Target Boutique Hubs", value: "Rue de Turenne (Paris 3e), Daikanyama T-Site (Tokyo)" },
        { label: "Retail Category Fit", value: "Independent designer womenswear, relaxed tailoring, slow fashion" },
        { label: "Price Tier Match", value: "Retail range $250–$900 · Compatible with $360 blazer RRP" },
        { label: "Aesthetic Anchors", value: "Architectural silhouettes, raw linen, muted earth palettes" },
      ],
      footerNote: "Discovers independent stockists whose floor curation matches your label caliber.",
    },
  },
  {
    stageNumber: "Stage 03",
    name: "Buyer Leads",
    icon: Users,
    kicker: "Evidence-Backed Fit Evaluation",
    headline: "Evaluate boutique retail viability with complete data transparency",
    problem:
      "Other B2B tools hallucinate 99% match scores without proof, leading makers to waste weeks pitching stores that don't buy external brands or have closed physical doors.",
    solution:
      "Every prospective boutique is evaluated across physical presence, price alignment, and carried designer lines. If a key fact is missing online, Vitrine truthfully displays 'Not enough evidence'—we never coerce unknown scores to zero or invent fictional facts.",
    bulletPoints: [
      "Verified physical brick-and-mortar storefront address and active retail hours",
      "Carried designer lines verified: e.g. Studio Nicholson, Casey Casey, Margaret Howell",
      "Explicit audit trail distinguishing verified facts from subjective aesthetic hypotheses",
    ],
    specimen: {
      title: "Boutique L'Ombre · Rue Charlot, Paris 3e",
      badge: "Evaluation Score: 92%",
      badgeStyle: "bg-emerald-50 text-emerald-800 border-emerald-200",
      details: [
        { label: "Physical Store Status", value: "Street-level boutique verified (Paris 3e · Active retail hours)" },
        { label: "Curated Designer Lines", value: "Carries European artisanal linen, raw silks, slow tailoring" },
        { label: "Retail Price Tier Match", value: "Blazer tier $320–$650 · Fits maker $145 wholesale / $360 RRP" },
        { label: "Wholesale Intake Status", value: "Not enough evidence (unconfirmed online intake window)" },
      ],
      footerNote: "High aesthetic fit with verified physical presence and honest intake disclosure.",
    },
  },
  {
    stageNumber: "Stage 04",
    name: "Outreach Studio",
    icon: Mail,
    kicker: "Personalized Wholesale Correspondence",
    headline: "Draft bespoke wholesale inquiries citing verified boutique curation",
    problem:
      "Independent boutique buyers delete automated mass email blasts instantly. They recognize generic AI mailers and consider them disrespectful to their curation.",
    solution:
      "Vitrine prepares tailored, highly specific wholesale inquiries citing the boutique's actual carried designers and current season window curation. Outreach is manual-review only: draft, edit, copy to your own email client, and track status manually. Zero automated bot sending.",
    bulletPoints: [
      "Customized opening citing the boutique's specific curation and aesthetic alignment",
      "Includes structured Product Passport line-sheet specs (wholesale pricing, MOQ, lead time)",
      "Strict maker control: review, copy, and send via your own studio email with zero bot spam",
    ],
    specimen: {
      title: "Wholesale Inquiry: Boutique L'Ombre Paris",
      badge: "Draft Ready for Review",
      badgeStyle: "bg-surface text-ink border-border",
      details: [
        { label: "Recipient & Store", value: "Head Buyer · Boutique L'Ombre showroom, Paris 3e" },
        { label: "Cited Collection Fit", value: "References L'Ombre's current curation of undyed European flax tailoring" },
        { label: "Line-Sheet Attached", value: "Spring/Summer Collection 06 line-sheet with size curves & MOQ 12" },
        { label: "Workflow Guarantee", value: "Manual copy & personal send only. Vitrine never fires automated emails." },
      ],
      footerNote: "Thoughtful, tailored communication engineered to open enduring retail partnerships.",
    },
  },
];

export function PipelineSection() {
  return (
    <section
      id="workflow"
      aria-labelledby="workflow-heading"
      className="scroll-mt-16 border-b border-border bg-canvas px-6 py-20 sm:px-8 sm:py-28 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header with Typographic Rhythm */}
        <div className="max-w-3xl">
          <span className="text-xs font-semibold text-accent">
            Four-Stage Wholesale Architecture
          </span>
          <h2
            id="workflow-heading"
            className="mt-3 font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink leading-tight"
          >
            A Disciplined Journey from Studio Collection to Boutique Floor
          </h2>
          <p className="mt-4 text-base sm:text-lg leading-relaxed text-muted">
            Independent fashion wholesale fails when brands rely on mass email blasts. Vitrine provides an evidence-based method to codify your line-sheet, find aligned stockists, and open relationships with genuine buyers.
          </p>
        </div>

        {/* 4 Steps in a Varied Editorial Progression */}
        <div className="mt-16 sm:mt-24 space-y-20 sm:space-y-28">
          {WORKFLOW_STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isReversed = idx % 2 === 1;

            return (
              <div
                key={step.stageNumber}
                className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-16 pt-12 border-t border-border-subtle first:pt-0 first:border-t-0"
              >
                {/* Content Column */}
                <div
                  className={`lg:col-span-6 ${
                    isReversed ? "lg:order-2" : "lg:order-1"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-primary">
                      {step.stageNumber}
                    </span>
                    <span className="h-px w-8 bg-border" aria-hidden="true" />
                    <span className="text-xs font-medium text-muted">
                      {step.kicker}
                    </span>
                  </div>

                  <h3 className="mt-4 font-display text-2xl sm:text-3xl font-bold tracking-tight text-ink">
                    {step.headline}
                  </h3>

                  {/* Problem & Solution Callout */}
                  <div className="mt-4 space-y-2 text-sm leading-relaxed text-muted">
                    <p>
                      <strong className="text-ink font-semibold">The Disconnect: </strong>
                      {step.problem}
                    </p>
                    <p>
                      <strong className="text-primary font-semibold">The Vitrine Approach: </strong>
                      {step.solution}
                    </p>
                  </div>

                  <ul className="mt-6 space-y-2.5 text-xs sm:text-sm text-ink">
                    {step.bulletPoints.map((point) => (
                      <li key={point} className="flex items-start gap-2.5">
                        <span className="mt-1.5 size-1.5 rounded-full bg-accent flex-shrink-0" />
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Specimen Preview Column */}
                <div
                  className={`lg:col-span-6 ${
                    isReversed ? "lg:order-1" : "lg:order-2"
                  }`}
                >
                  <div data-ui className="rounded-xl border border-border bg-surface p-5 sm:p-6 shadow-card transition-[border-color,box-shadow] hover:shadow-elevated hover:border-primary/40">
                    {/* Header */}
                    <div className="flex items-center justify-between pb-4 border-b border-border">
                      <div className="flex items-center gap-2.5">
                        <span className="grid size-8 place-items-center rounded-lg bg-surface-subtle text-primary border border-border-subtle">
                          <Icon size={16} />
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-ink leading-tight">
                            {step.specimen.title}
                          </p>
                          <p className="text-[11px] text-muted">
                            Vitrine {step.name}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`rounded-md border px-2.5 py-0.5 text-[11px] font-medium ${step.specimen.badgeStyle}`}
                      >
                        {step.specimen.badge}
                      </span>
                    </div>

                    {/* Details Grid */}
                    <div className="mt-4 divide-y divide-border-subtle text-xs">
                      {step.specimen.details.map((detail) => (
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

                    {/* Footer */}
                    <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between text-[11px] text-muted">
                      <span>{step.specimen.footerNote}</span>
                      <span className="text-[10px] text-subtle">Apparel Wholesale Standard</span>
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
