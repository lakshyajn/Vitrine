import React from "react";
import { Navigate, Outlet, useLocation, useSearchParams } from "react-router-dom";
import { useAuth } from "./AuthProvider";

function AuthLoadingSkeleton() {
  return (
    <div
      data-ui
      data-testid="auth-loading-skeleton"
      className="flex min-h-screen flex-col items-center justify-center bg-canvas px-4"
    >
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-card space-y-4 animate-pulse">
        <div className="flex items-center justify-center gap-3">
          <div className="size-8 rounded-lg bg-border-subtle" />
          <div className="h-5 w-24 rounded bg-border-subtle" />
        </div>
        <div className="mx-auto h-3 w-40 rounded bg-border-subtle" />
        <div className="mt-6 space-y-2.5">
          <div className="h-9 w-full rounded-xl bg-border-subtle" />
          <div className="h-9 w-full rounded-xl bg-border-subtle" />
        </div>
      </div>
    </div>
  );
}

export function RequireAuth({ children }: { children?: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  if (!user) {
    const nextPath = location.pathname + location.search;
    const next = encodeURIComponent(nextPath);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}

export function RedirectIfAuthenticated({ children }: { children?: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const [searchParams] = useSearchParams();

  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  if (user) {
    const rawNext = searchParams.get("next");
    // Strict open-redirect guard: allow only same-origin relative paths starting with /app
    const isValidNext =
      Boolean(rawNext) &&
      rawNext!.startsWith("/app") &&
      !rawNext!.startsWith("//") &&
      !rawNext!.includes("://") &&
      !rawNext!.includes("\\");

    const destination = isValidNext ? rawNext! : "/app";
    return <Navigate to={destination} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
