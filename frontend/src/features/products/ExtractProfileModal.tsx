import { useState } from "react";
import { Sparkles, Check, X, AlertCircle, Loader2 } from "lucide-react";
import { extractProductProfile, type ProductAttributes } from "@/api";

interface ExtractProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (extracted: Partial<ProductAttributes>) => void;
}

export function ExtractProfileModal({
  isOpen,
  onClose,
  onApply,
}: ExtractProfileModalProps) {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ProductAttributes | null>(null);

  // Field selection state for user control (field-by-field accept/reject)
  const [acceptedFields, setAcceptedFields] = useState<Record<string, boolean>>({
    category: true,
    materials: true,
    style: true,
    motifs: true,
    colours: true,
    price_segment: true,
    price_min: true,
    price_max: true,
    moq: true,
    monthly_capacity: true,
    target_retailer_types: true,
  });

  if (!isOpen) return null;

  const handleExtract = async () => {
    if (!inputText.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await extractProductProfile({ description: inputText });
      setResults(res);
      // Auto-enable fields that were populated
      setAcceptedFields({
        category: Boolean(res.category),
        materials: res.materials.length > 0,
        style: res.style.length > 0,
        motifs: res.motifs.length > 0,
        colours: res.colours.length > 0,
        price_segment: Boolean(res.price_segment),
        price_min: res.price_min !== null,
        price_max: res.price_max !== null,
        moq: res.moq !== null,
        monthly_capacity: res.monthly_capacity !== null,
        target_retailer_types: res.target_retailer_types.length > 0,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to extract product attributes.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleField = (field: string) => {
    setAcceptedFields((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const handleApplySelected = () => {
    if (!results) return;
    const toApply: Partial<ProductAttributes> = {};
    if (acceptedFields.category && results.category) toApply.category = results.category;
    if (acceptedFields.materials && results.materials.length) toApply.materials = results.materials;
    if (acceptedFields.style && results.style.length) toApply.style = results.style;
    if (acceptedFields.motifs && results.motifs.length) toApply.motifs = results.motifs;
    if (acceptedFields.colours && results.colours.length) toApply.colours = results.colours;
    if (acceptedFields.price_segment && results.price_segment) toApply.price_segment = results.price_segment;
    if (acceptedFields.price_min && results.price_min !== null) toApply.price_min = results.price_min;
    if (acceptedFields.price_max && results.price_max !== null) toApply.price_max = results.price_max;
    if (acceptedFields.moq && results.moq !== null) toApply.moq = results.moq;
    if (acceptedFields.monthly_capacity && results.monthly_capacity !== null) toApply.monthly_capacity = results.monthly_capacity;
    if (acceptedFields.target_retailer_types && results.target_retailer_types.length) toApply.target_retailer_types = results.target_retailer_types;

    onApply(toApply);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-fade-in">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-2xl border border-border bg-surface shadow-elevated">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary-light text-primary">
              <Sparkles className="size-4" />
            </div>
            <div>
              <h3 className="font-display text-base font-semibold text-ink">
                AI Attribute Extraction
              </h3>
              <p className="text-xs text-muted">
                Analyze studio notes or catalog copy into structured wholesale attributes.
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

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {!results ? (
            <div className="space-y-3">
              <label htmlFor="notes-input" className="block text-xs font-semibold text-ink">
                Paste Artisan Notes, Lookbook Narrative or Production Details:
              </label>
              <textarea
                id="notes-input"
                rows={6}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="e.g. Handcrafted mulberry silk scarf kettle-dyed with madder root. Small batches of 12 scarves, priced around $85 wholesale, looking for independent museum shops and slow-craft boutiques..."
                className="w-full rounded-xl border border-border bg-canvas p-3.5 text-xs text-ink placeholder:text-subtle focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary"
              />

              {error && (
                <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                  <AlertCircle className="size-4 flex-shrink-0 text-rose-600" />
                  <span>{error}</span>
                </div>
              )}

              <div className="rounded-xl border border-border bg-surface-subtle/50 p-3 text-xs text-muted">
                <span className="font-semibold text-ink">Seller Protection:</span> Vitrine never auto-saves extracted attributes. You will review and accept or reject each suggestion before applying it to your form.
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 text-xs text-emerald-900 flex items-center justify-between">
                <span>Extraction complete. Select which attributes to accept into your Product Passport:</span>
                <button
                  type="button"
                  onClick={() => setResults(null)}
                  className="font-semibold underline text-emerald-800 hover:text-emerald-950 text-xs"
                >
                  Edit prompt
                </button>
              </div>

              {/* Assumptions & Uncertainties callout if present */}
              {results.assumptions.length > 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-xs text-amber-900 space-y-1">
                  <span className="font-semibold">Model Assumptions & Notes:</span>
                  <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-amber-800">
                    {results.assumptions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Field Review Grid */}
              <div className="space-y-2">
                {/* Category */}
                {results.category && (
                  <div
                    onClick={() => toggleField("category")}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      acceptedFields.category
                        ? "border-primary bg-primary-light/40"
                        : "border-border bg-surface opacity-60"
                    }`}
                  >
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Category</span>
                      <p className="text-xs font-semibold text-ink">{results.category}</p>
                    </div>
                    <div className={`size-5 rounded flex items-center justify-center border ${acceptedFields.category ? "bg-primary border-primary text-white" : "border-border"}`}>
                      {acceptedFields.category && <Check className="size-3.5" />}
                    </div>
                  </div>
                )}

                {/* Materials */}
                {results.materials.length > 0 && (
                  <div
                    onClick={() => toggleField("materials")}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      acceptedFields.materials
                        ? "border-primary bg-primary-light/40"
                        : "border-border bg-surface opacity-60"
                    }`}
                  >
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Materials</span>
                      <p className="text-xs font-medium text-ink">{results.materials.join(", ")}</p>
                    </div>
                    <div className={`size-5 rounded flex items-center justify-center border ${acceptedFields.materials ? "bg-primary border-primary text-white" : "border-border"}`}>
                      {acceptedFields.materials && <Check className="size-3.5" />}
                    </div>
                  </div>
                )}

                {/* Style */}
                {results.style.length > 0 && (
                  <div
                    onClick={() => toggleField("style")}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      acceptedFields.style
                        ? "border-primary bg-primary-light/40"
                        : "border-border bg-surface opacity-60"
                    }`}
                  >
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Style</span>
                      <p className="text-xs font-medium text-ink">{results.style.join(", ")}</p>
                    </div>
                    <div className={`size-5 rounded flex items-center justify-center border ${acceptedFields.style ? "bg-primary border-primary text-white" : "border-border"}`}>
                      {acceptedFields.style && <Check className="size-3.5" />}
                    </div>
                  </div>
                )}

                {/* Price Range & Segment */}
                {(results.price_min !== null || results.price_segment) && (
                  <div
                    onClick={() => toggleField("price_segment")}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      acceptedFields.price_segment
                        ? "border-primary bg-primary-light/40"
                        : "border-border bg-surface opacity-60"
                    }`}
                  >
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Price Segment & Range</span>
                      <p className="text-xs font-medium text-ink">
                        {results.price_segment} {results.price_min && results.price_max ? `($${results.price_min} – $${results.price_max})` : ""}
                      </p>
                    </div>
                    <div className={`size-5 rounded flex items-center justify-center border ${acceptedFields.price_segment ? "bg-primary border-primary text-white" : "border-border"}`}>
                      {acceptedFields.price_segment && <Check className="size-3.5" />}
                    </div>
                  </div>
                )}

                {/* Target Retailer Types */}
                {results.target_retailer_types.length > 0 && (
                  <div
                    onClick={() => toggleField("target_retailer_types")}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      acceptedFields.target_retailer_types
                        ? "border-primary bg-primary-light/40"
                        : "border-border bg-surface opacity-60"
                    }`}
                  >
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Target Retailers</span>
                      <p className="text-xs font-medium text-ink">{results.target_retailer_types.join(", ")}</p>
                    </div>
                    <div className={`size-5 rounded flex items-center justify-center border ${acceptedFields.target_retailer_types ? "bg-primary border-primary text-white" : "border-border"}`}>
                      {acceptedFields.target_retailer_types && <Check className="size-3.5" />}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end gap-3 border-t border-border px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border bg-surface px-4 py-2 text-xs font-semibold text-ink hover:bg-surface-subtle transition-colors"
          >
            Cancel
          </button>

          {!results ? (
            <button
              type="button"
              disabled={isLoading || !inputText.trim()}
              onClick={handleExtract}
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold text-white shadow-xs disabled:opacity-50 transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  <span>Extracting Attributes...</span>
                </>
              ) : (
                <>
                  <Sparkles className="size-3.5" />
                  <span>Run Extraction</span>
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              onClick={handleApplySelected}
              data-btn-primary
              className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors"
            >
              <Check className="size-3.5" />
              <span>Apply Accepted Attributes</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

