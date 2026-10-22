import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Shell } from "@/components/layout/Shell";
import { LandingPage } from "@/features/landing/LandingPage";

/**
 * Backward-compatibility redirector for legacy workspace routes.
 * Preserves pathname, detail/nested IDs, and search parameters.
 */
function LegacyRedirect() {
  const location = useLocation();
  return (
    <Navigate
      to={{
        pathname: `/app${location.pathname}`,
        search: location.search,
      }}
      replace
    />
  );
}

function NotFound() {
  return (
    <div data-ui className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 py-20 text-center animate-fade-in">
      <div className="w-full rounded-2xl border border-border bg-surface p-8 shadow-card sm:p-10">
        <span className="inline-flex items-center rounded-md bg-primary-light px-2.5 py-1 text-xs font-semibold text-primary border border-primary-border">
          404 Error
        </span>
        <h1 className="mt-4 font-serif text-2xl sm:text-3xl font-normal tracking-tight text-ink">
          Page not found
        </h1>
        <p className="mx-auto mt-2.5 max-w-xs text-sm leading-relaxed text-muted">
          The requested path does not exist in the Vitrine platform.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/app"
            className="pressable inline-flex w-full sm:w-auto items-center justify-center rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Back to Dashboard
          </Link>
          <Link
            to="/"
            className="pressable inline-flex w-full sm:w-auto items-center justify-center rounded-lg border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-ink shadow-xs hover:bg-surface-subtle focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Public Home
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Public Landing Page */}
      <Route path="/" element={<LandingPage />} />

      {/* Non-shell auth routes */}
      <Route path="/login" element={<PlaceholderPage title="Sign in" />} />
      <Route
        path="/signup"
        element={<PlaceholderPage title="Create account" />}
      />

      {/* Workspace routes — wrapped in Shell (sidebar + mobile nav) */}
      <Route path="/app" element={<Shell />}>
        <Route index element={<PlaceholderPage title="Dashboard" />} />
        <Route
          path="products"
          element={<PlaceholderPage title="Product Passport" />}
        />
        <Route
          path="products/new"
          element={<PlaceholderPage title="New product" />}
        />
        <Route
          path="products/:id"
          element={<PlaceholderPage title="Product" />}
        />
        <Route
          path="discovery"
          element={<PlaceholderPage title="Market Discovery" />}
        />
        <Route
          path="discovery/:runId"
          element={<PlaceholderPage title="Research run" />}
        />
        <Route
          path="leads"
          element={<PlaceholderPage title="Buyer Leads" />}
        />
        <Route path="leads/:id" element={<PlaceholderPage title="Lead" />} />
        <Route
          path="outreach"
          element={<PlaceholderPage title="Outreach Studio" />}
        />
        <Route
          path="outreach/:leadId"
          element={<PlaceholderPage title="Outreach draft" />}
        />
      </Route>

      {/* Backward-compatible redirects for legacy workspace paths & details */}
      <Route path="/products" element={<LegacyRedirect />} />
      <Route path="/products/*" element={<LegacyRedirect />} />
      <Route path="/discovery" element={<LegacyRedirect />} />
      <Route path="/discovery/*" element={<LegacyRedirect />} />
      <Route path="/leads" element={<LegacyRedirect />} />
      <Route path="/leads/*" element={<LegacyRedirect />} />
      <Route path="/outreach" element={<LegacyRedirect />} />
      <Route path="/outreach/*" element={<LegacyRedirect />} />

      {/* Catch-all 404 route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
