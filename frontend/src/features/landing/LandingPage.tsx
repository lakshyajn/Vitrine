import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { EvidenceSection } from "./EvidenceSection";
import { InteractivePreviewSection } from "./InteractivePreviewSection";
import { LandingFooter } from "./LandingFooter";
import { LandingHero } from "./LandingHero";
import { LandingNav } from "./LandingNav";
import { PipelineSection } from "./PipelineSection";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas text-ink selection:bg-primary-light selection:text-primary animate-fade-in">
      <LandingNav />
      <main id="main-content">
        <LandingHero />
        <PipelineSection />
        <InteractivePreviewSection />
        <EvidenceSection />

        {/* Section F: Final Confident Invitation Banner */}
        <section
          aria-labelledby="cta-heading"
          className="relative overflow-hidden border-b border-[#2A222C] bg-sidebar text-white px-6 py-20 sm:px-8 sm:py-24 lg:px-12 text-center"
        >
          {/* Subtle ambient plum glow */}
          <div
            className="pointer-events-none absolute -bottom-24 left-1/2 -translate-x-1/2 size-[480px] rounded-full bg-primary/30 blur-[100px]"
            aria-hidden="true"
          />

          <div className="relative mx-auto max-w-3xl">
            <span className="text-xs font-semibold text-accent">
              Wholesale Expansion for Independent Labels
            </span>
            <h2
              id="cta-heading"
              className="mt-4 font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-tight"
            >
              Your collection belongs on the world&apos;s best boutique rails.
            </h2>
            <p className="mt-4 text-base sm:text-lg text-stone-300 leading-relaxed max-w-2xl mx-auto">
              Build your wholesale-ready line-sheet, discover stockists who share your design ethos, and open direct conversations with verified buyers.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/app"
                className="pressable inline-flex items-center justify-center gap-2.5 rounded-lg bg-accent px-7 py-3.5 text-base font-semibold text-white shadow-xs transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <span>Explore the workspace</span>
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-stone-400">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={14} className="text-emerald-400" />
                No payment fees or order commissions
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={14} className="text-accent" />
                Zero automated spam bots
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={14} className="text-stone-300" />
                100% verified boutique evidence
              </span>
            </div>
          </div>
        </section>
      </main>
      <LandingFooter />
    </div>
  );
}
