import { AlertCircle, CheckCircle2, Eye, Flame, Lock, ShieldCheck, Sparkles } from "lucide-react";

export function EvidenceSection() {
  return (
    <section
      id="evidence-standard"
      aria-labelledby="evidence-heading"
      className="scroll-mt-24 border-b border-border bg-surface px-6 py-14 sm:px-8 sm:py-20 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header: Balanced 2-Column Grid eliminating empty space on the right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end pb-8 border-b border-border">
          {/* Left Column: Heading & Philosophy */}
          <div className="lg:col-span-7">
            <span className="text-xs font-semibold text-accent">
              Our Data Integrity Standard
            </span>
            <h2
              id="evidence-heading"
              className="mt-3 font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink"
            >
              Why Evidence Beats Speculation in Fashion Wholesale
            </h2>
            <p className="mt-3 text-sm sm:text-base leading-relaxed text-muted max-w-2xl">
              Independent boutique buyers are discerning curators who ignore mass cold emails. Vitrine provides clear, verifiable stockist evidence rather than fabricated match scores.
            </p>
          </div>

          {/* Right Column: Core Truth Invariants Card (Balances Layout) */}
          <div className="lg:col-span-5">
            <div className="rounded-xl border border-border bg-canvas p-4 shadow-xs">
              <span className="text-xs font-bold text-ink block pb-2 border-b border-border-subtle">
                Core Epistemic Invariants
              </span>
              <ul className="mt-2.5 space-y-2 text-[11px] text-muted">
                <li className="flex items-start gap-2">
                  <span className="mt-1 size-1.5 rounded-full bg-emerald-600 flex-shrink-0" />
                  <span>Verified store facts are strictly isolated from aesthetic hypotheses.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 size-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span>Missing signals remain &ldquo;Not enough evidence&rdquo;&mdash;never coerced to zero.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 size-1.5 rounded-full bg-accent flex-shrink-0" />
                  <span>Manual review only: zero automated cold email blasts or bots.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* The Three Epistemic States: Visual Breakdown */}
        <div className="mt-10 rounded-2xl border border-border bg-canvas p-6 sm:p-8 shadow-xs">
          <div className="pb-5 border-b border-border">
            <h3 className="font-display text-xl font-bold text-ink">
              The Three-State Truth Standard
            </h3>
            <p className="mt-1 text-xs sm:text-sm text-muted">
              How Vitrine categorizes retail information so you never approach a stockist based on fabricated data.
            </p>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* State 1: Verified Fact */}
            <div data-ui className="flex flex-col justify-between rounded-xl border border-emerald-200 bg-emerald-50/40 p-5">
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid size-8 place-items-center rounded-lg bg-emerald-100 text-emerald-800">
                    <ShieldCheck size={16} />
                  </span>
                  <span className="rounded bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                    Verified Fact
                  </span>
                </div>
                <h4 className="mt-3.5 font-display text-base font-bold text-emerald-950">
                  Documented Store Evidence
                </h4>
                <p className="mt-1.5 text-xs leading-relaxed text-emerald-900/80">
                  Concrete retail signals: physical storefront address, operating hours, confirmed price ranges, and verified carried designer labels.
                </p>
              </div>

              <div className="mt-5 rounded border border-emerald-200/80 bg-white p-2.5 text-[11px] text-emerald-950">
                <span className="font-semibold block text-[10px] text-emerald-700">
                  Illustrative example:
                </span>
                &ldquo;Physical storefront confirmed: 14 Rue Charlot, Paris 3e. Retail outerwear tier $320&ndash;$650.&rdquo;
              </div>
            </div>

            {/* State 2: Aesthetic Hypothesis */}
            <div data-ui className="flex flex-col justify-between rounded-xl border border-primary-border bg-primary-light/40 p-5">
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid size-8 place-items-center rounded-lg bg-primary-light text-primary">
                    <Eye size={16} />
                  </span>
                  <span className="rounded bg-primary-light text-primary border border-primary-border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                    Aesthetic Hypothesis
                  </span>
                </div>
                <h4 className="mt-3.5 font-display text-base font-bold text-ink">
                  Style &amp; Curation Alignment
                </h4>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">
                  Subjective style overlap: silhouettes, color palettes, textile philosophies, and customer demographics. Kept strictly distinct from verified store facts.
                </p>
              </div>

              <div className="mt-5 rounded border border-primary-border/60 bg-white p-2.5 text-[11px] text-ink">
                <span className="font-semibold block text-[10px] text-primary">
                  Illustrative example:
                </span>
                &ldquo;Collection alignment: Relaxed unisex tailoring in natural linen matches boutique aesthetic.&rdquo;
              </div>
            </div>

            {/* State 3: Unknown Evidence */}
            <div data-ui className="flex flex-col justify-between rounded-xl border border-border bg-surface p-5">
              <div>
                <div className="flex items-center justify-between">
                  <span className="grid size-8 place-items-center rounded-lg bg-surface-subtle text-muted">
                    <AlertCircle size={16} />
                  </span>
                  <span className="rounded bg-surface-subtle text-muted border border-border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                    Unknown State
                  </span>
                </div>
                <h4 className="mt-3.5 font-display text-base font-bold text-ink">
                  Missing or Incomplete Signals
                </h4>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">
                  Information that cannot be verified online. Rendered honestly as <strong className="text-ink">&ldquo;Not enough evidence&rdquo;</strong>&mdash;never coerced to zero or invented.
                </p>
              </div>

              <div className="mt-5 rounded border border-border bg-canvas p-2.5 text-[11px] text-muted">
                <span className="font-semibold block text-[10px] text-ink">
                  Illustrative example:
                </span>
                &ldquo;Wholesale intake window: Not enough evidence. Buyer intake dates not disclosed online.&rdquo;
              </div>
            </div>
          </div>
        </div>

        {/* Ethical Foundations: Direct Relationships & Zero Take Rates */}
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          {/* Commitment 1 */}
          <div data-ui className="rounded-xl border border-border bg-surface p-5 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-8 place-items-center rounded-lg bg-surface-subtle text-accent border border-border">
                <Flame size={16} />
              </span>
              <div>
                <h4 className="text-sm font-bold text-ink">
                  Zero Automated Email Sending
                </h4>
                <p className="text-[11px] text-muted">Human Discretion by Design</p>
              </div>
            </div>
            <p className="mt-2.5 text-xs leading-relaxed text-muted">
              Boutique owners immediately discard automated mailers. Vitrine organizes verified line-sheet facts and retailer context; you review, copy, and send directly from your studio email client.
            </p>
          </div>

          {/* Commitment 2 */}
          <div data-ui className="rounded-xl border border-border bg-surface p-5 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-8 place-items-center rounded-lg bg-surface-subtle text-emerald-800 border border-border">
                <Lock size={16} />
              </span>
              <div>
                <h4 className="text-sm font-bold text-ink">
                  No Order Commissions or Gateways
                </h4>
                <p className="text-[11px] text-muted">Pure Studio Wholesale Instrument</p>
              </div>
            </div>
            <p className="mt-2.5 text-xs leading-relaxed text-muted">
              Vitrine takes zero percent of your wholesale orders. There are no payment processors, invoices, or transactional fees. Every buyer relationship belongs entirely to your label.
            </p>
          </div>
        </div>

        {/* Standards Certification */}
        <div data-ui className="mt-6 rounded-xl border border-border bg-canvas p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={17} className="text-primary mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs sm:text-sm font-semibold text-ink">
                The Vitrine Data Integrity Pledge
              </p>
              <p className="mt-0.5 text-xs text-muted">
                We never fabricate stockists, cite fake retailer testimonials, or generate false buyer statistics.
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 self-start sm:self-auto rounded-md bg-surface px-3 py-1.5 text-xs font-semibold text-ink border border-border shadow-xs">
            <Sparkles size={12} className="text-accent" />
            Evidence-Backed Standard
          </span>
        </div>
      </div>
    </section>
  );
}
