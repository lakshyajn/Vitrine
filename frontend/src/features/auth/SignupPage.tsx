import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight, Mail, Lock, Building, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "./AuthProvider";
import { updateProfile } from "@/api/profile";

function mapSignupError(err: Error | null): string {
  if (!err) return "";
  const msg = err.message || "";
  const lower = msg.toLowerCase();
  if (lower.includes("already registered") || lower.includes("already exists")) {
    return "An account with this email address already exists. Please sign in instead.";
  }
  if (lower.includes("password should be at least")) {
    return "Password must be at least 6 characters long.";
  }
  if (lower.includes("rate limit") || lower.includes("too many requests")) {
    return "Too many sign-up attempts. Please wait a moment before trying again.";
  }
  if (lower.includes("network") || lower.includes("failed to fetch") || lower.includes("load failed")) {
    return "Could not reach the authentication server. Please check your internet connection and try again.";
  }
  return msg || "Sign up failed. Please check your details and try again.";
}

export function SignupPage() {
  const navigate = useNavigate();
  const { signUp, signIn, resendConfirmation, isMockMode } = useAuth();

  const [studioName, setStudioName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // Confirmation email state
  const [emailConfirmationRequired, setEmailConfirmationRequired] = useState(false);
  const [resendStatus, setResendStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [resendMessage, setResendMessage] = useState("");

  const studioNameValid = studioName.trim().length >= 2 && studioName.trim().length <= 80;
  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  const passwordValid = password.length >= 6;
  const canSubmit = studioNameValid && emailValid && passwordValid && !isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const trimmedStudio = studioName.trim();
      const trimmedEmail = email.trim();

      const { data_or_session, error } = await (async () => {
        const res = await signUp({
          email: trimmedEmail,
          password,
          studioName: trimmedStudio,
        });
        return { data_or_session: res.session, error: res.error };
      })();

      if (error) {
        setErrorMessage(mapSignupError(error));
        setIsSubmitting(false);
        return;
      }

      // If Supabase returned an active session immediately (auto-confirm enabled or mock mode)
      if (data_or_session) {
        try {
          await updateProfile({ business_name: trimmedStudio });
        } catch {
          // Non-blocking: profile will be verified or completed during onboarding
        }
        navigate("/app", { replace: true });
        return;
      }

      // If no session returned, email confirmation is enabled on Supabase
      setEmailConfirmationRequired(true);
    } catch (err: unknown) {
      setErrorMessage(mapSignupError(err instanceof Error ? err : new Error(String(err))));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (resendStatus === "sending") return;
    setResendStatus("sending");
    setResendMessage("");
    try {
      const { error } = await resendConfirmation(email.trim());
      if (error) {
        setResendStatus("error");
        setResendMessage(mapSignupError(error));
      } else {
        setResendStatus("sent");
        setResendMessage("A new verification link has been sent to your email.");
      }
    } catch {
      setResendStatus("error");
      setResendMessage("Failed to resend confirmation email. Please try again.");
    }
  };

  const handleDemoSignIn = async () => {
    setIsSubmitting(true);
    setErrorMessage("");
    try {
      const { error } = await signIn("studio@ateliersolenne.com", "demopassword");
      if (!error) {
        navigate("/app", { replace: true });
      } else {
        setErrorMessage(mapSignupError(error));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render "Check your email" confirmation screen if email confirmation is required
  if (emailConfirmationRequired) {
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
          <div className="mx-auto grid size-12 place-items-center rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
            <Mail className="size-6" />
          </div>
          <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
            Check your studio email
          </h1>
          <p className="text-xs text-muted leading-relaxed">
            We sent a verification link to <strong className="text-ink font-semibold">{email}</strong>.
            Click the link in the message to activate your maker workspace.
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="rounded-2xl border border-border bg-surface p-8 shadow-elevated space-y-6 text-center">
            {resendMessage && (
              <div
                role="status"
                aria-live="polite"
                className={`flex items-start gap-2.5 rounded-xl border p-3.5 text-xs text-left ${
                  resendStatus === "error"
                    ? "border-red-200 bg-red-50 text-red-800"
                    : "border-emerald-200 bg-emerald-50 text-emerald-800"
                }`}
              >
                {resendStatus === "error" ? (
                  <AlertCircle className="size-4 flex-shrink-0 text-red-600 mt-0.5" />
                ) : (
                  <CheckCircle className="size-4 flex-shrink-0 text-emerald-600 mt-0.5" />
                )}
                <span>{resendMessage}</span>
              </div>
            )}

            <div className="space-y-3">
              <button
                type="button"
                onClick={handleResendConfirmation}
                disabled={resendStatus === "sending"}
                data-btn-primary
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2"
              >
                {resendStatus === "sending" ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    <span>Resending email...</span>
                  </>
                ) : (
                  <span>Resend verification email</span>
                )}
              </button>

              <Link
                to="/login"
                className="inline-flex w-full items-center justify-center rounded-xl border border-border bg-canvas py-2.5 text-xs sm:text-sm font-semibold text-ink shadow-xs hover:bg-surface-subtle transition-colors"
              >
                Return to sign in
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
          Create account for your Maker Studio
        </h1>
        <p className="text-xs text-muted">
          Start discovering high-alignment independent retail stockists worldwide.
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
              <label htmlFor="signup-studio" className="block text-xs font-semibold text-ink">
                Studio or Brand Name
              </label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="signup-studio"
                  type="text"
                  autoComplete="organization"
                  required
                  value={studioName}
                  onChange={(e) => setStudioName(e.target.value)}
                  placeholder="e.g. Atelier Solenne"
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs transition-colors"
                />
              </div>
              {studioName.length > 0 && !studioNameValid && (
                <p className="text-[11px] text-red-600" aria-live="polite">
                  Studio name must be between 2 and 80 characters.
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <label htmlFor="signup-email" className="block text-xs font-semibold text-ink">
                Studio Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="signup-email"
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
              <label htmlFor="signup-pwd" className="block text-xs font-semibold text-ink">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                <input
                  id="signup-pwd"
                  type="password"
                  autoComplete="new-password"
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
                  <span>Creating Studio...</span>
                </>
              ) : (
                <>
                  <span>Create Account &amp; Start</span>
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
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}