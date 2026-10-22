import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import { BRAND_HEADLINE, BRAND_SUBHEAD } from "@/config/brand";

export function LandingHero() {
  const [imageError, setImageError] = useState(false);

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative overflow-hidden bg-sidebar text-white border-b border-[#2A222C] px-6 pt-10 pb-16 sm:px-8 sm:pt-16 sm:pb-20 lg:px-12"
    >
      {/* Subtle ambient lighting accent in deep plum */}
      <div
        className="pointer-events-none absolute -top-40 right-0 size-[550px] rounded-full bg-primary/25 blur-[120px]"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl">
        <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-14">
          {/* Left Column: Editorial Value Proposition & Actions */}
          <div className="flex flex-col lg:col-span-7">
            {/* Kicker Eyebrow */}
            <div className="inline-flex items-center gap-2 self-start rounded-full border border-white/15 bg-white/5 px-3.5 py-1.5 shadow-xs">
              <span className="size-2 rounded-full bg-accent" aria-hidden="true" />
              <span className="text-xs font-medium text-stone-300">
                Wholesale discovery for independent fashion labels
              </span>
            </div>

            {/* Headline in Space Grotesk */}
            <h1
              id="hero-heading"
              className="mt-5 font-display text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-[1.08]"
            >
              {BRAND_HEADLINE}
            </h1>

            {/* Supporting Copy in Inter */}
            <p className="mt-5 max-w-2xl text-base sm:text-lg leading-relaxed text-stone-300">
              {BRAND_SUBHEAD}
            </p>

            {/* Above-the-fold Action CTAs */}
            <div className="mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5">
              <Link
                to="/app"
                className="pressable inline-flex items-center justify-center gap-2.5 rounded-lg bg-accent px-6 py-3.5 text-sm sm:text-base font-semibold text-white shadow-xs transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <span>Explore the workspace</span>
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
              <a
                href="#workflow"
                className="pressable inline-flex items-center justify-center gap-2 rounded-lg border border-white/20 bg-white/5 px-5 py-3.5 text-sm sm:text-base font-medium text-stone-200 shadow-xs transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <span>See how it works</span>
                <ArrowDown size={16} className="text-stone-400" aria-hidden="true" />
              </a>
            </div>

            {/* Trust & Transparency Row */}
            <div className="mt-9 grid grid-cols-1 sm:grid-cols-2 gap-3 pt-6 border-t border-white/10 text-xs text-stone-300">
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-accent flex-shrink-0" />
                <span>Zero automated cold email blasts</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
                <span>100% verified boutique retailer evidence</span>
              </div>
            </div>
          </div>

          {/* Right Column: Architectural Fashion Atelier Exhibition Framing */}
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl border border-white/15 bg-white/5 p-3 sm:p-4 shadow-elevated">
              {/* Image Frame */}
              <div className="relative overflow-hidden rounded-xl border border-white/10 bg-black/40 aspect-[4/3]">
                <img
                  src={
                    imageError
                      ? "/images/fashion-atelier-fallback.svg"
                      : "/images/fashion-collection-atelier.webp"
                  }
                  onError={() => {
                    if (!imageError) {
                      setImageError(true);
                    }
                  }}
                  alt="Independent designer fashion showroom with tailored double-breasted linen garments on a minimalist blackened steel rail"
                  className="size-full object-cover object-center transition-transform duration-700 hover:scale-[1.02]"
                  width={1200}
                  height={896}
                  loading="eager"
                />

                {/* Live Collection Pill */}
                <div className="absolute top-3 left-3 rounded-md bg-black/80 px-2.5 py-1 text-[11px] font-medium tracking-wide text-white border border-white/10">
                  Collection 06 · Studio Tailoring
                </div>

                <div className="absolute bottom-3 right-3 rounded-md bg-white px-2.5 py-1 text-[11px] font-semibold text-ink shadow-xs">
                  Evidence-Led Match
                </div>
              </div>

              {/* Inset Line-Sheet Specification Card */}
              <div data-ui className="mt-3.5 rounded-lg border border-white/10 bg-[#201A22] p-3.5 text-xs text-stone-300">
                <div className="flex items-center justify-between pb-2 border-b border-white/10">
                  <span className="font-semibold text-white">Double-Breasted Belgian Linen Blazer</span>
                  <span className="rounded bg-accent/20 border border-accent/40 px-2 py-0.5 text-[10px] font-bold text-rose-300">
                    PASSPORT SPEC
                  </span>
                </div>
                <div className="mt-2.5 grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="block text-[10px] font-medium text-stone-400">
                      Fabric &amp; Trim
                    </span>
                    <span className="text-stone-200 font-medium">340gsm undyed flax, horn buttons</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-medium text-stone-400">
                      Wholesale / Retail
                    </span>
                    <span className="text-white font-medium">$145 / $360 (2.5×)</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-medium text-stone-400">
                      Minimum Opening Order
                    </span>
                    <span className="text-stone-200 font-medium">12 units · Size curve XS–XL</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-medium text-stone-400">
                      Target Boutique Tier
                    </span>
                    <span className="text-stone-200 font-medium">Independent designer concept</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
