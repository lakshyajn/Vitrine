import React, { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { X, AlertTriangle, Loader2 } from "lucide-react";

export type ModalMaxWidth = "sm" | "md" | "lg" | "xl" | "2xl" | "3xl" | "4xl";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  maxWidth?: ModalMaxWidth;
  showCloseButton?: boolean;
  closeOnBackdropClick?: boolean;
  closeOnEscape?: boolean;
  className?: string;
  ariaLabelledBy?: string;
  ariaDescribedBy?: string;
  headerLeading?: React.ReactNode;
}

const MAX_WIDTH_MAP: Record<ModalMaxWidth, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
  "3xl": "max-w-3xl",
  "4xl": "max-w-4xl",
};

/**
 * Standard Viewport-Centered Modal Dialog.
 *
 * Guaranteed positioning:
 * - Always portaled directly to `document.body` outside of any scroll or transform containers.
 * - Backdrop fixed to `inset: 0` spanning the exact browser viewport.
 * - Center-aligned vertically and horizontally with responsive margins.
 * - Constrained to `100dvh - 3rem` with internal scrolling for tall content.
 * - Locks document body scroll while mounted.
 * - Restores focus to the triggering element on close.
 * - Implements keyboard focus trap and Escape key listener.
 */
export function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = "md",
  showCloseButton = true,
  closeOnBackdropClick = true,
  closeOnEscape = true,
  className = "",
  ariaLabelledBy,
  ariaDescribedBy,
  headerLeading,
}: ModalProps) {
  const previousActiveElement = useRef<HTMLElement | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Body scroll lock
  useEffect(() => {
    if (!isOpen || typeof document === "undefined") return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  // Focus trap & focus restoration
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement | null;
      const timer = setTimeout(() => {
        if (modalRef.current) {
          const focusable = modalRef.current.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          );
          if (focusable.length > 0) {
            focusable[0].focus();
          } else {
            modalRef.current.focus();
          }
        }
      }, 50);
      return () => clearTimeout(timer);
    } else if (previousActiveElement.current && typeof previousActiveElement.current.focus === "function") {
      previousActiveElement.current.focus();
    }
  }, [isOpen]);

  // Keyboard navigation & accessibility handlers
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape" && closeOnEscape) {
      e.stopPropagation();
      onClose();
      return;
    }

    if (e.key === "Tab" && modalRef.current) {
      const focusable = modalRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  };

  if (!isOpen) return null;

  const content = (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={ariaLabelledBy || (title ? "shared-modal-title" : undefined)}
      aria-describedby={ariaDescribedBy || (subtitle ? "shared-modal-subtitle" : undefined)}
      onKeyDown={handleKeyDown}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs animate-fade-in"
      onClick={(e) => {
        if (closeOnBackdropClick && e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        className={`relative w-full ${MAX_WIDTH_MAP[maxWidth]} max-h-[calc(100dvh-2rem)] sm:max-h-[calc(100dvh-3.5rem)] flex flex-col rounded-2xl border border-border bg-surface p-6 shadow-elevated text-ink animate-scale-in focus:outline-none ${className}`}
      >
        {/* Header (if title or leading icon provided) */}
        {(title || showCloseButton || headerLeading) && (
          <div className="flex items-start justify-between gap-3 pb-4 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-3 min-w-0">
              {headerLeading && <div className="flex-shrink-0">{headerLeading}</div>}
              <div className="min-w-0">
                {title && (
                  <h2 id={ariaLabelledBy || "shared-modal-title"} className="font-display text-lg font-bold tracking-tight text-ink truncate">
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p id={ariaDescribedBy || "shared-modal-subtitle"} className="mt-0.5 text-xs text-muted truncate">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>

            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg p-1 text-muted hover:text-ink hover:bg-surface-subtle transition-colors focus-visible:outline-2 focus-visible:outline-primary flex-shrink-0"
                aria-label="Close dialog"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
        )}

        {/* Scrollable Body Content */}
        <div className="overflow-y-auto min-h-0 py-4 flex-1">
          {children}
        </div>
      </div>
    </div>
  );

  return typeof document !== "undefined" ? createPortal(content, document.body) : content;
}

export interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  subtitle?: string;
  description: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "primary" | "warning";
  isLoading?: boolean;
  icon?: React.ComponentType<{ className?: string }>;
}

/**
 * Standard confirmation dialog for destructive or workflow actions.
 */
export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  subtitle,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "primary",
  isLoading = false,
  icon: IconComponent = AlertTriangle,
}: ConfirmationModalProps) {
  const iconColors =
    variant === "danger"
      ? "bg-rose-50 text-rose-600 border-rose-200"
      : variant === "warning"
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : "bg-primary/10 text-primary border-primary/20";

  const confirmBtnColors =
    variant === "danger"
      ? "bg-rose-600 hover:bg-rose-700 text-white focus-visible:outline-rose-600"
      : variant === "warning"
      ? "bg-amber-600 hover:bg-amber-700 text-white focus-visible:outline-amber-600"
      : "bg-primary hover:bg-primary-hover text-white focus-visible:outline-primary";

  return (
    <Modal
      isOpen={isOpen}
      onClose={isLoading ? () => {} : onClose}
      maxWidth="md"
      showCloseButton={!isLoading}
      closeOnBackdropClick={!isLoading}
      closeOnEscape={!isLoading}
      headerLeading={
        <div className={`flex size-10 items-center justify-center rounded-xl border ${iconColors}`}>
          <IconComponent className="size-5" />
        </div>
      }
      title={title}
      subtitle={subtitle}
    >
      <div className="space-y-5">
        <div className="text-sm text-ink leading-relaxed">
          {description}
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
          <button
            type="button"
            disabled={isLoading}
            onClick={onClose}
            className="rounded-xl border border-border bg-surface px-4 py-2 text-xs sm:text-sm font-semibold text-ink hover:bg-surface-subtle transition-colors disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-primary"
          >
            {cancelText}
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={onConfirm}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs sm:text-sm font-semibold shadow-xs transition-colors disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 ${confirmBtnColors}`}
          >
            {isLoading && <Loader2 className="size-4 animate-spin" />}
            <span>{isLoading ? "Please wait..." : confirmText}</span>
          </button>
        </div>
      </div>
    </Modal>
  );
}

