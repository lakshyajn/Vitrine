import { Sparkles } from "lucide-react";

interface DemoBadgeProps {
  label?: string;
  className?: string;
}

export function DemoBadge({ label = "Demo data", className = "" }: DemoBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-border-strong bg-surface-subtle px-2.5 py-0.5 text-[11px] font-medium tracking-tight text-muted ${className}`}
      title="This record is synthesized or sample demonstration data"
    >
      <Sparkles className="size-3 text-subtle" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}
