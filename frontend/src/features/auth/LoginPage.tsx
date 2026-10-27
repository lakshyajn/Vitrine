import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Sparkles, ArrowRight, Mail, Lock, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "./AuthProvider";

function mapAuthError(err: Error | null): string {
  if (!err) return "";
  const msg = err.message || "";
  const lower = msg.toLowerCase();
  if (lower.includes("invalid login credentials") || lower.includes("invalid credentials")) {
    return "Invalid email or password. Please check your credentials and try again.";
  }
  if (lower.includes("email not confirmed")) {
    return "Your email address has not been confirmed. Please check your inbox for the verification email.";
  }
  if (lower.includes("rate limit") || lower.includes("too many requests")) {
    return "Too many sign-in attempts. Please wait a moment before trying again.";
  }
  if (lower.includes("network") || lower.includes("failed to fetch") || lower.includes("load failed")) {
    return "Could not reach the authentication server. Please check your internet connection and try again.";
  }
  return msg || "Sign in failed. Please try again.";
}

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { signIn, isMockMode } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  const passwordValid = password.length >= 6;
  const canSubmit = emailValid && passwordValid && !isSubmitting;

  const getDestination = () => {
    const rawNext = searchParams.get("next");
    if (
      rawNext &&
      rawNext.startsWith("/app") &&
      !rawNext.startsWith("//") &&
      !rawNext.includes("://") &&
      !rawNext.includes("\\")
    ) {
      return rawNext;
    }
    return "/app";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const { error } = await signIn(email.trim(), password);
      if (error) {
        setErrorMessage(mapAuthError(error));
      } else {
        navigate(getDestination(), { replace: true });
      }
    } catch (err: unknown) {
      setErrorMessage(mapAuthError(err instanceof Error ? err : new Error(String(err))));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoSignIn = async () => {
    setIsSubmitting(true);
    setErrorMessage("");
    try {
      const { error } = await signIn("studio@ateliersolenne.com", "demopassword");
      if (!error) {
        navigate(getDestination(), { replace: true });
      } else {
        setErrorMessage(mapAuthError(error));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-canvas px-4 py-12 sm:px-6 lg:px-8 animate-fade-in text-ink">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <Link to="/" className="inline-flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-primary">
          <img
            src="/vitrine-mark.svg"
            alt="Vitrine"
            className="size-10 transition-transform duration-300 hover:rotate-6"
          />
          <span className="font-display text-2xl font-bold tracking-tight text-ink">
            Vitrine
          </span>
        </Link>
        <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
          Sign in to your Maker Workspace
        </h1>
        <p className="text-xs text-muted">
          Access your Product Passports, Discovery runs, and verified Buyer Leads.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="rounded-2xl border border-border bg-surface p-8 shadow-elevated space-y-6">
          {errorMessage && (
            <div
              role="alert"
              aria-live="assertive"
              className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800 animate-fade-in"
            >
              <AlertCircle className="size-4 flex-shrink-0 text-red-600 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <label htmlFor="login-email" className="block text-xs font-semibold text-ink">
                Studio Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="artisan@studio.com"
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs transition-colors"
                />
              </div>
              {email.length > 0 && !emailValid && (
                <p className="text-[11px] text-red-600" aria-live="polite">
                  Please enter a valid email address.
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="login-pwd" className="block text-xs font-semibold text-ink">
                  Password
                </label>
                <Link
                  to="/reset-password"
                  className="text-[11px] font-medium text-primary hover:underline focus-visible:outline-1 focus-visible:outline-primary"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="login-pwd"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs transition-colors"
                />
              </div>
              {password.length > 0 && !passwordValid && (
                <p className="text-[11px] text-red-600" aria-live="polite">
                  Password must be at least 6 characters.
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={!canSubmit}
              data-btn-primary
              className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight className="size-4" />
                </>
              )}
            </button>
          </form>

          {/* Demonstration Notice & Action: rendered only when in mock mode */}
          {isMockMode && (
            <div className="rounded-xl border border-border bg-surface-subtle/50 p-4 text-xs text-muted space-y-2.5">
              <div className="flex items-center gap-1.5 font-semibold text-ink">
                <Sparkles className="size-3.5 text-primary" />
                <span>Demonstration Mode Active</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                Vitrine is currently running in local offline mock mode. Click below to explore the pre-seeded Atelier Solenne artisan workspace.
              </p>
              <button
                type="button"
                onClick={handleDemoSignIn}
                disabled={isSubmitting}
                className="pressable inline-flex w-full items-center justify-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-semibold text-primary transition-colors hover:bg-primary/15"
              >
                <span>Try the demo workspace</span>
                <ArrowRight className="size-3.5" />
              </button>
            </div>
          )}

          <div className="text-center text-xs text-muted">
            Don't have a workspace yet?{" "}
            <Link to="/signup" className="font-semibold text-primary hover:underline">
              Create account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
