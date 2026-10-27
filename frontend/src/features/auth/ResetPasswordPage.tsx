import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Lock, Mail, ArrowRight, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { useAuth } from "./AuthProvider";
import { supabase } from "@/lib/supabase";

function mapResetError(err: Error | null): string {
  if (!err) return "";
  const msg = err.message || "";
  const lower = msg.toLowerCase();
  if (lower.includes("rate limit") || lower.includes("too many requests")) {
    return "Too many requests. Please wait a few moments before trying again.";
  }
  if (lower.includes("network") || lower.includes("failed to fetch") || lower.includes("load failed")) {
    return "Could not reach the server. Please check your network connection.";
  }
  return msg || "Failed to process request. Please try again.";
}

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const { resetPassword, isMockMode } = useAuth();

  // Mode: "request" (send email) or "update" (enter new password)
  const [isUpdateMode, setIsUpdateMode] = useState(false);

  // Request form state
  const [email, setEmail] = useState("");
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [requestSent, setRequestSent] = useState(false);
  const [requestError, setRequestError] = useState("");

  // Update password state
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmittingUpdate, setIsSubmittingUpdate] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [updateError, setUpdateError] = useState("");

  // Check URL hash for Supabase recovery token on mount
  useEffect(() => {
    const hash = window.location.hash;
    if (hash && (hash.includes("type=recovery") || hash.includes("access_token="))) {
      setIsUpdateMode(true);
    }

    if (!supabase || isMockMode) return;

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") {
        setIsUpdateMode(true);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [isMockMode]);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  const canSubmitRequest = emailValid && !isSubmittingRequest;

  const passwordValid = newPassword.length >= 6;
  const passwordsMatch = newPassword === confirmPassword;
  const canSubmitUpdate = passwordValid && passwordsMatch && !isSubmittingUpdate;

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmitRequest) return;

    setIsSubmittingRequest(true);
    setRequestError("");

    try {
      const { error } = await resetPassword(email.trim());
      if (error) {
        setRequestError(mapResetError(error));
      } else {
        setRequestSent(true);
      }
    } catch (err: unknown) {
      setRequestError(mapResetError(err instanceof Error ? err : new Error(String(err))));
    } finally {
      setIsSubmittingRequest(false);
    }
  };

  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmitUpdate) return;

    setIsSubmittingUpdate(true);
    setUpdateError("");

    try {
      if (isMockMode) {
        setUpdateSuccess(true);
        setTimeout(() => navigate("/login", { replace: true }), 1500);
        return;
      }

      if (!supabase) {
        throw new Error("Authentication client is not configured");
      }

      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) {
        setUpdateError(mapResetError(error));
      } else {
        setUpdateSuccess(true);
        setTimeout(() => navigate("/app", { replace: true }), 1500);
      }
    } catch (err: unknown) {
      setUpdateError(mapResetError(err instanceof Error ? err : new Error(String(err))));
    } finally {
      setIsSubmittingUpdate(false);
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
          {isUpdateMode ? "Set new password" : "Reset your password"}
        </h1>
        <p className="text-xs text-muted">
          {isUpdateMode
            ? "Choose a strong password for your studio account."
            : "Enter your registered email address to receive a recovery link."}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="rounded-2xl border border-border bg-surface p-8 shadow-elevated space-y-6">
          {/* Recovery Form: Update Password */}
          {isUpdateMode ? (
            <div>
              {updateSuccess ? (
                <div
                  role="status"
                  aria-live="polite"
                  className="flex flex-col items-center justify-center p-4 text-center space-y-3"
                >
                  <div className="grid size-12 place-items-center rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                    <CheckCircle className="size-6" />
                  </div>
                  <h2 className="font-display text-base font-semibold text-ink">
                    Password updated successfully!
                  </h2>
                  <p className="text-xs text-muted">
                    Redirecting you to your studio workspace...
                  </p>
                </div>
              ) : (
                <form onSubmit={handleUpdateSubmit} className="space-y-4" noValidate>
                  {updateError && (
                    <div
                      role="alert"
                      aria-live="assertive"
                      className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800"
                    >
                      <AlertCircle className="size-4 flex-shrink-0 text-red-600 mt-0.5" />
                      <span>{updateError}</span>
                    </div>
                  )}

                  <div className="space-y-1.5">
                    <label htmlFor="new-password" className="block text-xs font-semibold text-ink">
                      New Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                      <input
                        id="new-password"
                        type="password"
                        autoComplete="new-password"
                        required
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs transition-colors"
                      />
                    </div>
                    {newPassword.length > 0 && !passwordValid && (
                      <p className="text-[11px] text-red-600" aria-live="polite">
                        Password must be at least 6 characters.
                      </p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <label htmlFor="confirm-password" className="block text-xs font-semibold text-ink">
                      Confirm New Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                      <input
                        id="confirm-password"
                        type="password"
                        autoComplete="new-password"
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted/60 focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs transition-colors"
                      />
                    </div>
                    {confirmPassword.length > 0 && !passwordsMatch && (
                      <p className="text-[11px] text-red-600" aria-live="polite">
                        Passwords do not match.
                      </p>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={!canSubmitUpdate}
                    data-btn-primary
                    className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2"
                  >
                    {isSubmittingUpdate ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        <span>Updating Password...</span>
                      </>
                    ) : (
                      <>
                        <span>Update Password</span>
                        <ArrowRight className="size-4" />
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          ) : (
            /* Request Reset Link Form */
            <div>
              {requestSent ? (
                <div
                  role="status"
                  aria-live="polite"
                  className="flex flex-col items-center justify-center p-2 text-center space-y-4"
                >
                  <div className="grid size-12 place-items-center rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                    <CheckCircle className="size-6" />
                  </div>
                  <h2 className="font-display text-base font-semibold text-ink">
                    Reset link dispatched
                  </h2>
                  <p className="text-xs text-muted leading-relaxed">
                    If an account exists for <strong className="text-ink font-semibold">{email}</strong>,
                    you will receive an email with instructions to reset your password shortly.
                  </p>
                  <Link
                    to="/login"
                    className="inline-flex w-full items-center justify-center rounded-xl border border-border bg-canvas py-2.5 text-xs sm:text-sm font-semibold text-ink shadow-xs hover:bg-surface-subtle transition-colors"
                  >
                    Return to sign in
                  </Link>
                </div>
              ) : (
                <form onSubmit={handleRequestSubmit} className="space-y-4" noValidate>
                  {requestError && (
                    <div
                      role="alert"
                      aria-live="assertive"
                      className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800"
                    >
                      <AlertCircle className="size-4 flex-shrink-0 text-red-600 mt-0.5" />
                      <span>{requestError}</span>
                    </div>
                  )}

                  <div className="space-y-1.5">
                    <label htmlFor="reset-email" className="block text-xs font-semibold text-ink">
                      Studio Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none" />
                      <input
                        id="reset-email"
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

                  <button
                    type="submit"
                    disabled={!canSubmitRequest}
                    data-btn-primary
                    className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2"
                  >
                    {isSubmittingRequest ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        <span>Sending Link...</span>
                      </>
                    ) : (
                      <>
                        <span>Send Reset Link</span>
                        <ArrowRight className="size-4" />
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          )}

          {!requestSent && !updateSuccess && (
            <div className="text-center text-xs text-muted">
              Remember your password?{" "}
              <Link to="/login" className="font-semibold text-primary hover:underline">
                Sign in
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}