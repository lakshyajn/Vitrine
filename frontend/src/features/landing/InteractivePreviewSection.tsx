import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Copy, Sparkles } from "lucide-react";

export function InteractivePreviewSection() {
  const [activeTab, setActiveTab] = useState<"passport" | "match" | "outreach">("passport");
  const [copied, setCopied] = useState(false);

  const samplePitch = `Dear Curation Team at Gallery Hakujin,

I have followed your seasonal exhibitions in Daikanyama with great admiration, particularly your recent focus on reduction-fired contemporary ceramics.

Our studio, Komorebi Stoneware (Devon/Kyoto), produces hand-thrown fluted table vessels fired at 1280°C with local mineral ash glazes. Given your stockist focus on tactile Japanese homeware, we believe our Series 04 Amphora would resonate with your clientele.

Wholesale specifications:
• Wholesale price: $48 USD (Suggested Retail: $120 USD · 2.5x markup)
• Minimum opening order: 6 units
• Production lead time: 4 weeks

Our full Product Passport and trade sheet are attached for your consideration.

Warm regards,
Komorebi Studio Atelier`;

  const handleCopy = () => {
    navigator.clipboard?.writeText(samplePitch);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section
      id="preview"
      aria-labelledby="preview-heading"
      className="scroll-mt-16 border-b border-border bg-canvas px-6 py-20 sm:px-8 sm:py-28 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 pb-8 border-b border-border">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 shadow-xs">
              <span className="size-2 rounded-full bg-brass" aria-hidden="true" />
              <span className="text-xs font-medium text-muted">
                Interactive studio simulation
              </span>
            </div>
            <h2
              id="preview-heading"
              className="mt-4 font-serif text-3xl sm:text-4xl lg:text-5xl font-normal tracking-tight text-ink"
            >
              The Maker’s Workbench in Action
            </h2>
            <p className="mt-3 text-base text-muted">
              Explore how Vitrine structures trade data, evaluates boutique fit, and drafts evidence-backed inquiries.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-muted shadow-xs">
              <Sparkles size={13} className="text-brass" />
              Demo data preview
            </span>
            <Link
              to="/app"
              className="pressable inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-primary-hover"
            >
              <span>Open live workspace</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="mt-8 flex flex-wrap gap-2" role="tablist" aria-label="Interactive Preview Tabs">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "passport"}
            onClick={() => setActiveTab("passport")}
            className={`pressable rounded-lg px-4 py-2.5 text-xs sm:text-sm font-semibold transition-colors ${
              activeTab === "passport"
                ? "bg-ink text-white shadow-xs"
                : "border border-border bg-surface text-muted hover:text-ink hover:bg-surface-subtle"
            }`}
          >
            1. Product Passport Specification
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "match"}
            onClick={() => setActiveTab("match")}
            className={`pressable rounded-lg px-4 py-2.5 text-xs sm:text-sm font-semibold transition-colors ${
              activeTab === "match"
                ? "bg-ink text-white shadow-xs"
                : "border border-border bg-surface text-muted hover:text-ink hover:bg-surface-subtle"
            }`}
          >
            2. Vetted Stockist Fit &amp; Evidence
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "outreach"}
            onClick={() => setActiveTab("outreach")}
            className={`pressable rounded-lg px-4 py-2.5 text-xs sm:text-sm font-semibold transition-colors ${
              activeTab === "outreach"
                ? "bg-ink text-white shadow-xs"
                : "border border-border bg-surface text-muted hover:text-ink hover:bg-surface-subtle"
            }`}
          >
            3. Tailored Outreach Draft
          </button>
        </div>

        {/* Workbench Frame Container */}
        <div data-ui className="mt-6 rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-elevated transition-colors">
          {activeTab === "passport" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <span className="text-[11px] font-medium text-muted">
                    SKU: KM-AMP-04 · Vitrine Passport
                  </span>
                  <h3 className="font-serif text-2xl font-normal text-ink">
                    Series 04 Hand-thrown Stoneware Amphora
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 text-xs font-semibold">
                    Wholesale Ready
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Wholesale Price
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    $48.00 <span className="text-xs font-normal text-muted">USD</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Suggested retail: $120.00 (60% margin)</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Minimum Order Quantity
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    6 <span className="text-xs font-normal text-muted">units</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Opening wholesale minimum</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Studio Lead Time
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    4 <span className="text-xs font-normal text-muted">weeks</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Handcrafted to order in studio</p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <span className="block text-[11px] font-medium text-muted">
                    Monthly Studio Capacity
                  </span>
                  <p className="mt-1 text-2xl font-bold text-ink">
                    40 <span className="text-xs font-normal text-muted">units / mo</span>
                  </p>
                  <p className="mt-1 text-xs text-muted">Protected craft limits</p>
                </div>
              </div>

              <div className="rounded-lg border border-border-subtle bg-surface-subtle p-5 text-xs text-muted">
                <p className="font-semibold text-ink text-[12px]">
                  Material &amp; Craft Dimension Specifications
                </p>
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <span className="font-medium text-ink">Dimensions:</span> 38cm H × 22cm Dia (3.2kg net)
                  </div>
                  <div>
                    <span className="font-medium text-ink">Body:</span> Coarse iron reduction stoneware
                  </div>
                  <div>
                    <span className="font-medium text-ink">Finish:</span> Natural wood-ash glaze, food-safe
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "match" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium text-muted">
                      Lead evaluation · Daikanyama, Tokyo
                    </span>
                    <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold">
                      Verified Stockist
                    </span>
                  </div>
                  <h3 className="font-serif text-2xl font-normal text-ink mt-1">
                    Gallery Hakujin · Contemporary Living
                  </h3>
                </div>
                <div className="text-right">
                  <span className="block text-[11px] font-medium text-muted">
                    Overall Fit Score
                  </span>
                  <span className="text-3xl font-bold text-primary">
                    91<span className="text-base font-normal text-muted">/100</span>
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
                    Active street-level gallery in Daikanyama. Regular opening hours and documented foot traffic confirmed.
                  </p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink">Price Alignment</span>
                    <span className="text-xs font-bold text-emerald-800">Strong (94%)</span>
                  </div>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Current retail ceramics tier: $80–$250. Accommodates maker wholesale $48 / retail $120.
                  </p>
                </div>

                <div className="rounded-lg border border-border-subtle bg-surface-subtle p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink">Wholesale Intake</span>
                    <span className="text-xs font-bold text-subtle">Not enough evidence</span>
                  </div>
                  <p className="mt-2 text-xs text-muted leading-relaxed">
                    Intake cycle is unconfirmed online. Truthfully marked as unknown rather than penalized with 0.
                  </p>
                </div>
              </div>

              <div className="rounded-lg border border-border-subtle bg-surface p-4 text-xs">
                <span className="font-semibold text-ink text-[12px]">
                  Carried Lines &amp; Aesthetic Overlap
                </span>
                <p className="mt-1 text-muted leading-relaxed">
                  Carries wood-fired ceramics from Mashiko and Kyoto, washed linen throws, and hand-cast bronze incense burners. Zero mass-produced resin or factory slipcast wares.
                </p>
              </div>
            </div>
          )}

          {activeTab === "outreach" && (
            <div className="animate-fade-in space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
                <div>
                  <span className="text-[11px] font-medium text-muted">
                    Outreach Studio · Personalized inquiry draft
                  </span>
                  <h3 className="font-serif text-2xl font-normal text-ink mt-1">
                    Wholesale Inquiry: Gallery Hakujin
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

              <div className="rounded-xl border border-border-subtle bg-surface-subtle p-6 text-xs leading-relaxed text-ink whitespace-pre-wrap selection:bg-primary-light">
                {samplePitch}
              </div>

              <div className="flex items-center justify-between text-xs text-muted pt-2 border-t border-border-subtle">
                <span className="flex items-center gap-1.5">
                  <span className="size-2 rounded-full bg-emerald-600" />
                  Manual review completed · Ready for maker email client
                </span>
                <span className="text-subtle text-[11px]">
                  Vitrine Outbox Contract
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
