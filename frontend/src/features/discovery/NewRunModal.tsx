import { useState, useEffect } from "react";
import { Compass, Loader2, Zap, Sparkles, Search, Clock } from "lucide-react";
import {
  createResearchRun,
  type Product,
} from "@/api";
import { Modal } from "@/components/shared/Modal";

interface NewRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
  initialProductId?: string;
  onRunCreated: (runId: string) => void;
}

export type EffortLevel = "quick" | "standard" | "deep";

interface EffortOption {
  id: EffortLevel;
  name: string;
  badge: string;
  targetCount: number;
  estTime: string;
  description: string;
  icon: typeof Zap;
}

const EFFORT_OPTIONS: EffortOption[] = [
  {
    id: "quick",
    name: "Quick Probe",
    badge: "FASTEST",
    targetCount: 3,
    estTime: "~45s – 1 min",
    description: "Rapid initial market test. Verifies 3–4 high-fit independent boutiques.",
    icon: Zap,
  },
  {
    id: "standard",
    name: "Standard Discovery",
    badge: "RECOMMENDED",
    targetCount: 6,
    estTime: "~1.5 – 2.5 mins",
    description: "Recommended for makers. Balanced multi-query sweep across ~6–8 stockists.",
    icon: Sparkles,
  },
  {
    id: "deep",
    name: "Deep Market Sweep",
    badge: "MOST THOROUGH",
    targetCount: 12,
    estTime: "~3 – 5 mins",
    description: "Exhaustive multi-region discovery examining up to 12–15 verified retailers.",
    icon: Search,
  },
];

const REGION_OPTIONS = [
  "United Kingdom",
  "France & Western Europe",
  "Japan & East Asia",
  "United States - Northeast",
  "United States - Pacific Northwest",
  "United States - California",
  "Scandinavia & Nordics",
];

export function NewRunModal({
  isOpen,
  onClose,
  products,
  initialProductId,
  onRunCreated,
}: NewRunModalProps) {
  const [selectedProductId, setSelectedProductId] = useState(
    initialProductId || products[0]?.id || ""
  );
  const [selectedEffort, setSelectedEffort] = useState<EffortLevel>("standard");
  const [selectedRegions, setSelectedRegions] = useState<string[]>([
    "United Kingdom",
    "France & Western Europe",
  ]);
  const [notes, setNotes] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Synchronize and validate selected product whenever initialProductId, products, or modal open state changes
  useEffect(() => {
    if (!isOpen) return;
    setError(null);

    if (initialProductId && products.some((p) => p.id === initialProductId)) {
      setSelectedProductId(initialProductId);
    } else if (
      (!selectedProductId || !products.some((p) => p.id === selectedProductId)) &&
      products.length > 0
    ) {
      setSelectedProductId(products[0].id);
    }
  }, [initialProductId, products, selectedProductId, isOpen]);

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, isLoading]);

  if (!isOpen) return null;

  const toggleRegion = (reg: string) => {
    setSelectedRegions((prev) =>
      prev.includes(reg) ? prev.filter((r) => r !== reg) : [...prev, reg]
    );
  };

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    const effectiveProductId =
      selectedProductId || initialProductId || (products.length > 0 ? products[0].id : "");

    if (!effectiveProductId) {
      setError("Please select a product for market discovery.");
      return;
    }
    if (selectedRegions.length === 0) {
      setError("Please select at least one target market region.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const selectedProd = products.find((p) => p.id === effectiveProductId);
      const retailerTypes = selectedProd?.target_retailer_types?.length
        ? selectedProd.target_retailer_types
        : [
            "Independent Design Boutique",
            "Curated Lifestyle Concept Store",
          ];

      const effortMeta = EFFORT_OPTIONS.find((e) => e.id === selectedEffort) || EFFORT_OPTIONS[1];
      const effortTag = `[effort:${selectedEffort}] [max_leads:${effortMeta.targetCount}]`;
      const userNotes = notes.trim();
      const combinedNotes = userNotes ? `${effortTag}\n${userNotes}` : effortTag;

      const run = await createResearchRun({
        product_id: effectiveProductId,
        inputs: {
          regions: selectedRegions,
          retailer_types: retailerTypes,
          notes: combinedNotes,
        },
      });

      onRunCreated(run.id);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate research run.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="xl"
      title="Start Market Discovery Run"
      subtitle="Initiate evidence-backed retailer discovery across target regions."
      headerLeading={
        <div className="flex size-8 items-center justify-center rounded-lg bg-primary-light text-primary">
          <Compass className="size-4" />
        </div>
      }
    >
      <form onSubmit={handleStart} className="space-y-4">
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}

        {/* Product Selector */}
        <div className="space-y-1.5">
          <label htmlFor="modal-prod" className="block text-xs font-semibold text-ink">
            Select Product Passport <span className="text-rose-600">*</span>
          </label>
          {products.length === 0 ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 space-y-1">
              <p className="font-semibold">No products in your catalogue yet.</p>
              <p>Please create your first Product Passport before launching a discovery run.</p>
            </div>
          ) : (
            <select
              id="modal-prod"
              value={selectedProductId || (products.length > 0 ? products[0].id : "")}
              onChange={(e) => {
                setSelectedProductId(e.target.value);
                if (error) setError(null);
              }}
              className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.category})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Discovery Depth & Lead Target */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold text-ink">
              Discovery Depth & Lead Target <span className="text-rose-600">*</span>
            </label>
            <span className="text-[11px] text-muted">
              Controls search query breadth & verification time
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-1">
            {EFFORT_OPTIONS.map((opt) => {
              const isSelected = selectedEffort === opt.id;
              const Icon = opt.icon;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setSelectedEffort(opt.id)}
                  className={`flex flex-col text-left rounded-xl border p-3 transition-all relative ${
                    isSelected
                      ? "border-primary bg-primary-light/30 ring-1 ring-primary shadow-xs"
                      : "border-border bg-surface hover:bg-surface-subtle"
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-1.5 font-semibold text-xs text-ink">
                      <Icon className={`size-3.5 ${isSelected ? "text-primary" : "text-muted"}`} />
                      <span>{opt.name}</span>
                    </div>
                    <span
                      className={`text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded uppercase ${
                        isSelected
                          ? "bg-primary text-white"
                          : "bg-surface-subtle border border-border text-muted"
                      }`}
                    >
                      {opt.badge}
                    </span>
                  </div>

                  <div className="mt-2 text-xs font-semibold text-ink">
                    Target: ~{opt.targetCount} verified leads
                  </div>

                  <div className="flex items-center gap-1 text-[11px] text-muted mt-0.5">
                    <Clock className="size-3 text-subtle" />
                    <span>Est: {opt.estTime}</span>
                  </div>

                  <p className="text-[11px] text-muted mt-1.5 leading-relaxed">
                    {opt.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* AI Verification & Time Expectations Notice Box */}
        <div className="rounded-xl border border-amber-200/80 bg-amber-50/70 p-3.5 text-xs text-amber-950 space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-amber-900">
            <Clock className="size-3.5 text-amber-700" />
            <span>AI Verification & Time Expectations</span>
          </div>
          <p className="text-[11px] leading-relaxed text-amber-900/90">
            Unlike generic directory dumps, Vitrine performs{" "}
            <strong className="font-semibold text-amber-950">deep reasoning with NVIDIA Nemotron 3 Ultra (550B)</strong>{" "}
            and <strong className="font-semibold text-amber-950">Super VL (120B)</strong> over live retailer websites to corroborate store catalogs and aesthetic alignment.
          </p>
          <p className="text-[11px] leading-relaxed text-amber-800">
            ⚡ <em>Choosing more leads or multiple regions increases search crawls and model latency (~15–20s per verified retailer). You can also confirm more anchors later on a completed run to expand your leads anytime!</em>
          </p>
        </div>

        {/* Regions Multi-Select */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-ink">
            Target Geographic Regions <span className="text-rose-600">*</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            {REGION_OPTIONS.map((region) => {
              const isSelected = selectedRegions.includes(region);
              return (
                <button
                  key={region}
                  type="button"
                  onClick={() => toggleRegion(region)}
                  className={`flex items-center justify-between rounded-xl border p-2.5 text-left text-xs transition-colors ${
                    isSelected
                      ? "border-primary bg-primary-light/40 font-semibold text-ink"
                      : "border-border bg-surface text-muted hover:bg-surface-subtle"
                  }`}
                >
                  <span>{region}</span>
                  <span
                    className={`size-4 rounded-full border flex items-center justify-center text-[10px] ${
                      isSelected ? "bg-primary border-primary text-white" : "border-border"
                    }`}
                  >
                    {isSelected ? "✓" : ""}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Additional Notes */}
        <div className="space-y-1.5">
          <label htmlFor="modal-notes" className="block text-xs font-semibold text-ink">
            Specific Retailer Focus / Context (Optional)
          </label>
          <textarea
            id="modal-notes"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Focus on stockists carrying slow-fashion, botanical pigments, and artisan textiles with physical storefronts..."
            className="w-full rounded-xl border border-border bg-canvas p-3 text-xs text-ink placeholder:text-subtle focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
          />
        </div>

        <div className="rounded-xl border border-border bg-surface-subtle/50 p-3 text-xs text-muted">
          <span className="font-semibold text-ink">Next step:</span> Once started, Vitrine will formulate search queries and propose reference stockists for your interactive review before final retailer discovery and verification.
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-border bg-surface px-4 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || products.length === 0}
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-xl px-5 py-2 text-xs font-semibold text-white shadow-xs disabled:opacity-50 transition-colors"
          >
            {isLoading ? (
              <>
                <Loader2 className="size-3.5 animate-spin" />
                <span>Initiating Run...</span>
              </>
            ) : (
              <>
                <Compass className="size-3.5" />
                <span>Launch Research Run</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
