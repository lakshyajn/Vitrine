import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  code?: string;
  requestId?: string;
  isRetryable?: boolean;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  message = "An unexpected error occurred while communicating with the service.",
  code,
  requestId,
  isRetryable,
  onRetry,
  className = "",
}: ErrorStateProps) {
  // Auth errors must never render as the generic "Action Failed" card
  if (code === "unauthorized" || code === "401") {
    return null;
  }

  // Retry allowed for upstream_timeout, upstream_unavailable, rate_limited or explicit isRetryable
  const canRetry =
    Boolean(onRetry) &&
    (isRetryable ||
      (code &&
        ["upstream_timeout", "upstream_unavailable", "rate_limited", "network_error"].includes(
          code
        )));

  return (
    <div
      role="alert"
      className={`rounded-xl border border-rose-200 bg-rose-50/70 p-5 text-rose-950 sm:p-6 ${className}`}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="size-5 text-rose-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-rose-950">Action Failed</h4>
          <p className="mt-1 text-xs leading-relaxed text-rose-800">{message}</p>

          {(code || requestId) && (
            <div className="mt-2.5 flex flex-wrap items-center gap-2 font-mono text-[11px] text-rose-700/80">
              {code && (
                <span className="rounded bg-rose-100/80 px-1.5 py-0.5 border border-rose-200">
                  code: {code}
                </span>
              )}
              {requestId && (
                <span className="rounded bg-rose-100/80 px-1.5 py-0.5 border border-rose-200">
                  req: {requestId}
                </span>
              )}
            </div>
          )}

          {canRetry && onRetry && (
            <div className="mt-4">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-2 rounded-lg border border-rose-300 bg-white px-3 py-1.5 text-xs font-semibold text-rose-900 shadow-xs hover:bg-rose-50 focus-visible:outline-2 focus-visible:outline-rose-500"
              >
                <RefreshCw className="size-3.5" aria-hidden="true" />
                <span>Retry operation</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
