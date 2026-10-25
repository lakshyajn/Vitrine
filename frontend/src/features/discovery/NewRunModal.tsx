import { useState } from "react";
import { X, Compass, Loader2 } from "lucide-react";
import {
  createResearchRun,
  type Product,
} from "@/api";

interface NewRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
  initialProductId?: string;
  onRunCreated: (runId: string) => void;
}

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
  const [selectedRegions, setSelectedRegions] = useState<string[]>([
    "United Kingdom",
    "France & Western Europe",
  ]);
  const [notes, setNotes] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const toggleRegion = (reg: string) => {
    setSelectedRegions((prev) =>
      prev.includes(reg) ? prev.filter((r) => r !== reg) : [...prev, reg]
    );
  };

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId) {
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
      const selectedProd = products.find((p) => p.id === selectedProductId);
      const retailerTypes = selectedProd?.target_retailer_types || [
        "Independent Design Boutique",
        "Curated Lifestyle Concept Store",
      ];

      const run = await createResearchRun({
        product_id: selectedProductId,
        inputs: {
          regions: selectedRegions,
          retailer_types: retailerTypes,
          notes: notes.trim() || undefined,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-fade-in">
      <div className="flex max-h-[90vh] w-full max-w-xl flex-col rounded-2xl border border-border bg-surface shadow-elevated">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary-light text-primary">
              <Compass className="size-4" />
            </div>
            <div>
              <h3 className="font-display text-base font-semibold text-ink">
                Start Market Discovery Run
              </h3>
              <p className="text-xs text-muted">
                Initiate evidence-backed retailer discovery across target regions.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted hover:bg-surface-subtle hover:text-ink transition-colors"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleStart} className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
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
            <select
              id="modal-prod"
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(e.target.value)}
              className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.category})
                </option>
              ))}
            </select>
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
            <span className="font-semibold text-ink">Workflow Notice:</span> Once initiated, Vitrine will formulate search queries and propose Brand Taste Anchors for your interactive review before final retailer discovery and verification.
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
              disabled={isLoading}
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
      </div>
    </div>
  );
}

