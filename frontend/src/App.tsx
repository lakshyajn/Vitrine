import { Link, Route, Routes } from "react-router-dom";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Shell } from "@/components/layout/Shell";

function NotFound() {
  return (
    <div data-ui className="mx-auto flex max-w-md flex-col items-center justify-center px-6 py-20 text-center">
      <div className="w-full rounded-xl border border-border bg-surface p-8 shadow-card sm:p-10">
        <span className="inline-flex items-center rounded-md bg-accent-light px-2.5 py-1 text-xs font-semibold text-accent-hover">
          404 Error
        </span>
        <h1 className="mt-4 font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
          Page not found
        </h1>
        <p className="mx-auto mt-2.5 max-w-xs text-sm leading-relaxed text-muted">
          The requested path does not exist in the Vitrine workspace.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="pressable inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Non-shell routes — rendered without sidebar/nav */}
      <Route path="/login" element={<PlaceholderPage title="Sign in" />} />
      <Route
        path="/signup"
        element={<PlaceholderPage title="Create account" />}
      />

      {/* Workspace routes — wrapped in Shell (sidebar + mobile nav) */}
      <Route element={<Shell />}>
        <Route index element={<PlaceholderPage title="Dashboard" />} />
        <Route
          path="/products"
          element={<PlaceholderPage title="Product Passport" />}
        />
        <Route
          path="/products/new"
          element={<PlaceholderPage title="New product" />}
        />
        <Route
          path="/products/:id"
          element={<PlaceholderPage title="Product" />}
        />
        <Route
          path="/discovery"
          element={<PlaceholderPage title="Market Discovery" />}
        />
        <Route
          path="/discovery/:runId"
          element={<PlaceholderPage title="Research run" />}
        />
        <Route
          path="/leads"
          element={<PlaceholderPage title="Buyer Leads" />}
        />
        <Route path="/leads/:id" element={<PlaceholderPage title="Lead" />} />
        <Route
          path="/outreach"
          element={<PlaceholderPage title="Outreach Studio" />}
        />
        <Route
          path="/outreach/:leadId"
          element={<PlaceholderPage title="Outreach draft" />}
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
