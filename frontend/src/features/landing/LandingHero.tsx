import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import { BRAND_HEADLINE, BRAND_SUBHEAD } from "@/config/brand";

interface TiltState {
  rotateX: number;
  rotateY: number;
  translateX: number;
  translateY: number;
}

export function LandingHero() {
  const [imageError, setImageError] = useState(false);
  const [tilt, setTilt] = useState<TiltState>({
    rotateX: 0,
    rotateY: 0,
    translateX: 0,
    translateY: 0,
  });
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (reducedMotion) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5; // -0.5 to 0.5

    // Modestly increased rigid 3D tilt (~25% increase: max ±4.2 deg rotation, 5px translation)
    setTilt({
      rotateX: -y * 4.2,
      rotateY: x * 4.2,
      translateX: x * 5,
      translateY: y * 5,
    });
  };

  const handlePointerLeave = () => {
    setTilt({ rotateX: 0, rotateY: 0, translateX: 0, translateY: 0 });
  };

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative overflow-hidden bg-sidebar text-white border-b border-[#2A222C] px-6 pt-6 pb-16 sm:px-8 sm:pt-10 sm:pb-20 lg:px-12"
    >
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
                data-btn-accent
                style={{ backgroundColor: "#CF1E1E", color: "#FFFFFF" }}
                className="btn-accent pressable inline-flex items-center justify-center gap-2.5 rounded-lg px-6 py-3.5 text-sm sm:text-base font-semibold text-white shadow-xs transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                  Explore the workspace
                </span>
                <ArrowRight size={17} style={{ color: "#FFFFFF" }} className="text-white" aria-hidden="true" />
              </Link>
              <a
                href="#walkthrough"
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
                <span>Evidence-backed boutique discovery</span>
              </div>
            </div>
          </div>

          {/* Right Column: Multi-Image Fashion Collection Composition */}
          <div className="relative lg:col-span-5 [perspective:1200px]">
            <div
              onPointerMove={handlePointerMove}
              onPointerLeave={handlePointerLeave}
              style={{
                transform: reducedMotion
                  ? "none"
                  : `rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg) translate3d(${tilt.translateX}px, ${tilt.translateY}px, 6px)`,
                transformStyle: "preserve-3d",
                transition:
                  tilt.rotateX === 0
                    ? "transform 500ms cubic-bezier(0.16, 1, 0.3, 1)"
                    : "transform 100ms ease-out",
                willChange: "transform",
              }}
              className="relative rounded-2xl border border-white/15 bg-white/5 p-2 sm:p-2.5 shadow-elevated transition-colors duration-300 hover:border-white/30"
            >
              {/* Primary Collection Atelier Frame */}
              <div className="relative overflow-hidden rounded-xl border border-white/10 bg-black/40 aspect-[16/10]">
                <img
                  src={
                    imageError
                      ? "/images/fashion-atelier-fallback.svg"
                      : "/images/vitrine-boutique-collection.webp"
                  }
                  onError={() => {
                    if (!imageError) {
                      setImageError(true);
                    }
                  }}
                  alt="Curated independent fashion collection with diverse tailored coats, knitwear, and trousers on a steel rail in a boutique showroom"
                  className="size-full object-cover object-center"
                  width={1376}
                  height={768}
                  loading="eager"
                />

                {/* Collection Meta Badge */}
                <div className="absolute top-3 left-3 rounded-md bg-black/90 px-2.5 py-1 text-[11px] font-medium tracking-wide text-white border border-white/15">
                  Curated Collection · Atelier Autumn/Winter
                </div>

                {/* Bottom Evidence Note */}
                <div className="absolute bottom-3 inset-x-3 flex items-center justify-between text-[11px] text-stone-200">
                  <span className="font-medium bg-black/85 px-2.5 py-1 rounded border border-white/10">
                    Boutique wholesale line-sheet
                  </span>
                  <span className="rounded bg-white/95 px-2.5 py-1 font-semibold text-[#161117]">
                    Evidence-Backed Match
                  </span>
                </div>
              </div>

              {/* Complementary Detail Collage Row: Fabric & Silhouette */}
              <div className="mt-2.5 grid grid-cols-2 gap-2 text-xs text-stone-300">
                {/* Detail 1: Fabric Weave & Trim */}
                <div className="flex items-center gap-2.5 rounded-lg border border-white/10 bg-black/40 p-2">
                  <div className="size-11 overflow-hidden rounded border border-white/15 flex-shrink-0">
                    <img
                      src="/images/fashion-detail-textile.webp"
                      alt="Artisanal Belgian linen weave and natural horn button detail"
                      className="size-full object-cover"
                      width={400}
                      height={400}
                      loading="lazy"
                    />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-white leading-tight truncate">
                      340gsm Flax Linen
                    </p>
                    <p className="text-[10px] text-stone-400 mt-0.5 leading-tight">
                      Horn trims &amp; French seams
                    </p>
                  </div>
                </div>

                {/* Detail 2: Garment Silhouette & Cut */}
                <div className="flex items-center gap-2.5 rounded-lg border border-white/10 bg-black/40 p-2">
                  <div className="size-11 overflow-hidden rounded border border-white/15 flex-shrink-0">
                    <img
                      src="/images/fashion-detail-silhouette.webp"
                      alt="Relaxed architectural garment drape and tailoring silhouette"
                      className="size-full object-cover"
                      width={400}
                      height={400}
                      loading="lazy"
                    />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-white leading-tight truncate">
                      Relaxed Tailoring
                    </p>
                    <p className="text-[10px] text-stone-400 mt-0.5 leading-tight">
                      Unisex collection silhouette
                    </p>
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
