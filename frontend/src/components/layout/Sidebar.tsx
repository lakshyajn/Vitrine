import { NavLink } from "react-router-dom";
import { BRAND_NAME, BRAND_TAGLINE } from "@/config/brand";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav-items";

/**
 * Architectural Vitrine showcase aperture glyph.
 * Represents precision framing and exhibition for independent craft makers.
 */
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

export function Sidebar() {
  return (
    <aside
      data-ui
      className="flex h-dvh w-64 flex-shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-text"
      aria-label="Workspace navigation"
    >
      {/* Brand Header */}
      <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-sidebar-border px-5">
        <div className="flex items-center gap-3">
          <span
            className="grid size-8 place-items-center rounded-lg bg-accent/15 text-accent border border-accent/25 shadow-xs"
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
        </div>
      </div>

      {/* Primary Navigation */}
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
                      {/* Active indicator bar */}
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

      {/* Workspace Footer Profile */}
      <div className="flex-shrink-0 border-t border-sidebar-border p-4">
        <div className="rounded-lg bg-sidebar-surface/60 border border-sidebar-border/70 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">
              Studio Workspace
            </span>
            <span className="flex size-2 rounded-full bg-emerald-500" aria-label="System operational" />
          </div>
          <p className="mt-1 text-[11px] text-sidebar-muted">
            Independent Maker Edition
          </p>
        </div>
      </div>
    </aside>
  );
}
