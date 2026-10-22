import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { BRAND_NAME, BRAND_TAGLINE, WORKSPACE_NAME } from "@/config/brand";
import { VitrineMark } from "./LandingNav";

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-ink text-white" aria-label="Site footer">
      <div className="mx-auto max-w-7xl px-6 py-16 sm:px-8 sm:py-20 lg:px-12">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:gap-16">
          {/* Brand Info */}
          <div className="lg:col-span-5">
            <div className="flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-md border border-stone-800 bg-stone-900 text-stone-200">
                <VitrineMark className="size-5" />
              </span>
              <div className="flex flex-col">
                <span className="font-serif text-xl font-semibold tracking-tight text-white leading-none">
                  {BRAND_NAME}
                </span>
                <span className="mt-1 text-[11px] font-medium text-stone-400 leading-none">
                  {BRAND_TAGLINE}
                </span>
              </div>
            </div>

            <p className="mt-5 max-w-sm text-xs sm:text-sm leading-relaxed text-stone-400">
              An evidence-led wholesale intelligence workspace designed specifically for independent makers, craft studios, and discerning boutique stockists worldwide.
            </p>

            <div className="mt-6 flex items-center gap-2 text-xs text-stone-400">
              <span className="size-2 rounded-full bg-emerald-500" />
              <span>Independent Maker Edition · WS1 Standard</span>
            </div>
          </div>

          {/* Links Column 1: Public Exploration */}
          <div className="lg:col-span-2">
            <p className="text-xs font-semibold text-stone-300">
              Architecture
            </p>
            <ul className="mt-4 space-y-2.5 text-xs sm:text-sm text-stone-400">
              <li>
                <a href="#how-it-works" className="hover:text-white transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#evidence-philosophy" className="hover:text-white transition-colors">
                  Data-Truth Philosophy
                </a>
              </li>
              <li>
                <a href="#preview" className="hover:text-white transition-colors">
                  Interactive Preview
                </a>
              </li>
            </ul>
          </div>

          {/* Links Column 2: Studio Workspace */}
          <div className="lg:col-span-3">
            <p className="text-xs font-semibold text-stone-300">
              {WORKSPACE_NAME}
            </p>
            <ul className="mt-4 space-y-2.5 text-xs sm:text-sm text-stone-400">
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

          {/* Links Column 3: Access */}
          <div className="lg:col-span-2">
            <p className="text-xs font-semibold text-stone-300">
              Access
            </p>
            <ul className="mt-4 space-y-2.5 text-xs sm:text-sm text-stone-400">
              <li>
                <Link to="/login" className="hover:text-white transition-colors">
                  Sign in
                </Link>
              </li>
              <li>
                <Link to="/signup" className="hover:text-white transition-colors">
                  Create account
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-stone-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-stone-400">
          <p>© {new Date().getFullYear()} {BRAND_NAME}. Dedicated to craft provenance and honest commerce.</p>
          <p className="text-[11px] text-stone-400">
            No payment gateways · Zero email blast spam · Strict epistemic truth
          </p>
        </div>
      </div>
    </footer>
  );
}
