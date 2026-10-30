import { Outlet, useLocation } from "react-router-dom";
import { MobileNav } from "./MobileNav";
import { Sidebar } from "./Sidebar";
import { NAV_ITEMS } from "./nav-items";
import { OnboardingModal } from "@/features/auth/OnboardingModal";

export function Shell() {
  const location = useLocation();
  const currentNav = NAV_ITEMS.find((item) =>
    item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path)
  );

  return (
    <div
      data-ui
      className="flex h-dvh overflow-hidden bg-canvas text-ink selection:bg-accent-light selection:text-ink"
    >
      {/* First-run studio onboarding modal */}
      <OnboardingModal />

      {/* Desktop sidebar: hidden below lg breakpoint */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <Sidebar />
      </div>

      {/* Main column: mobile nav + top bar + page canvas */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Mobile top bar: visible below lg */}
        <div className="lg:hidden">
          <MobileNav />
        </div>

        {/* Skip link for keyboard accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:border focus:border-border focus:bg-surface focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-ink focus:shadow-elevated focus:outline-none focus:ring-2 focus:ring-accent"
        >
          Skip to main content
        </a>

        {/* Desktop Top Bar Context */}
        <header
          data-ui
          className="hidden lg:flex h-16 flex-shrink-0 items-center justify-between border-b border-border bg-surface px-8"
        >
          {/* Breadcrumb Trail */}
          <nav aria-label="Breadcrumb">
            <ol className="flex items-center gap-2 text-xs font-medium text-muted">
              <li>
                <span>Vitrine</span>
              </li>
              <li className="text-border-strong" aria-hidden="true">
                /
              </li>
              <li>
                <span aria-current="page" className="font-semibold text-ink">
                  {currentNav?.label || "Workspace"}
                </span>
              </li>
            </ol>
          </nav>

          {/* Right Status Affordance */}
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-canvas px-3 py-1 text-xs font-medium text-muted">
              <span className="size-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
              <span>Evidence-led mode</span>
            </span>
          </div>
        </header>

        {/* Page canvas */}
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto focus:outline-none"
        >
          <div className="animate-page-enter min-h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
