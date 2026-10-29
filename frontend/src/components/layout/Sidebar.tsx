import { Link, NavLink } from "react-router-dom";
import { LogOut } from "lucide-react";
import { BRAND_NAME, BRAND_TAGLINE } from "@/config/brand";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav-items";
import { useAuth } from "@/features/auth/AuthProvider";
import { useProfile } from "@/api/profile";


/**
 * Architectural Vitrine showcase aperture glyph.
 * Represents precision framing and exhibition for independent craft makers.
 */
function VitrineMark({ className }: { className?: string }) {
  return (
    <img
      src="/vitrine-mark.svg"
      alt="Vitrine mark"
      className={className}
      width={24}
      height={24}
      aria-hidden="true"
    />
  );
}

export function Sidebar() {
  const { user, signOut } = useAuth();
  const { data: profile } = useProfile(!!user);

  const businessName =
    profile?.business_name ||
    (user?.user_metadata?.studio_name as string) ||
    "Studio Workspace";
  const userEmail = user?.email || "";

  return (
    <aside
      data-ui
      className="flex h-dvh w-64 flex-shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-text"
      aria-label="Workspace navigation"
    >
      {/* Brand Header */}
      <Link
        to="/app"
        className="flex h-16 flex-shrink-0 items-center justify-between border-b border-sidebar-border px-5 focus-visible:outline-2 focus-visible:outline-primary"
      >
        <div className="flex items-center gap-3">
          <span
            className="grid size-8 place-items-center rounded-lg bg-[#FAF8F5] border border-white/20 shadow-xs"
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
      </Link>

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

      {/* Workspace Footer Profile with Signed-in Maker Details & Sign Out */}
      <div className="flex-shrink-0 border-t border-sidebar-border p-3.5">
        <div className="rounded-lg bg-sidebar-surface/60 border border-sidebar-border/70 p-3 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-xs font-semibold text-white">
                  {businessName}
                </span>
              </div>
              {userEmail && (
                <p className="truncate text-[11px] text-sidebar-muted" title={userEmail}>
                  {userEmail}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => void signOut()}
              title="Sign out of workspace"
              aria-label="Sign out"
              className="pressable grid size-7 flex-shrink-0 place-items-center rounded-md text-sidebar-muted hover:text-white hover:bg-sidebar-hover transition-colors focus-visible:outline-2 focus-visible:outline-accent"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}