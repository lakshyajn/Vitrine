import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { LandingPage } from "@/features/landing/LandingPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { SignupPage } from "@/features/auth/SignupPage";
import { ResetPasswordPage } from "@/features/auth/ResetPasswordPage";
import { RequireAuth, RedirectIfAuthenticated } from "@/features/auth/AuthGuards";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { ProductListPage } from "@/features/products/ProductListPage";
import { ProductFormPage } from "@/features/products/ProductFormPage";
import { DiscoveryListPage } from "@/features/discovery/DiscoveryListPage";
import { RunDetailPage } from "@/features/discovery/RunDetailPage";
import { LeadsListPage } from "@/features/leads/LeadsListPage";
import { LeadDetailPage } from "@/features/leads/LeadDetailPage";
import { OutreachListPage } from "@/features/outreach/OutreachListPage";
import { OutreachWorkspacePage } from "@/features/outreach/OutreachWorkspacePage";
import { InsightsPage } from "@/features/insights/InsightsPage";

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
        <h1 className="mt-4 font-display text-2xl sm:text-3xl font-bold tracking-tight text-ink">
          Page not found
        </h1>
        <p className="mx-auto mt-2.5 max-w-xs text-sm leading-relaxed text-muted">
          The requested path does not exist in the Vitrine platform.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/app"
            data-btn-primary
            className="pressable inline-flex w-full sm:w-auto items-center justify-center rounded-lg px-4 py-2.5 text-sm font-semibold text-white shadow-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            <span>Back to Dashboard</span>
          </Link>
          <Link
            to="/"
            className="pressable inline-flex w-full sm:w-auto items-center justify-center rounded-lg border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-ink shadow-xs hover:bg-surface-subtle focus-visible:outline-2 focus-visible:outline-offset-2"
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

      {/* Non-shell auth routes (redirect to /app if already signed in) */}
      <Route
        path="/login"
        element={
          <RedirectIfAuthenticated>
            <LoginPage />
          </RedirectIfAuthenticated>
        }
      />
      <Route
        path="/signup"
        element={
          <RedirectIfAuthenticated>
            <SignupPage />
          </RedirectIfAuthenticated>
        }
      />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      {/* Workspace routes — guarded by RequireAuth, wrapped in Shell */}
      <Route
        path="/app"
        element={
          <RequireAuth>
            <Shell />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="products" element={<ProductListPage />} />
        <Route path="products/new" element={<ProductFormPage />} />
        <Route path="products/:id" element={<ProductFormPage />} />
        <Route path="products/:id/edit" element={<ProductFormPage />} />
        <Route path="discovery" element={<DiscoveryListPage />} />
        <Route path="discovery/:runId" element={<RunDetailPage />} />
        <Route path="discovery/runs/:runId" element={<RunDetailPage />} />
        <Route path="leads" element={<LeadsListPage />} />
        <Route path="leads/:id" element={<LeadDetailPage />} />
        <Route path="outreach" element={<OutreachListPage />} />
        <Route path="outreach/:leadId" element={<OutreachWorkspacePage />} />
        <Route path="outreach/drafts/:leadId" element={<OutreachWorkspacePage />} />
        <Route path="insights" element={<InsightsPage />} />
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
      <Route path="/insights" element={<LegacyRedirect />} />
      <Route path="/insights/*" element={<LegacyRedirect />} />

      {/* Catch-all 404 route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
