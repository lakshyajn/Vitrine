import { HelpCircle } from "lucide-react";

interface ScoreBarProps {
  label: string;
  score: number | null | undefined;
  dimensionLabel?: "high" | "medium" | "low" | "unknown" | string | null;
  description?: string;
  className?: string;
}

export function ScoreBar({
  label,
  score,
  dimensionLabel,
  description,
  className = "",
}: ScoreBarProps) {
  // If score is null or undefined, or dimensionLabel is unknown, strictly state "Not enough evidence"
  const isUnknown = score === null || score === undefined || dimensionLabel === "unknown";

  const getScoreColor = (val: number) => {
    if (val >= 80) return "bg-emerald-600";
    if (val >= 50) return "bg-amber-600";
    return "bg-rose-600";
  };

  const getBadgeStyle = () => {
    if (isUnknown) return "bg-surface-subtle text-muted border-border";
    const s = score as number;
    if (s >= 80) return "bg-emerald-50 text-emerald-800 border-emerald-200";
    if (s >= 50) return "bg-amber-50 text-amber-800 border-amber-200";
    return "bg-rose-50 text-rose-800 border-rose-200";
  };

  const formattedScoreText = isUnknown
    ? "Not enough evidence"
    : `${Math.round(score as number)}%`;

  return (
    <div className={`space-y-1.5 ${className}`}>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-ink">{label}</span>
        <div className="flex items-center gap-1.5">
          {dimensionLabel && dimensionLabel !== "unknown" && (
            <span className="rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted">
              {dimensionLabel}
            </span>
          )}
          <span
            className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-semibold ${getBadgeStyle()}`}
          >
            {isUnknown && <HelpCircle className="size-3 text-subtle" aria-hidden="true" />}
            {formattedScoreText}
          </span>
        </div>
      </div>

      <div className="relative h-2 w-full overflow-hidden rounded-full bg-border-subtle">
        {isUnknown ? (
          <div
            className="h-full w-full bg-[repeating-linear-gradient(45deg,#f1ecf0,#f1ecf0_6px,#e5dee4_6px,#e5dee4_12px)] opacity-60"
            title="Evidence pending or unknown"
          />
        ) : (
          <div
            className={`h-full rounded-full transition-all duration-300 ${getScoreColor(
              score as number
            )}`}
            style={{ width: `${Math.max(0, Math.min(100, score as number))}%` }}
          />
        )}
      </div>

      {description && (
        <p className="text-[11px] leading-relaxed text-muted">{description}</p>
      )}
    </div>
  );
}
