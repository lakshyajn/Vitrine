import { Check, Clock, AlertTriangle, Loader2 } from "lucide-react";

export type ResearchRunStatusType =
  | "queued"
  | "running"
  | "awaiting_review"
  | "completed"
  | "failed";

export type ResearchRunStageType =
  | "planning"
  | "anchor_proposal"
  | "anchor_review"
  | "discovery"
  | "assessment"
  | "scoring"
  | "done";

interface StatusStepperProps {
  status: ResearchRunStatusType;
  stage: ResearchRunStageType;
  className?: string;
}

const STAGES: { key: ResearchRunStageType; label: string; description: string }[] = [
  { key: "planning", label: "Plan", description: "Formulating queries & regions" },
  { key: "anchor_proposal", label: "Anchors", description: "Proposing brand taste anchors" },
  { key: "anchor_review", label: "Review", description: "Awaiting seller confirmation" },
  { key: "discovery", label: "Discovery", description: "Extracting candidate retailers" },
  { key: "assessment", label: "Evidence", description: "Verifying official websites" },
  { key: "scoring", label: "Fit Score", description: "Calculating dimensional fit" },
  { key: "done", label: "Complete", description: "Verified leads ready" },
];

export function StatusStepper({ status, stage, className = "" }: StatusStepperProps) {
  const currentStageIndex = STAGES.findIndex((s) => s.key === stage);
  const isFailed = status === "failed";
  const isCompleted = status === "completed";
  const isAwaitingReview = status === "awaiting_review";

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Status Header Callout */}
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          {status === "running" && (
            <span className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary-light px-3 py-1 text-xs font-semibold text-primary">
              <Loader2 className="size-3.5 animate-spin" />
              Running Discovery
            </span>
          )}
          {isAwaitingReview && (
            <span className="flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900">
              <Clock className="size-3.5" />
              Action Required: Anchor Review
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-2 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-900">
              <Check className="size-3.5" />
              Discovery Run Completed
            </span>
          )}
          {isFailed && (
            <span className="flex items-center gap-2 rounded-full border border-rose-300 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-900">
              <AlertTriangle className="size-3.5" />
              Run Failed
            </span>
          )}
          {status === "queued" && (
            <span className="flex items-center gap-2 rounded-full border border-border bg-surface-subtle px-3 py-1 text-xs font-semibold text-muted">
              <Clock className="size-3.5" />
              Queued
            </span>
          )}
        </div>
        <span className="text-xs font-medium text-muted">
          Stage: <span className="font-semibold text-ink capitalize">{stage.replace("_", " ")}</span>
        </span>
      </div>

      {/* Stepper Grid */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
        {STAGES.map((s, index) => {
          let state: "upcoming" | "current" | "passed" | "error" = "upcoming";

          if (isFailed && index === currentStageIndex) {
            state = "error";
          } else if (index < currentStageIndex || isCompleted) {
            state = "passed";
          } else if (index === currentStageIndex) {
            state = "current";
          }

          return (
            <div
              key={s.key}
              className={`rounded-lg border p-2.5 transition-colors ${
                state === "current"
                  ? "border-primary bg-primary-light/50"
                  : state === "passed"
                  ? "border-emerald-200 bg-emerald-50/50"
                  : state === "error"
                  ? "border-rose-300 bg-rose-50/60"
                  : "border-border bg-surface opacity-60"
              }`}
            >
              <div className="flex items-center gap-1.5">
                {state === "passed" && (
                  <Check className="size-3.5 text-emerald-600" aria-hidden="true" />
                )}
                {state === "current" && (
                  <span className="size-2 rounded-full bg-primary animate-pulse" />
                )}
                {state === "error" && (
                  <AlertTriangle className="size-3.5 text-rose-600" aria-hidden="true" />
                )}
                {state === "upcoming" && (
                  <span className="size-1.5 rounded-full bg-subtle" />
                )}
                <span className="text-xs font-semibold text-ink">{s.label}</span>
              </div>
              <p className="mt-1 text-[11px] leading-tight text-muted">{s.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
