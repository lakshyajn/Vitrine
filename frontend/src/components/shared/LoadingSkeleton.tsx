interface LoadingSkeletonProps {
  variant?: "table" | "cards" | "detail" | "text";
  count?: number;
  className?: string;
}

export function LoadingSkeleton({
  variant = "cards",
  count = 3,
  className = "",
}: LoadingSkeletonProps) {
  if (variant === "text") {
    return (
      <div className={`space-y-2 animate-pulse ${className}`}>
        <div className="h-4 w-3/4 rounded bg-border" />
        <div className="h-4 w-1/2 rounded bg-border-subtle" />
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className={`space-y-3 animate-pulse ${className}`}>
        <div className="h-10 w-full rounded-lg bg-surface-subtle" />
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-16 w-full rounded-lg bg-surface border border-border flex items-center px-4 gap-4">
            <div className="size-8 rounded-full bg-border-subtle" />
            <div className="flex-1 space-y-2">
              <div className="h-3.5 w-1/4 rounded bg-border" />
              <div className="h-2.5 w-1/3 rounded bg-border-subtle" />
            </div>
            <div className="h-6 w-20 rounded bg-border-subtle" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "detail") {
    return (
      <div className={`space-y-6 animate-pulse ${className}`}>
        <div className="h-8 w-1/3 rounded bg-border" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 rounded-xl bg-surface border border-border" />
          <div className="h-24 rounded-xl bg-surface border border-border" />
          <div className="h-24 rounded-xl bg-surface border border-border" />
        </div>
        <div className="h-64 rounded-xl bg-surface border border-border" />
      </div>
    );
  }

  // Default: cards
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="h-4 w-28 rounded bg-border" />
            <div className="h-5 w-16 rounded-full bg-border-subtle" />
          </div>
          <div className="space-y-2">
            <div className="h-3 w-full rounded bg-border-subtle" />
            <div className="h-3 w-4/5 rounded bg-border-subtle" />
          </div>
          <div className="h-8 w-full rounded-lg bg-surface-subtle" />
        </div>
      ))}
    </div>
  );
}
