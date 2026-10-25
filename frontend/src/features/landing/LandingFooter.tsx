import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { BRAND_NAME, BRAND_TAGLINE, WORKSPACE_NAME } from "@/config/brand";
import { VitrineMark } from "./LandingNav";

export function LandingFooter() {
  return (
    <footer
      className="border-t border-[#2A222C] bg-sidebar text-white"
      aria-label="Site footer"
    >
      <div className="mx-auto max-w-7xl px-6 py-14 sm:px-8 sm:py-16 lg:px-12">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-14">
          {/* Brand Column */}
          <div className="lg:col-span-5">
            <div className="flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-lg border border-white/20 bg-[#FAF8F5] shadow-xs">
                <VitrineMark className="size-5" />
              </span>
              <div className="flex flex-col">
                <span className="font-display text-xl font-bold tracking-tight text-white leading-none">
                  {BRAND_NAME}
                </span>
                <span className="mt-1 text-[11px] font-medium text-stone-400 leading-none">
                  {BRAND_TAGLINE}
                </span>
              </div>
            </div>

            <p className="mt-4 max-w-sm text-xs sm:text-sm leading-relaxed text-stone-400">
              An evidence-led wholesale intelligence workspace designed specifically for independent fashion labels, designer studios, and boutique stockists worldwide.
            </p>

            <div className="mt-5 flex items-center gap-2 text-xs text-stone-400">
              <span className="size-2 rounded-full bg-emerald-500" />
              <span>Independent Label Edition</span>
            </div>
          </div>

          {/* Links Column 1: Platform Architecture */}
          <div className="lg:col-span-3">
            <p className="text-xs font-semibold text-stone-300">
              Platform Overview
            </p>
            <ul className="mt-3.5 space-y-2 text-xs sm:text-sm text-stone-400">
              <li>
                <a href="#walkthrough" className="hover:text-white transition-colors">
                  Workflow &amp; Workbench
                </a>
              </li>
              <li>
                <a href="#evidence-standard" className="hover:text-white transition-colors">
                  Evidence Standard
                </a>
              </li>
            </ul>
          </div>

          {/* Links Column 2: Studio Workspace */}
          <div className="lg:col-span-4">
            <p className="text-xs font-semibold text-stone-300">
              {WORKSPACE_NAME}
            </p>
            <ul className="mt-3.5 space-y-2 text-xs sm:text-sm text-stone-400">
              <li>
                <Link to="/app" className="inline-flex items-center gap-1 hover:text-white transition-colors">
                  <span>Studio Dashboard</span>
                  <ArrowUpRight size={13} className="text-stone-400" />
                </Link>
              </li>
              <li>
                <Link to="/app/products" className="hover:text-white transition-colors">
                  Product Passport
                </Link>
              </li>
              <li>
                <Link to="/app/discovery" className="hover:text-white transition-colors">
                  Market Discovery
                </Link>
              </li>
              <li>
                <Link to="/app/leads" className="hover:text-white transition-colors">
                  Buyer Leads
                </Link>
              </li>
              <li>
                <Link to="/app/outreach" className="hover:text-white transition-colors">
                  Outreach Studio
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-6 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-stone-400">
          <p>© {new Date().getFullYear()} Vitrine. Evidence-backed boutique discovery.</p>
          <div className="flex items-center gap-6">
            <Link to="/login" className="hover:text-white transition-colors">
              Sign in
            </Link>
            <Link to="/signup" className="hover:text-white transition-colors">
              Create account
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
