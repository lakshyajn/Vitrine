import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { BRAND_NAME, BRAND_TAGLINE } from "@/config/brand";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav-items";

function VitrineMark({ className }: { className?: string }) {
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
        rx="3"
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
        rx="1.5"
        fill="currentColor"
        fillOpacity="0.2"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  );
}

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  // Close drawer on route change
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  // Close drawer on Escape key
  useEffect(() => {
    if (!open) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <>
      {/* Top Header Bar */}
      <header
        data-ui
        className="flex h-16 flex-shrink-0 items-center justify-between border-b border-sidebar-border bg-sidebar px-4 text-white"
      >
        <Link to="/app" className="flex items-center gap-3">
          <span
            className="grid size-8 place-items-center rounded-lg bg-accent/15 text-accent border border-accent/25"
            aria-hidden="true"
          >
            <VitrineMark className="size-5" />
          </span>
          <div className="flex flex-col">
            <span className="font-display text-base font-bold tracking-tight text-white leading-none">
              {BRAND_NAME}
            </span>
            <span className="mt-1 text-[11px] font-medium text-sidebar-muted leading-none">
              {BRAND_TAGLINE}
            </span>
          </div>
        </Link>

        {/* Hamburger Toggle Button */}
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="pressable grid size-10 place-items-center rounded-lg text-sidebar-label hover:bg-white/10 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
        >
          {open ? (
            <X size={20} strokeWidth={2} />
          ) : (
            <Menu size={20} strokeWidth={2} />
          )}
        </button>
      </header>

      {/* Backdrop scrim */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-slate-950/70 transition-opacity duration-200 ease-out",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        aria-hidden="true"
        onClick={() => setOpen(false)}
      />

      {/* Slide-in drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
        data-ui
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-sidebar-border bg-sidebar text-white shadow-drawer",
          "transition-transform duration-200 ease-out",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Drawer header */}
        <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-sidebar-border px-4">
          <div className="flex items-center gap-3">
            <span
              className="grid size-8 place-items-center rounded-lg bg-accent/15 text-accent border border-accent/25"
              aria-hidden="true"
            >
              <VitrineMark className="size-5" />
            </span>
            <span className="font-display text-base font-bold tracking-tight text-white">
              {BRAND_NAME}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="pressable grid size-9 place-items-center rounded-lg text-sidebar-muted hover:bg-white/10 hover:text-white"
            aria-label="Close navigation"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        {/* Navigation links */}
        <nav
          className="flex-1 overflow-y-auto px-3 py-4"
          aria-label="Primary"
        >
          <div className="mb-2.5 px-3 text-[11px] font-medium text-sidebar-muted">
            Workspace
          </div>
          <ul role="list" className="space-y-1.5">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    end={item.exact}
                    className={({ isActive }) =>
                      cn(
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150 ease-out",
                        isActive
                          ? "bg-sidebar-active text-white shadow-xs font-semibold"
                          : "text-sidebar-label hover:bg-sidebar-hover hover:text-white",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span
                            className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-accent"
                            aria-hidden="true"
                          />
                        )}
                        <Icon
                          size={17}
                          strokeWidth={isActive ? 2.2 : 1.8}
                          className={cn(
                            "flex-shrink-0 transition-colors duration-150",
                            isActive
                              ? "text-accent"
                              : "text-sidebar-muted group-hover:text-white",
                          )}
                          aria-hidden="true"
                        />
                        <span className="truncate">{item.label}</span>
                      </>
                    )}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer info */}
        <div className="flex-shrink-0 border-t border-sidebar-border p-4">
          <p className="text-xs font-semibold text-white">
            Studio Workspace
          </p>
          <p className="mt-0.5 text-[11px] text-sidebar-muted">
            Independent Maker Edition
          </p>
        </div>
      </div>
    </>
  );
}
