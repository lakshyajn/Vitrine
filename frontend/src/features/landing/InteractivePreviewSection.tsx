import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Compass, Copy, Mail, Package, Sparkles, Users } from "lucide-react";

type StageId = "passport" | "discovery" | "leads" | "outreach";

interface StageTab {
  id: StageId;
  label: string;
  shortLabel: string;
  icon: typeof Package;
}

const STAGE_TABS: readonly StageTab[] = [
  { id: "passport", label: "1. Product Passport (Apparel Line-Sheet)", shortLabel: "1. Passport", icon: Package },
  { id: "discovery", label: "2. Market Discovery (Boutique Scan)", shortLabel: "2. Discovery", icon: Compass },
  { id: "leads", label: "3. Buyer Leads (Evidence Evaluation)", shortLabel: "3. Buyer Leads", icon: Users },
  { id: "outreach", label: "4. Outreach Studio (Bespoke Letter)", shortLabel: "4. Outreach", icon: Mail },
];

export function InteractivePreviewSection() {
  const [activeStage, setActiveStage] = useState<StageId>("passport");
  const [copied, setCopied] = useState(false);

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
      className="scroll-mt-16 border-b border-border bg-canvas px-6 py-20 sm:px-8 sm:py-28 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 pb-8 border-b border-border">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 shadow-xs">
              <span className="size-2 rounded-full bg-accent" aria-hidden="true" />
              <span className="text-xs font-medium text-muted">
                Interactive apparel studio simulation
              </span>
            </div>
            <h2
              id="walkthrough-heading"
              className="mt-4 font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink"
            >
              The Designer’s Wholesale Workbench in Action
            </h2>
            <p className="mt-3 text-base text-muted">
              Explore how Vitrine organizes collection specifications, runs boutique scans, evaluates stockist fit, and crafts tailored wholesale correspondence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-muted shadow-xs">
              <Sparkles size={13} className="text-accent" />
              Demo preview · Illustrative data
            </span>
            <Link
              to="/app"
              className="pressable inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-primary-hover"
            >
              <span>Explore workspace</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>

        {/* 4 Interactive Stage Tabs */}
        <div className="mt-8 flex flex-wrap gap-2" role="tablist" aria-label="Interactive Workflow Stages">
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
                className={`pressable inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-xs sm:text-sm font-semibold transition-colors ${
                  isActive
                    ? "bg-primary text-white shadow-xs"
                    : "border border-border bg-surface text-muted hover:text-ink hover:bg-surface-subtle"
                }`}
              >
                <Icon size={15} />
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.shortLabel}</span>
              </button>
            );
          })}
        </div>

        {/* Interactive Workbench Screen Frame */}
        <div data-ui className="mt-6 rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-elevated transition-colors">
          {/* Stage 1: Product Passport */}
          {activeStage === "passport" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <span className="text-[11px] font-medium text-muted">
                    SKU: AS-JKT-06 · Collection 06 Spring/Summer
                  </span>
                  <h3 className="font-display text-2xl font-bold text-ink mt-0.5">
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
                    Wholesale Price
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    $145.00 <span className="text-xs font-normal text-muted">USD</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Suggested RRP: $360.00 (2.48× markup)</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Minimum Order Quantity
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
                  <p className="mt-1 text-xs text-muted">Cut &amp; sewn to order in Lisbon</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Studio Capacity Cap
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    60 <span className="text-xs font-normal text-muted">units / season</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Protects craft quality &amp; exclusivity</p>
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
                  <span className="text-[11px] font-medium text-muted">
                    DISCOVERY SCAN RUN #04 · TARGET HUBS: PARIS &amp; TOKYO
                  </span>
                  <h3 className="font-display text-2xl font-bold text-ink mt-0.5">
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
                    Store jacket/coat price range $300–$850 · Matches maker $145 wholesale / $360 RRP
                  </p>
                </div>
              </div>

              <div className="rounded-lg border border-border-subtle bg-surface p-4 text-xs text-muted">
                <span className="font-semibold text-ink text-[12px]">
                  Regional Discovery Rule
                </span>
                <p className="mt-1 leading-relaxed">
                  Vitrine filters out mass-market department stores and fast-fashion chains. Only independent multi-brand boutiques with verified street storefronts and bespoke curation are surfaced.
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
                    <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold">
                      VERIFIED BOUTIQUE
                    </span>
                  </div>
                  <h3 className="font-display text-2xl font-bold text-ink mt-0.5">
                    Boutique L&apos;Ombre · Independent Designer Concept
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
                    <span className="text-xs font-bold text-emerald-800">Strong (95%)</span>
                  </div>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Store blazer tier is $320–$650. Perfectly accommodates maker wholesale $145 / retail $360.
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
                  Carries independent European labels including Studio Nicholson, Casey Casey, and Margaret Howell. Focus on raw natural fibers, architectural tailoring, and zero polyester or synthetic fabrics.
                </p>
              </div>
            </div>
          )}

          {/* Stage 4: Outreach Studio */}
          {activeStage === "outreach" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <span className="text-[11px] font-medium text-muted">
                    OUTREACH STUDIO · PERSONALIZED WHOLESALE INQUIRY
                  </span>
                  <h3 className="font-display text-2xl font-bold text-ink mt-0.5">
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
                  Zero Automated Email Sending Policy
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
