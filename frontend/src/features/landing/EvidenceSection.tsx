import { AlertCircle, CheckCircle2, Eye, Flame, Lock, ShieldCheck, Sparkles } from "lucide-react";

export function EvidenceSection() {
  return (
    <section
      id="evidence-standard"
      aria-labelledby="evidence-heading"
      className="scroll-mt-16 border-b border-border bg-surface px-6 py-20 sm:px-8 sm:py-28 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="max-w-3xl">
          <span className="text-xs font-semibold text-accent">
            Our Data-Truth Standard
          </span>
          <h2
            id="evidence-heading"
            className="mt-3 font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink"
          >
            Why Evidence Beats Speculation in Fashion Wholesale
          </h2>
          <p className="mt-4 text-base sm:text-lg leading-relaxed text-muted">
            Independent boutique buyers are discerning curators who ignore mass cold emails. Most B2B platforms rely on aggressive bots that invent fake match percentages. Vitrine is built on strict data honesty.
          </p>
        </div>

        {/* The Three Epistemic States: A Visual Comparison Breakdown */}
        <div className="mt-16 rounded-2xl border border-border bg-canvas p-6 sm:p-10 shadow-xs">
          <div className="pb-6 border-b border-border">
            <h3 className="font-display text-xl font-bold text-ink">
              The Three-State Truth Standard
            </h3>
            <p className="mt-1 text-sm text-muted">
              How Vitrine categorizes retail information so you never pitch a stockist based on fabricated data.
            </p>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-8 md:grid-cols-3">
            {/* State 1: Verified Fact */}
            <div data-ui className="flex flex-col justify-between rounded-xl border border-emerald-200 bg-emerald-50/40 p-6">
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid size-9 place-items-center rounded-lg bg-emerald-100 text-emerald-800">
                    <ShieldCheck size={18} />
                  </span>
                  <span className="rounded bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                    Verified Fact
                  </span>
                </div>
                <h4 className="mt-4 font-display text-base font-bold text-emerald-950">
                  Source-Supported Store Evidence
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-emerald-900/80">
                  Concrete, documented retail data: physical street address, regular operating hours, confirmed price ranges, and verified carried designer labels.
                </p>
              </div>

              <div className="mt-6 rounded border border-emerald-200/80 bg-white p-3 text-[11px] text-emerald-950">
                <span className="font-semibold block text-[10px] text-emerald-700">Example:</span>
                “Physical storefront confirmed: 14 Rue Charlot, Paris 3e. Retail blazer tier $320–$650.”
              </div>
            </div>

            {/* State 2: Aesthetic Hypothesis */}
            <div data-ui className="flex flex-col justify-between rounded-xl border border-primary-border bg-primary-light/40 p-6">
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid size-9 place-items-center rounded-lg bg-primary-light text-primary">
                    <Eye size={18} />
                  </span>
                  <span className="rounded bg-primary-light text-primary border border-primary-border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                    Aesthetic Hypothesis
                  </span>
                </div>
                <h4 className="mt-4 font-display text-base font-bold text-ink">
                  Style &amp; Cultural Alignment
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  Subjective style overlap: silhouettes, color palettes, textile philosophies, and customer demographic alignment. Kept strictly distinct from verified facts.
                </p>
              </div>

              <div className="mt-6 rounded border border-primary-border/60 bg-white p-3 text-[11px] text-ink">
                <span className="font-semibold block text-[10px] text-primary">Example:</span>
                “Collection alignment: Relaxed unisex tailoring in natural linen matches boutique aesthetic.”
              </div>
            </div>

            {/* State 3: Unknown Evidence */}
            <div data-ui className="flex flex-col justify-between rounded-xl border border-border bg-surface p-6">
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid size-9 place-items-center rounded-lg bg-surface-subtle text-muted">
                    <AlertCircle size={18} />
                  </span>
                  <span className="rounded bg-surface-subtle text-muted border border-border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                    Unknown State
                  </span>
                </div>
                <h4 className="mt-4 font-display text-base font-bold text-ink">
                  Missing or Incomplete Signals
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  Information that cannot be verified online. Rendered honestly as <strong className="text-ink">“Not enough evidence”</strong>—never coerced to zero or invented.
                </p>
              </div>

              <div className="mt-6 rounded border border-border bg-canvas p-3 text-[11px] text-muted">
                <span className="font-semibold block text-[10px] text-ink">Example:</span>
                “Wholesale intake window: Not enough evidence. Buyer intake dates not disclosed online.”
              </div>
            </div>
          </div>
        </div>

        {/* Additional Ethical Commitments: Bot Spam & Commissions */}
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
          {/* Commitment 1 */}
          <div data-ui className="rounded-xl border border-border bg-surface p-6 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-lg bg-surface-subtle text-accent border border-border">
                <Flame size={18} />
              </span>
              <div>
                <h4 className="text-sm font-bold text-ink">
                  Zero Automated Email Sending or Spam Bots
                </h4>
                <p className="text-xs text-muted">Human Discretion by Design</p>
              </div>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted">
              Boutique owners recognize generic mass mailers and delete them instantly. Vitrine prepares verified collection facts; you review, copy, and send personally from your own designer email.
            </p>
          </div>

          {/* Commitment 2 */}
          <div data-ui className="rounded-xl border border-border bg-surface p-6 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-lg bg-surface-subtle text-emerald-800 border border-border">
                <Lock size={18} />
              </span>
              <div>
                <h4 className="text-sm font-bold text-ink">
                  No Commissions, Gateways, or Take Rates
                </h4>
                <p className="text-xs text-muted">Pure Studio Wholesale Instrument</p>
              </div>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted">
              Vitrine takes zero percent of your wholesale orders. There are no payment processors, invoices, or hidden transaction cuts. Every buyer relationship belongs entirely to your label.
            </p>
          </div>
        </div>

        {/* Standards Certification */}
        <div data-ui className="mt-10 rounded-xl border border-border bg-canvas p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={18} className="text-primary mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs sm:text-sm font-semibold text-ink">
                The Vitrine Anti-Slop Data Guarantee
              </p>
              <p className="mt-0.5 text-xs text-muted">
                We never fabricate stockists, cite fake retailer testimonials, or generate false buyer statistics.
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 self-start sm:self-auto rounded-md bg-surface px-3 py-1.5 text-xs font-semibold text-ink border border-border shadow-xs">
            <Sparkles size={13} className="text-accent" />
            Verified Standard
          </span>
        </div>
      </div>
    </section>
  );
}
