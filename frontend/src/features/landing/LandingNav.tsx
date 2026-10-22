import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Menu, X } from "lucide-react";
import { BRAND_NAME, BRAND_TAGLINE } from "@/config/brand";

/**
 * Vitrine aperture mark — architectural framing and exhibition glyph.
 */
export function VitrineMark({ className = "size-5" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <rect
        x="3"
        y="3"
        width="18"
        height="18"
        rx="2"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path
        d="M3 9H21"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeOpacity="0.4"
      />
      <rect
        x="7"
        y="12"
        width="10"
        height="6"
        rx="1"
        fill="currentColor"
        fillOpacity="0.25"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  );
}

export function LandingNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-canvas/95 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 sm:px-8 lg:px-12">
        {/* Brand Identity */}
        <Link
          to="/"
          className="group flex items-center gap-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          aria-label={`${BRAND_NAME} home`}
        >
          <span className="grid size-9 place-items-center rounded-md border border-border bg-surface text-primary shadow-xs transition-colors group-hover:border-primary/40 group-hover:text-primary-hover">
            <VitrineMark className="size-5" />
          </span>
          <div className="flex flex-col">
            <span className="font-serif text-xl font-semibold tracking-tight text-ink leading-none">
              {BRAND_NAME}
            </span>
            <span className="mt-1 text-[11px] font-medium text-muted leading-none">
              {BRAND_TAGLINE}
            </span>
          </div>
        </Link>

        {/* Desktop Anchor Navigation */}
        <nav
          className="hidden md:flex md:items-center md:gap-8 text-sm font-medium text-muted"
          aria-label="Public navigation"
        >
          <a
            href="#how-it-works"
            className="transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            How It Works
          </a>
          <a
            href="#evidence-philosophy"
            className="transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Evidence Philosophy
          </a>
          <a
            href="#preview"
            className="transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Interactive Preview
          </a>
        </nav>

        {/* Right CTA Cluster */}
        <div className="hidden sm:flex sm:items-center sm:gap-4">
          <Link
            to="/login"
            className="text-sm font-medium text-muted transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Sign in
          </Link>
          <Link
            to="/app"
            className="pressable inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-xs transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            <span>Open Workspace</span>
            <ArrowRight size={15} aria-hidden="true" />
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="grid size-10 place-items-center rounded-lg border border-border bg-surface text-ink transition-colors hover:bg-surface-subtle focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary md:hidden"
          aria-expanded={mobileMenuOpen}
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          className="border-b border-border bg-surface px-6 py-6 md:hidden animate-fade-in shadow-elevated"
          role="dialog"
          aria-label="Mobile navigation"
        >
          <nav className="flex flex-col space-y-4 text-base font-medium text-ink">
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 text-muted hover:text-ink"
            >
              How It Works
            </a>
            <a
              href="#evidence-philosophy"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 text-muted hover:text-ink"
            >
              Evidence Philosophy
            </a>
            <a
              href="#preview"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 text-muted hover:text-ink"
            >
              Interactive Preview
            </a>
            <div className="pt-4 border-t border-border flex flex-col gap-3">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-center text-sm font-semibold text-muted hover:text-ink"
              >
                Sign in
              </Link>
              <Link
                to="/app"
                onClick={() => setMobileMenuOpen(false)}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-primary-hover"
              >
                <span>Open Workspace</span>
                <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}

