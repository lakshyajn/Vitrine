import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Menu, X } from "lucide-react";
import { BRAND_NAME, BRAND_TAGLINE } from "@/config/brand";
import { useAuth } from "@/features/auth/AuthProvider";

/**
 * Vitrine aperture mark — unified architectural framing glyph.
 * Loaded directly from the public SVG asset so favicon and navbar cannot drift.
 */
export function VitrineMark({ className = "size-5" }: { className?: string }) {
  return (
    <img
      src="/vitrine-mark.svg"
      alt="Vitrine brand mark"
      className={className}
      width={24}
      height={24}
    />
  );
}

export function LandingNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user } = useAuth();

  return (
    <header
      className="sticky top-0 z-50 w-full border-b border-[#2A222C] bg-[#161117] text-white transition-colors"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 sm:px-8 lg:px-12">
        {/* Brand Identity */}
        <Link
          to="/"
          className="group flex items-center gap-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          aria-label={`${BRAND_NAME} home`}
        >
          <span className="grid size-9 place-items-center rounded-lg border border-white/20 bg-[#FAF8F5] shadow-xs transition-transform group-hover:scale-105">
            <VitrineMark className="size-5" />
          </span>
          <div className="flex flex-col">
            <span className="font-display text-lg font-bold tracking-tight text-white leading-none">
              {BRAND_NAME}
            </span>
            <span className="mt-1 text-[11px] font-medium text-stone-400 leading-none">
              {BRAND_TAGLINE}
            </span>
          </div>
        </Link>

        {/* Desktop Anchor Navigation */}
        <nav
          className="hidden md:flex md:items-center md:gap-8 text-sm font-medium text-stone-300"
          aria-label="Public navigation"
        >
          <a
            href="#walkthrough"
            className="transition-colors hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            Workflow &amp; Workbench
          </a>
          <a
            href="#evidence-standard"
            className="transition-colors hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            Evidence Standard
          </a>
        </nav>

        {/* Right CTA Cluster */}
        <div className="hidden sm:flex sm:items-center sm:gap-4">
          {user ? (
            <Link
              to="/app"
              data-btn-accent
              style={{ backgroundColor: "#CF1E1E", color: "#FFFFFF" }}
              className="btn-accent pressable inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-xs transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                Open workspace
              </span>
              <ArrowRight size={15} style={{ color: "#FFFFFF" }} className="text-white" aria-hidden="true" />
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-stone-300 transition-colors hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                Sign in
              </Link>
              <Link
                to="/app"
                data-btn-accent
                style={{ backgroundColor: "#CF1E1E", color: "#FFFFFF" }}
                className="btn-accent pressable inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-xs transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                  Explore workspace
                </span>
                <ArrowRight size={15} style={{ color: "#FFFFFF" }} className="text-white" aria-hidden="true" />
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="grid size-9 place-items-center rounded-lg border border-white/20 bg-white/5 text-stone-200 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white md:hidden"
          aria-expanded={mobileMenuOpen}
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          className="border-t border-[#2A222C] bg-[#161117] px-6 py-5 text-white md:hidden animate-fade-in"
          role="dialog"
          aria-label="Mobile navigation"
        >
          <nav className="mx-auto max-w-7xl flex flex-col space-y-3.5 text-sm font-medium text-stone-200">
            <a
              href="#walkthrough"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 text-stone-300 hover:text-white"
            >
              Workflow &amp; Workbench
            </a>
            <a
              href="#evidence-standard"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 text-stone-300 hover:text-white"
            >
              Evidence Standard
            </a>
            <div className="pt-3.5 border-t border-white/10 flex flex-col gap-3">
              {user ? (
                <Link
                  to="/app"
                  data-btn-accent
                  style={{ backgroundColor: "#CF1E1E", color: "#FFFFFF" }}
                  onClick={() => setMobileMenuOpen(false)}
                  className="btn-accent inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-xs"
                >
                  <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                    Open workspace
                  </span>
                  <ArrowRight size={15} style={{ color: "#FFFFFF" }} className="text-white" aria-hidden="true" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="py-2 text-center text-sm font-semibold text-stone-300 hover:text-white"
                  >
                    Sign in
                  </Link>
                  <Link
                    to="/app"
                    data-btn-accent
                    style={{ backgroundColor: "#CF1E1E", color: "#FFFFFF" }}
                    onClick={() => setMobileMenuOpen(false)}
                    className="btn-accent inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-xs"
                  >
                    <span style={{ color: "#FFFFFF" }} className="text-white font-semibold">
                      Explore workspace
                    </span>
                    <ArrowRight size={15} style={{ color: "#FFFFFF" }} className="text-white" aria-hidden="true" />
                  </Link>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}