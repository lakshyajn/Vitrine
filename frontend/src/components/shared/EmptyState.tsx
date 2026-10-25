import type { LucideIcon } from "lucide-react";
import { FolderSearch } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon = FolderSearch,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`mx-auto flex max-w-md flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-surface/50 p-8 text-center sm:p-12 ${className}`}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-surface-subtle border border-border text-muted">
        <Icon className="size-6 text-muted" aria-hidden="true" />
      </div>

      <h3 className="mt-4 font-display text-base font-semibold text-ink sm:text-lg">
        {title}
      </h3>

      <p className="mt-1.5 text-xs sm:text-sm leading-relaxed text-muted">
        {description}
      </p>

      {action && (
        <button
          type="button"
          onClick={action.onClick}
          data-btn-primary
          className="mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
        >
          {action.icon && <action.icon className="size-4" aria-hidden="true" />}
          <span>{action.label}</span>
        </button>
      )}
    </div>
  );
}
