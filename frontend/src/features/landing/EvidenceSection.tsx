import { AlertCircle, CheckCircle2, Flame, Layers, Lock, Sparkles } from "lucide-react";

export function EvidenceSection() {
  return (
    <section
      id="evidence-philosophy"
      aria-labelledby="philosophy-heading"
      className="scroll-mt-16 border-b border-border bg-surface px-6 py-20 sm:px-8 sm:py-28 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="max-w-3xl">
          <span className="text-xs font-medium text-brass">
            Our data-truth standard
          </span>
          <h2
            id="philosophy-heading"
            className="mt-3 font-serif text-3xl sm:text-4xl lg:text-5xl font-normal tracking-tight text-ink"
          >
            Why Evidence Beats Speculation in Wholesale
          </h2>
          <p className="mt-4 text-base sm:text-lg leading-relaxed text-muted">
            Most B2B platforms rely on aggressive web scrapers that invent fit percentages and encourage makers to send generic mass pitches. Vitrine is built on an ethical, evidence-first contract.
          </p>
        </div>

        {/* 4 Pillars of the Evidence Pledge */}
        <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-2 lg:gap-12">
          {/* Pillar 1 */}
          <div data-ui className="flex flex-col rounded-xl border border-border bg-canvas p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-lg bg-surface text-primary border border-border shadow-xs">
                <AlertCircle size={20} />
              </span>
              <div>
                <h3 className="text-base font-semibold text-ink">
                  Missing Evidence Is Never Coerced to Zero
                </h3>
                <p className="text-xs text-muted">Integrity of unknown states</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              If we cannot independently verify whether a boutique currently accepts new wholesale accounts, we display <strong className="text-ink">“Not enough evidence”</strong>. We never punish an aligned stockist with a zero score or hallucinate a fake intake status.
            </p>
            <div className="mt-5 rounded-md border border-border-subtle bg-surface p-3 text-xs text-ink">
              <code>unknown → null → &quot;Not enough evidence&quot;</code>
            </div>
          </div>

          {/* Pillar 2 */}
          <div data-ui className="flex flex-col rounded-xl border border-border bg-canvas p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-lg bg-surface text-brass border border-border shadow-xs">
                <Layers size={20} />
              </span>
              <div>
                <h3 className="text-base font-semibold text-ink">
                  Separating Hypotheses from Verified Facts
                </h3>
                <p className="text-xs text-muted">Strict epistemic boundaries</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              Cultural affinity and aesthetic resonance are subjective hypotheses. Verified facts—such as physical store presence, carried lines, and retail price tiers—are objectively verified data. Vitrine always keeps them separate in your view.
            </p>
            <div className="mt-5 rounded-md border border-border-subtle bg-surface p-3 text-xs text-ink">
              <code>verified_fact !== aesthetic_hypothesis</code>
            </div>
          </div>

          {/* Pillar 3 */}
          <div data-ui className="flex flex-col rounded-xl border border-border bg-canvas p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-lg bg-surface text-ink border border-border shadow-xs">
                <Flame size={20} />
              </span>
              <div>
                <h3 className="text-base font-semibold text-ink">
                  Zero Automated Email Sending or Spam Bots
                </h3>
                <p className="text-xs text-muted">Human discretion by design</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              Vitrine has no automated &quot;Send Campaign&quot; button and never connects to SMTP bots. Boutique owners value personal relationships. Vitrine prepares the facts and drafts the letter; you review, copy, and send via your own studio email.
            </p>
            <div className="mt-5 rounded-md border border-border-subtle bg-surface p-3 text-xs text-ink">
              <code>draft → review → copy → manual_track</code>
            </div>
          </div>

          {/* Pillar 4 */}
          <div data-ui className="flex flex-col rounded-xl border border-border bg-canvas p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-lg bg-surface text-emerald-800 border border-border shadow-xs">
                <Lock size={20} />
              </span>
              <div>
                <h3 className="text-base font-semibold text-ink">
                  No Commissions, Gateways, or Take Rates
                </h3>
                <p className="text-xs text-muted">Pure studio research instrument</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              Vitrine takes zero percentage of your wholesale orders. There are no payment processors, invoices, or hidden transaction fees. Your trade accounts and buyer relationships remain entirely your studio&apos;s direct assets.
            </p>
            <div className="mt-5 rounded-md border border-border-subtle bg-surface p-3 text-xs text-ink">
              <code>0% order fee · independent maker autonomy</code>
            </div>
          </div>
        </div>

        {/* Certification Callout */}
        <div data-ui className="mt-12 rounded-xl border border-brass-border bg-brass-light/30 p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 size={20} className="text-brass mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-ink text-sm sm:text-base">
                  The Vitrine Commitment to Studio Craftsmanship
                </p>
                <p className="mt-1 text-xs sm:text-sm text-muted max-w-2xl">
                  We never fabricate retailers, cite fictional citations, or generate fake customer testimonials. Every feature is engineered to honor the labor of the artisan and the discernment of the independent buyer.
                </p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 self-start sm:self-auto rounded-md bg-surface px-3 py-1.5 text-xs font-semibold text-ink border border-border shadow-xs">
              <Sparkles size={13} className="text-primary" />
              Verified Standard
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
