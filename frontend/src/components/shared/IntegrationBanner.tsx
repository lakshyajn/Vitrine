import { Cpu, Search, Sparkles } from "lucide-react";

export type IntegrationStateType = "live" | "mock" | "pending" | "disabled";

export interface IntegrationStatusResponse {
  nebius?: IntegrationStateType;
  tavily?: IntegrationStateType;
  qloo?: IntegrationStateType;
  [key: string]: IntegrationStateType | undefined;
}

interface IntegrationBannerProps {
  status?: IntegrationStatusResponse | null;
  className?: string;
}

export function IntegrationBanner({ status, className = "" }: IntegrationBannerProps) {
  const getBadge = (state?: IntegrationStateType) => {
    switch (state) {
      case "live":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            Live
          </span>
        );
      case "mock":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted">
            <span className="size-1.5 rounded-full bg-subtle" />
            Mock Adapter
          </span>
        );
      case "disabled":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700">
            <span className="size-1.5 rounded-full bg-rose-500" />
            Disabled
          </span>
        );
      case "pending":
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700">
            <span className="size-1.5 rounded-full bg-amber-500 animate-pulse" />
            Checking
          </span>
        );
    }
  };

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-surface px-4 py-2.5 text-xs text-muted shadow-card ${className}`}
    >
      <div className="flex items-center gap-2">
        <span className="font-semibold text-ink">Provider Subsystems</span>
        <span className="text-subtle">|</span>
        <span className="text-[11px] text-muted">Evidence & Model Pipeline</span>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        {/* Nebius / Nemotron AI */}
        <div className="flex items-center gap-1.5">
          <Cpu className="size-3.5 text-primary" aria-hidden="true" />
          <span className="font-medium text-ink">Nemotron AI:</span>
          {getBadge(status?.nebius || "mock")}
        </div>

        {/* Tavily Web Search */}
        <div className="flex items-center gap-1.5">
          <Search className="size-3.5 text-primary" aria-hidden="true" />
          <span className="font-medium text-ink">Tavily Web:</span>
          {getBadge(status?.tavily || "mock")}
        </div>

        {/* Qloo Cultural Taste */}
        <div className="flex items-center gap-1.5">
          <Sparkles className="size-3.5 text-primary" aria-hidden="true" />
          <span className="font-medium text-ink">Qloo Taste:</span>
          {getBadge(status?.qloo || "mock")}
        </div>
      </div>
    </div>
  );
}
