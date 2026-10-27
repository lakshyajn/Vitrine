import React from "react";
import type { LucideIcon } from "lucide-react";
import { FolderSearch, Loader2 } from "lucide-react";

interface ActionConfig {
  label: string;
  onClick: () => void;
  icon?: LucideIcon;
  disabled?: boolean;
  loading?: boolean;
}

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: ActionConfig;
  secondaryAction?: ActionConfig;
  children?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon = FolderSearch,
  action,
  secondaryAction,
  children,
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

      {children && <div className="mt-4 w-full">{children}</div>}

      {(action || secondaryAction) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {action && (
            <button
              type="button"
              onClick={action.onClick}
              disabled={action.disabled || action.loading}
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              {action.loading ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                action.icon && <action.icon className="size-4" aria-hidden="true" />
              )}
              <span>{action.label}</span>
            </button>
          )}

          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              disabled={secondaryAction.disabled || secondaryAction.loading}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-xs font-semibold text-ink shadow-xs hover:bg-surface-subtle transition-colors disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              {secondaryAction.loading ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                secondaryAction.icon && <secondaryAction.icon className="size-4" aria-hidden="true" />
              )}
              <span>{secondaryAction.label}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
