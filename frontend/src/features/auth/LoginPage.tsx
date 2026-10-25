import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight, Mail, Lock } from "lucide-react";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("studio@ateliersolenne.com");
  const [password, setPassword] = useState("••••••••••••");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      navigate("/app");
    }, 400);
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-canvas px-4 py-12 sm:px-6 lg:px-8 animate-fade-in">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <Link to="/" className="inline-flex items-center gap-2">
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
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="login-email" className="block text-xs font-semibold text-ink">
                Studio Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted" />
                <input
                  id="login-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="login-pwd" className="block text-xs font-semibold text-ink">
                  Password
                </label>
                <span className="text-[11px] text-muted hover:underline cursor-pointer">
                  Forgot password?
                </span>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted" />
                <input
                  id="login-pwd"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              data-btn-primary
              className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              <span>{isLoading ? "Signing in..." : "Enter Workspace"}</span>
              <ArrowRight className="size-4" />
            </button>
          </form>

          {/* Demonstration Notice */}
          <div className="rounded-xl border border-border bg-surface-subtle/50 p-3.5 text-xs text-muted space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-ink">
              <Sparkles className="size-3.5 text-primary" />
              <span>Instant Demo Mode</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Vitrine is preloaded with the Atelier Solenne demo studio catalog. Clicking Enter Workspace grants immediate access without requiring credentials.
            </p>
          </div>

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
