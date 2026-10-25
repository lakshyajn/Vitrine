import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Compass, Copy, Mail, Package, Sparkles, Users } from "lucide-react";

type StageId = "passport" | "discovery" | "leads" | "outreach";

interface StageTab {
  id: StageId;
  stageNumber: string;
  name: string;
  summary: string;
  icon: typeof Package;
}

const STAGE_TABS: readonly StageTab[] = [
  {
    id: "passport",
    stageNumber: "Stage 01",
    name: "Product Passport",
    summary:
      "Turn your collection into structured, wholesale-ready product information: garment specifications, fabric compositions, size curves (XS–XL), trade margins, and cut lead times.",
    icon: Package,
  },
  {
    id: "discovery",
    stageNumber: "Stage 02",
    name: "Market Discovery",
    summary:
      "Discover independent multi-brand boutiques and concept stockists whose existing assortment, price point, and aesthetic ethos align with your collection.",
    icon: Compass,
  },
  {
    id: "leads",
    stageNumber: "Stage 03",
    name: "Buyer Leads",
    summary:
      "Evaluate potential stockists with complete data transparency: verified storefront presence, carried designer lines, and explicit unknowns rendered truthfully.",
    icon: Users,
  },
  {
    id: "outreach",
    stageNumber: "Stage 04",
    name: "Outreach Studio",
    summary:
      "Prepare personalized wholesale inquiries grounded in approved collection facts and retailer evidence. Review, copy, and send directly from your own email.",
    icon: Mail,
  },
];

export function InteractivePreviewSection() {
  const [activeStage, setActiveStage] = useState<StageId>("passport");
  const [copied, setCopied] = useState(false);

  const currentTab = STAGE_TABS.find((t) => t.id === activeStage) ?? STAGE_TABS[0];

  const sampleOutreachLetter = `Dear Buying Team at Boutique L'Ombre,

I have followed your curation on Rue Charlot with great admiration, particularly your thoughtful focus on European artisanal tailoring and natural fiber garments.

Our studio, Atelier Sylvan (Lisbon/London), creates limited-run menswear and womenswear focused on relaxed, architectural tailoring. For Spring/Summer, our Double-Breasted Belgian Linen Blazer (340gsm undyed flax, horn button closures) closely aligns with your floor curation alongside brands like Studio Nicholson and Casey Casey.

Key collection specifications:
• Wholesale Price: $145 USD (Suggested Retail: $360 USD · 2.48× markup)
• Minimum Opening Order: 12 units (customizable size curve across XS–XL)
• Production Lead Time: 6 weeks (cut and sewn in our Lisbon studio)

Our complete digital linesheet and swatch cards are attached for your consideration. We would welcome the opportunity to send a sample piece to your showroom.

Warm regards,
Elena Vance · Founder & Designer, Atelier Sylvan`;

  const handleCopy = () => {
    navigator.clipboard?.writeText(sampleOutreachLetter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <section
      id="walkthrough"
      aria-labelledby="walkthrough-heading"
      className="scroll-mt-24 border-b border-border bg-canvas px-6 py-14 sm:px-8 sm:py-20 lg:px-12"
    >
      {/* Anchor alias so #workflow scrolls cleanly here */}
      <div id="workflow" className="-mt-24 pt-24" aria-hidden="true" />

      <div className="mx-auto max-w-7xl">
        {/* Section Header: Balanced 2-Column Grid eliminating empty space on the right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end pb-8 border-b border-border">
          {/* Left Column: Title & Proposition */}
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 shadow-xs">
              <span className="size-2 rounded-full bg-accent" aria-hidden="true" />
              <span className="text-xs font-medium text-muted">
                Interactive wholesale workbench
              </span>
            </div>
            <h2
              id="walkthrough-heading"
              className="mt-4 font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink"
            >
              The Designer’s Wholesale Workbench in Action
            </h2>
            <p className="mt-3 text-sm sm:text-base text-muted leading-relaxed max-w-2xl">
              Experience how Vitrine codifies collection line-sheets, discovers compatible boutique stockists, verifies retail fit, and prepares bespoke wholesale inquiries.
            </p>
          </div>

          {/* Right Column: Compact 4-Stage Progression Index Card (Balances Layout) */}
          <div className="lg:col-span-5">
            <div className="rounded-xl border border-border bg-surface p-4 shadow-xs">
              <div className="flex items-center justify-between pb-2.5 border-b border-border-subtle">
                <span className="text-xs font-bold text-ink">
                  Wholesale Discovery Sequence
                </span>
                <span className="inline-flex items-center gap-1 rounded bg-surface-subtle border border-border px-2 py-0.5 text-[10px] font-medium text-muted">
                  <Sparkles size={11} className="text-accent" />
                  Illustrative demo data
                </span>
              </div>
              <div className="mt-2.5 grid grid-cols-2 gap-2 text-[11px]">
                <div className="flex items-center gap-1.5 text-muted">
                  <span className="size-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span>01. Line-Sheet Specs</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted">
                  <span className="size-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span>02. Boutique Scanning</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted">
                  <span className="size-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span>03. Evidence Screening</span>
                </div>
                <div className="flex items-center gap-1.5 text-muted">
                  <span className="size-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span>04. Studio Outreach</span>
                </div>
              </div>
              <div className="mt-3 pt-2.5 border-t border-border-subtle flex items-center justify-between">
                <span className="text-[11px] text-muted">Direct boutique relationships</span>
                <Link
                  to="/app"
                  data-btn-primary
                  style={{ backgroundColor: "#4A154B", color: "#FFFFFF" }}
                  className="btn-primary pressable inline-flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-semibold text-white shadow-xs hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                >
                  <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                    Explore workspace
                  </span>
                  <ArrowRight size={13} style={{ color: "#FFFFFF" }} className="text-white" />
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* 4 Interactive Stage Tabs with Accessible Min 44px Touch Targets */}
        <div
          className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3"
          role="tablist"
          aria-label="Wholesale Discovery Workflow Stages"
        >
          {STAGE_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeStage === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setActiveStage(tab.id)}
                data-btn-primary={isActive ? true : undefined}
                style={
                  isActive
                    ? { backgroundColor: "#4A154B", color: "#FFFFFF" }
                    : undefined
                }
                className={`pressable group flex min-h-[52px] flex-col justify-center rounded-xl p-3 sm:p-4 text-left transition-[background-color,border-color,color,box-shadow] duration-200 ${
                  isActive
                    ? "btn-primary bg-primary text-white shadow-card border border-primary"
                    : "border border-border bg-surface text-muted hover:border-primary/40 hover:text-ink hover:bg-surface-subtle"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    style={{ color: isActive ? "#FFFFFF" : undefined }}
                    className={`text-[10px] font-bold uppercase tracking-wider ${
                      isActive ? "text-white" : "text-primary"
                    }`}
                  >
                    {tab.stageNumber}
                  </span>
                  <Icon
                    size={15}
                    style={{ color: isActive ? "#FFFFFF" : undefined }}
                    className={isActive ? "text-white" : "text-muted group-hover:text-primary"}
                  />
                </div>
                <span
                  style={{ color: isActive ? "#FFFFFF" : undefined }}
                  className={`mt-1 font-display text-sm sm:text-base font-bold ${
                    isActive ? "text-white" : "text-ink"
                  }`}
                >
                  {tab.name}
                </span>
              </button>
            );
          })}
        </div>

        {/* Stage Summary Description Bar */}
        <div className="mt-3 rounded-xl border border-border-subtle bg-surface-subtle p-4 sm:p-4.5 flex items-start gap-3.5 text-xs sm:text-sm leading-relaxed text-muted transition-colors duration-200">
          <span className="mt-0.5 grid size-5 place-items-center rounded-full bg-primary/10 text-primary flex-shrink-0 font-bold text-xs">
            i
          </span>
          <div>
            <span className="font-semibold text-ink">{currentTab.name}: </span>
            <span>{currentTab.summary}</span>
          </div>
        </div>

        {/* Interactive Workbench Screen Frame */}
        <div
          data-ui
          className="mt-5 rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-elevated transition-[border-color,box-shadow] duration-200"
        >
          {/* Stage 1: Product Passport */}
          {activeStage === "passport" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-muted">
                      SKU: AS-JKT-06 · Collection 06 Spring/Summer
                    </span>
                    <span className="rounded bg-surface-subtle border border-border px-2 py-0.5 text-[10px] font-medium text-muted">
                      Illustrative demo data
                    </span>
                  </div>
                  <h3 className="font-display text-2xl font-bold text-ink mt-1">
                    Double-Breasted Belgian Linen Blazer
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 text-xs font-semibold">
                    Wholesale Line-Sheet Ready
                  </span>
                </div>
              </div>

              {/* Specification Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Wholesale Trade Price
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    $145.00 <span className="text-xs font-normal text-muted">USD</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Suggested RRP: $360.00 (2.48× markup)</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Minimum Opening Order
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    12 <span className="text-xs font-normal text-muted">units</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Size curve: 2-XS, 4-S, 4-M, 2-L</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Production Lead Time
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    6 <span className="text-xs font-normal text-muted">weeks</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Cut &amp; sewn to order in Lisbon atelier</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Studio Capacity Cap
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    60 <span className="text-xs font-normal text-muted">units / season</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Guarantees craft quality and boutique exclusivity</p>
                </div>
              </div>

              {/* Garment Construction & Fabric Details */}
              <div className="rounded-lg border border-border-subtle bg-surface-subtle p-5 text-xs text-muted">
                <p className="font-semibold text-ink text-[12px]">
                  Fabrication &amp; Construction Specifications
                </p>
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <span className="font-medium text-ink">Body:</span> 340gsm undyed natural Belgian flax
                  </div>
                  <div>
                    <span className="font-medium text-ink">Finishing:</span> French seams, unlined, piped facings
                  </div>
                  <div>
                    <span className="font-medium text-ink">Hardware:</span> Hand-carved organic dark horn buttons
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stage 2: Market Discovery */}
          {activeStage === "discovery" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-muted">
                      DISCOVERY SCAN RUN #04 · TARGET HUBS: PARIS &amp; TOKYO
                    </span>
                    <span className="rounded bg-surface-subtle border border-border px-2 py-0.5 text-[10px] font-medium text-muted">
                      Illustrative demo data
                    </span>
                  </div>
                  <h3 className="font-display text-2xl font-bold text-ink mt-1">
                    Independent Boutique Discovery Filter
                  </h3>
                </div>
                <span className="rounded bg-primary-light text-primary border border-primary-border px-2.5 py-1 text-xs font-semibold">
                  Scanned 28 Boutique Stockists
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="text-xs font-semibold text-ink">Districts Targeted</span>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Le Marais &amp; Saint-Germain (Paris) · Daikanyama &amp; Aoyama (Tokyo) · Shoreditch (London)
                  </p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="text-xs font-semibold text-ink">Aesthetic Match Filters</span>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Relaxed architectural tailoring, natural unbleached textiles, quiet luxury, slow fashion
                  </p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="text-xs font-semibold text-ink">Retail Price Compatibility</span>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Store jacket/coat range $300–$850 · Accommodates label $145 wholesale / $360 RRP
                  </p>
                </div>
              </div>

              <div className="rounded-lg border border-border-subtle bg-surface p-4 text-xs text-muted">
                <span className="font-semibold text-ink text-[12px]">
                  Boutique Filtering Criterion
                </span>
                <p className="mt-1 leading-relaxed">
                  Vitrine filters out mass-market chains and souvenir stores. Only independent multi-brand boutiques with active physical storefronts and bespoke designer curation are surfaced.
                </p>
              </div>
            </div>
          )}

          {/* Stage 3: Buyer Leads */}
          {activeStage === "leads" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-muted">
                      LEAD EVALUATION · RUE CHARLOT, PARIS 3E
                    </span>
                    <span className="rounded bg-surface-subtle border border-border px-2 py-0.5 text-[10px] font-medium text-muted">
                      Illustrative demo data
                    </span>
                    <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold">
                      VERIFIED STOREFRONT
                    </span>
                  </div>
                  <h3 className="font-display text-2xl font-bold text-ink mt-1">
                    Boutique L&apos;Ombre · Independent Concept Store
                  </h3>
                </div>
                <div className="text-right">
                  <span className="block text-[11px] font-medium text-muted">
                    Overall Fit Score
                  </span>
                  <span className="font-display text-3xl font-bold text-primary">
                    92<span className="text-base font-normal text-muted">/100</span>
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink">Physical Presence</span>
                    <span className="text-xs font-bold text-emerald-800">Verified</span>
                  </div>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Active street storefront in Le Marais, Paris 3e. Confirmed regular trading hours and active customer traffic.
                  </p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink">Price Alignment</span>
                    <span className="text-xs font-bold text-emerald-800">Compatible</span>
                  </div>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Store outerwear tier is $320–$650. Well-aligned with label wholesale $145 / retail $360.
                  </p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink">Wholesale Intake Status</span>
                    <span className="text-xs font-bold text-subtle">Not enough evidence</span>
                  </div>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Next season intake window is unconfirmed online. Truthfully marked as unknown rather than penalized with zero.
                  </p>
                </div>
              </div>

              <div className="rounded-lg border border-border-subtle bg-surface p-4 text-xs">
                <span className="font-semibold text-ink text-[12px]">
                  Carried Lines &amp; Aesthetic Overlap
                </span>
                <p className="mt-1 text-muted leading-relaxed">
                  Carries independent European labels including Studio Nicholson, Casey Casey, and Margaret Howell. Focus on raw natural fibers and relaxed tailoring.
                </p>
              </div>
            </div>
          )}

          {/* Stage 4: Outreach Studio */}
          {activeStage === "outreach" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-muted">
                      OUTREACH STUDIO · PERSONALIZED WHOLESALE INQUIRY
                    </span>
                    <span className="rounded bg-surface-subtle border border-border px-2 py-0.5 text-[10px] font-medium text-muted">
                      Illustrative demo data
                    </span>
                  </div>
                  <h3 className="font-display text-2xl font-bold text-ink mt-1">
                    Wholesale Pitch: Boutique L&apos;Ombre (Paris)
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="pressable inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-xs font-semibold text-ink shadow-xs hover:bg-surface-subtle"
                >
                  {copied ? (
                    <>
                      <Check size={14} className="text-emerald-700" />
                      <span className="text-emerald-800">Copied to Clipboard</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copy Letter Text</span>
                    </>
                  )}
                </button>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-subtle p-6 text-xs leading-relaxed text-ink whitespace-pre-wrap selection:bg-primary-light font-mono">
                {sampleOutreachLetter}
              </div>

              <div className="flex items-center justify-between text-xs text-muted pt-2 border-t border-border-subtle">
                <span className="flex items-center gap-1.5">
                  <span className="size-2 rounded-full bg-emerald-600" />
                  Manual review completed · Ready to send from designer&apos;s email client
                </span>
                <span className="text-subtle text-[11px]">
                  Zero automated email sending
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
