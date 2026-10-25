import { CheckCircle2, Sparkles, HelpCircle, Database } from "lucide-react";

export type ProvenanceType = "verified_fact" | "ai_assessment" | "unknown" | "demo_data" | string;

interface ProvenanceTagProps {
  provenance: ProvenanceType;
  className?: string;
}

export function ProvenanceTag({ provenance, className = "" }: ProvenanceTagProps) {
  switch (provenance) {
    case "verified_fact":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800 ${className}`}
          title="Fact independently extracted and verified against retailer official website"
        >
          <CheckCircle2 className="size-3 text-emerald-600" aria-hidden="true" />
          <span>Verified Fact</span>
        </span>
      );
    case "ai_assessment":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-md border border-purple-200 bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-800 ${className}`}
          title="Generated via AI evaluation and criteria matching"
        >
          <Sparkles className="size-3 text-purple-600" aria-hidden="true" />
          <span>AI Assessment</span>
        </span>
      );
    case "demo_data":
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-md border border-border-strong bg-surface-subtle px-2 py-0.5 text-xs font-medium text-muted ${className}`}
          title="Sample test demonstration record"
        >
          <Database className="size-3 text-subtle" aria-hidden="true" />
          <span>Demo Data</span>
        </span>
      );
    case "unknown":
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800 ${className}`}
          title="Insufficient evidence to confirm authenticity"
        >
          <HelpCircle className="size-3 text-amber-600" aria-hidden="true" />
          <span>Unverified</span>
        </span>
      );
  }
}
