import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import { BRAND_HEADLINE, BRAND_SUBHEAD } from "@/config/brand";

export function LandingHero() {
  const [imageError, setImageError] = useState(false);

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative overflow-hidden border-b border-border bg-canvas px-6 pt-12 pb-16 sm:px-8 sm:pt-20 sm:pb-24 lg:px-12"
    >
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12 lg:gap-16">
          {/* Left Column: Value Proposition & CTAs */}
          <div className="flex flex-col lg:col-span-7">
            {/* Kicker Tag */}
            <div className="inline-flex items-center gap-2 self-start rounded-full border border-border bg-surface px-3.5 py-1.5 shadow-xs">
              <span className="size-2 rounded-full bg-primary" aria-hidden="true" />
              <span className="text-xs font-medium text-muted">
                Wholesale discovery for independent studios
              </span>
            </div>

            {/* Headline in Editorial Newsreader Serif */}
            <h1
              id="hero-heading"
              className="mt-6 font-serif text-3xl sm:text-5xl lg:text-6xl font-normal tracking-tight text-ink leading-[1.12]"
            >
              {BRAND_HEADLINE}
            </h1>

            {/* Subhead in Clean Inter Sans */}
            <p className="mt-6 max-w-2xl text-base sm:text-lg leading-relaxed text-muted">
              {BRAND_SUBHEAD}
            </p>

            {/* Working Action CTAs */}
            <div className="mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <Link
                to="/app"
                className="pressable inline-flex items-center justify-center gap-2.5 rounded-lg bg-primary px-6 py-3.5 text-base font-semibold text-white shadow-xs transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
              >
                <span>Open Studio Workspace</span>
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
              <a
                href="#how-it-works"
                className="pressable inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-surface px-5 py-3.5 text-base font-semibold text-ink shadow-xs transition-colors hover:bg-surface-subtle hover:border-border-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
              >
                <span>How It Works</span>
                <ArrowDown size={16} className="text-muted" aria-hidden="true" />
              </a>
            </div>

            {/* Trust & Transparency Badges */}
            <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3 pt-6 border-t border-border-subtle text-xs text-muted">
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-primary flex-shrink-0" />
                <span>Zero automated cold blast spam</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-brass flex-shrink-0" />
                <span>Verified boutique stockist evidence</span>
              </div>
            </div>
          </div>

          {/* Right Column: Maker Product Exhibition Framing */}
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl border border-border bg-surface p-3 sm:p-4 shadow-elevated">
              {/* Image Container with Aspect Ratio */}
              <div className="relative overflow-hidden rounded-xl border border-border bg-surface-subtle aspect-[4/3]">
                <img
                  src={
                    imageError
                      ? "/images/craft-atelier-fallback.svg"
                      : "/images/maker-ceramic-atelier.webp"
                  }
                  onError={() => {
                    if (!imageError) {
                      setImageError(true);
                    }
                  }}
                  alt="Handcrafted fluted stoneware ceramic vessel resting on a limestone plinth in a sunlit artisan pottery studio"
                  className="size-full object-cover object-center transition-transform duration-500 hover:scale-[1.02]"
                  width={1200}
                  height={896}
                  loading="eager"
                />

                {/* Live Spec Overlay Pill */}
                <div className="absolute top-3 left-3 rounded-md bg-ink px-2.5 py-1 text-[11px] font-medium text-white shadow-xs">
                  Atelier Exhibition No. 4
                </div>

                <div className="absolute bottom-3 right-3 rounded-md bg-surface px-2.5 py-1 text-[11px] font-medium text-ink shadow-xs border border-border">
                  100% Evidence-Led
                </div>
              </div>

              {/* Inset Craft Metadata Spec Card */}
              <div data-ui className="mt-4 rounded-lg border border-border-subtle bg-surface-subtle p-4 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <span className="font-semibold text-ink">Stoneware Table Amphora</span>
                  <span className="rounded bg-brass-light border border-brass-border px-2 py-0.5 text-[11px] font-semibold text-brass">
                    Passport specification
                  </span>
                </div>
                <div className="mt-2.5 grid grid-cols-2 gap-2 text-[11px] text-muted">
                  <div>
                    <span className="block text-[11px] font-medium text-subtle">
                      Material
                    </span>
                    <span className="text-ink font-medium">Reduction-fired stoneware</span>
                  </div>
                  <div>
                    <span className="block text-[11px] font-medium text-subtle">
                      Wholesale / Retail
                    </span>
                    <span className="text-ink font-medium">$48 / $120</span>
                  </div>
                  <div>
                    <span className="block text-[11px] font-medium text-subtle">
                      Minimum order
                    </span>
                    <span className="text-ink font-medium">6 units (4 wk lead)</span>
                  </div>
                  <div>
                    <span className="block text-[11px] font-medium text-subtle">
                      Target aesthetic
                    </span>
                    <span className="text-ink font-medium">Contemporary Japanese wabi</span>
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
