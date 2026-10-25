import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ArrowLeft, Sparkles, X, Upload, Check, AlertCircle, Loader2 } from "lucide-react";
import {
  getProduct,
  createProduct,
  updateProduct,
  uploadProductImage,
  type PriceSegment,
  type ProductCreate,
  type ProductAttributes,
} from "@/api";
import { ExtractProfileModal } from "./ExtractProfileModal";

export function ProductFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);

  const [isLoading, setIsLoading] = useState(isEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isExtractModalOpen, setIsExtractModalOpen] = useState(false);

  // Form Fields
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Apparel & Accessories");
  const [description, setDescription] = useState("");
  const [materialInput, setMaterialInput] = useState("");
  const [materials, setMaterials] = useState<string[]>([]);
  const [styleInput, setStyleInput] = useState("");
  const [style, setStyle] = useState<string[]>([]);
  const [motifsInput, setMotifsInput] = useState("");
  const [motifs, setMotifs] = useState<string[]>([]);
  const [coloursInput, setColoursInput] = useState("");
  const [colours, setColours] = useState<string[]>([]);
  const [priceSegment, setPriceSegment] = useState<PriceSegment>("mid_premium");
  const [priceMin, setPriceMin] = useState<string>("85");
  const [priceMax, setPriceMax] = useState<string>("140");
  const [currency, setCurrency] = useState("USD");
  const [moq, setMoq] = useState<string>("12");
  const [monthlyCapacity, setMonthlyCapacity] = useState<string>("150");
  const [retailerTypeInput, setRetailerTypeInput] = useState("");
  const [targetRetailerTypes, setTargetRetailerTypes] = useState<string[]>([
    "Independent Design Boutique",
    "Curated Lifestyle Concept Store",
  ]);
  const [images, setImages] = useState<string[]>([
    "/images/vitrine-boutique-collection.webp",
  ]);

  // Load product if edit mode
  useEffect(() => {
    if (!id) return;
    const load = async () => {
      setIsLoading(true);
      try {
        const prod = await getProduct(id);
        setName(prod.name);
        setCategory(prod.category);
        setDescription(prod.description);
        setMaterials(prod.materials);
        setStyle(prod.style);
        setMotifs(prod.motifs);
        setColours(prod.colours);
        setPriceSegment(prod.price_segment);
        setPriceMin(prod.price_min !== null ? String(prod.price_min) : "");
        setPriceMax(prod.price_max !== null ? String(prod.price_max) : "");
        setCurrency(prod.currency);
        setMoq(String(prod.moq));
        setMonthlyCapacity(prod.monthly_capacity !== null ? String(prod.monthly_capacity) : "");
        setTargetRetailerTypes(prod.target_retailer_types);
        setImages(prod.images);
      } catch (err: unknown) {
        setFormError(err instanceof Error ? err.message : "Failed to load product data.");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [id]);

  // Tag helper adders
  const addTag = (
    val: string,
    list: string[],
    setter: (l: string[]) => void,
    inputSetter: (v: string) => void
  ) => {
    const trimmed = val.trim();
    if (trimmed && !list.includes(trimmed)) {
      setter([...list, trimmed]);
      inputSetter("");
    }
  };

  const removeTag = (tag: string, list: string[], setter: (l: string[]) => void) => {
    setter(list.filter((t) => t !== tag));
  };

  // AI Attribute Application
  const handleApplyExtracted = (extracted: Partial<ProductAttributes>) => {
    if (extracted.category) setCategory(extracted.category);
    if (extracted.materials?.length) {
      setMaterials((prev) => Array.from(new Set([...prev, ...extracted.materials!])));
    }
    if (extracted.style?.length) {
      setStyle((prev) => Array.from(new Set([...prev, ...extracted.style!])));
    }
    if (extracted.motifs?.length) {
      setMotifs((prev) => Array.from(new Set([...prev, ...extracted.motifs!])));
    }
    if (extracted.colours?.length) {
      setColours((prev) => Array.from(new Set([...prev, ...extracted.colours!])));
    }
    if (extracted.price_segment) setPriceSegment(extracted.price_segment);
    if (extracted.price_min !== undefined && extracted.price_min !== null) setPriceMin(String(extracted.price_min));
    if (extracted.price_max !== undefined && extracted.price_max !== null) setPriceMax(String(extracted.price_max));
    if (extracted.moq !== undefined && extracted.moq !== null) setMoq(String(extracted.moq));
    if (extracted.monthly_capacity !== undefined && extracted.monthly_capacity !== null) setMonthlyCapacity(String(extracted.monthly_capacity));
    if (extracted.target_retailer_types?.length) {
      setTargetRetailerTypes((prev) => Array.from(new Set([...prev, ...extracted.target_retailer_types!])));
    }
  };

  // Image Upload Handler
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (id) {
      try {
        const updatedImages = await uploadProductImage(id, file);
        setImages(updatedImages);
      } catch (err: unknown) {
        alert(err instanceof Error ? err.message : "Image upload failed");
      }
    } else {
      // Local preview before saving
      const localUrl = URL.createObjectURL(file);
      setImages((prev) => [...prev, localUrl]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Validation
    if (name.length < 2 || name.length > 80) {
      setFormError("Product name must be between 2 and 80 characters.");
      return;
    }
    if (!category.trim()) {
      setFormError("Category is required.");
      return;
    }
    if (!description.trim()) {
      setFormError("Description is required.");
      return;
    }
    if (materials.length === 0) {
      setFormError("Please add at least one material.");
      return;
    }

    const pMin = priceMin ? parseFloat(priceMin) : null;
    const pMax = priceMax ? parseFloat(priceMax) : null;

    if (pMin !== null && pMax !== null && pMin > pMax) {
      setFormError("Minimum price cannot exceed maximum price.");
      return;
    }

    const parsedMoq = parseInt(moq, 10) || 1;
    if (parsedMoq < 1) {
      setFormError("MOQ must be at least 1.");
      return;
    }

    const parsedCap = monthlyCapacity ? parseInt(monthlyCapacity, 10) : null;

    const payload: ProductCreate = {
      name: name.trim(),
      category: category.trim(),
      description: description.trim(),
      materials,
      style,
      motifs,
      colours,
      price_segment: priceSegment,
      price_min: pMin,
      price_max: pMax,
      currency,
      moq: parsedMoq,
      monthly_capacity: parsedCap,
      target_retailer_types: targetRetailerTypes,
      images,
      is_demo: false,
    };

    setIsSaving(true);
    try {
      if (isEditMode && id) {
        await updateProduct(id, payload);
      } else {
        await createProduct(payload);
      }
      navigate("/app/products");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save product.";
      setFormError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const isCapWarning =
    monthlyCapacity && moq && parseInt(monthlyCapacity, 10) < parseInt(moq, 10);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="h-8 w-48 rounded bg-border animate-pulse" />
        <div className="mt-6 space-y-4">
          <div className="h-12 w-full rounded-xl bg-surface border border-border animate-pulse" />
          <div className="h-32 w-full rounded-xl bg-surface border border-border animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Top Navigation & AI Trigger */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <Link
            to="/app/products"
            className="flex size-9 items-center justify-center rounded-xl border border-border bg-surface text-muted hover:bg-surface-subtle hover:text-ink transition-colors shadow-xs"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-ink">
              {isEditMode ? "Edit Product Passport" : "New Product Passport"}
            </h1>
            <p className="text-xs text-muted">
              Define artisan specifications, materials provenance, and wholesale terms.
            </p>
          </div>
        </div>

        {/* AI Extraction Trigger */}
        <button
          type="button"
          onClick={() => setIsExtractModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl border border-primary/30 bg-primary-light px-3.5 py-2 text-xs font-semibold text-primary hover:bg-primary-light/80 transition-colors shadow-xs"
        >
          <Sparkles className="size-4" />
          <span>AI Extract from Spec / Notes</span>
        </button>
      </div>

      {formError && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-900">
          <AlertCircle className="size-4 flex-shrink-0 text-rose-600" />
          <span>{formError}</span>
        </div>
      )}

      {/* Form Container */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core Identity Card */}
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
          <h2 className="font-display text-base font-semibold text-ink">Product Identity</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2 space-y-1.5">
              <label htmlFor="prod-name" className="block text-xs font-semibold text-ink">
                Product Title <span className="text-rose-600">*</span>
              </label>
              <input
                id="prod-name"
                type="text"
                required
                maxLength={80}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Botanical Plant-Dyed Habotai Silk Scarf"
                className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
              <span className="text-[10px] text-muted">{name.length}/80 characters</span>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="prod-cat" className="block text-xs font-semibold text-ink">
                Category <span className="text-rose-600">*</span>
              </label>
              <select
                id="prod-cat"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              >
                <option value="Apparel & Accessories">Apparel & Accessories</option>
                <option value="Ceramics & Homeware">Ceramics & Homeware</option>
                <option value="Leather & Goods">Leather & Goods</option>
                <option value="Jewelry & Objects">Jewelry & Objects</option>
                <option value="Stationery & Print">Stationery & Print</option>
                <option value="Apothecary & Fragrance">Apothecary & Fragrance</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="prod-desc" className="block text-xs font-semibold text-ink">
              Narrative & Craft Description <span className="text-rose-600">*</span>
            </label>
            <textarea
              id="prod-desc"
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe origin, technique, finish, and the maker's philosophy..."
              className="w-full rounded-xl border border-border bg-canvas p-3.5 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            />
          </div>
        </div>

        {/* Materials & Aesthetics Card */}
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
          <h2 className="font-display text-base font-semibold text-ink">Materials & Aesthetic Profile</h2>

          {/* Materials Tag Input */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-ink">
              Materials Provenance <span className="text-rose-600">* (at least 1)</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={materialInput}
                onChange={(e) => setMaterialInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag(materialInput, materials, setMaterials, setMaterialInput);
                  }
                }}
                placeholder="e.g. Mulberry Silk, Madder Root Dye (press Enter to add)"
                className="flex-1 rounded-xl border border-border bg-canvas px-3.5 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
              <button
                type="button"
                onClick={() => addTag(materialInput, materials, setMaterials, setMaterialInput)}
                className="rounded-xl border border-border bg-surface-subtle px-3 py-2 text-xs font-semibold text-ink hover:bg-surface transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {materials.map((m) => (
                <span
                  key={m}
                  className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface-subtle px-2.5 py-1 text-xs font-medium text-ink"
                >
                  <span>{m}</span>
                  <button
                    type="button"
                    onClick={() => removeTag(m, materials, setMaterials)}
                    className="text-muted hover:text-rose-600"
                  >
                    <X className="size-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Style Tags */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-ink">Style Tags</label>
              <div className="flex gap-1.5">
                <input
                  type="text"
                  value={styleInput}
                  onChange={(e) => setStyleInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addTag(styleInput, style, setStyle, setStyleInput);
                    }
                  }}
                  placeholder="e.g. Minimalist"
                  className="flex-1 rounded-xl border border-border bg-canvas px-3 py-1.5 text-xs text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
                <button
                  type="button"
                  onClick={() => addTag(styleInput, style, setStyle, setStyleInput)}
                  className="rounded-xl border border-border bg-surface-subtle px-2.5 py-1.5 text-xs font-semibold text-ink"
                >
                  +
                </button>
              </div>
              <div className="flex flex-wrap gap-1 pt-1">
                {style.map((s) => (
                  <span
                    key={s}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-0.5 text-[11px] text-muted"
                  >
                    <span>{s}</span>
                    <button type="button" onClick={() => removeTag(s, style, setStyle)}>
                      <X className="size-2.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Motifs */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-ink">Motifs & Textures</label>
              <div className="flex gap-1.5">
                <input
                  type="text"
                  value={motifsInput}
                  onChange={(e) => setMotifsInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addTag(motifsInput, motifs, setMotifs, setMotifsInput);
                    }
                  }}
                  placeholder="e.g. Variegation"
                  className="flex-1 rounded-xl border border-border bg-canvas px-3 py-1.5 text-xs text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
                <button
                  type="button"
                  onClick={() => addTag(motifsInput, motifs, setMotifs, setMotifsInput)}
                  className="rounded-xl border border-border bg-surface-subtle px-2.5 py-1.5 text-xs font-semibold text-ink"
                >
                  +
                </button>
              </div>
              <div className="flex flex-wrap gap-1 pt-1">
                {motifs.map((m) => (
                  <span
                    key={m}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-0.5 text-[11px] text-muted"
                  >
                    <span>{m}</span>
                    <button type="button" onClick={() => removeTag(m, motifs, setMotifs)}>
                      <X className="size-2.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Colours */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-ink">Palette / Colours</label>
              <div className="flex gap-1.5">
                <input
                  type="text"
                  value={coloursInput}
                  onChange={(e) => setColoursInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addTag(coloursInput, colours, setColours, setColoursInput);
                    }
                  }}
                  placeholder="e.g. Madder Coral"
                  className="flex-1 rounded-xl border border-border bg-canvas px-3 py-1.5 text-xs text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
                <button
                  type="button"
                  onClick={() => addTag(coloursInput, colours, setColours, setColoursInput)}
                  className="rounded-xl border border-border bg-surface-subtle px-2.5 py-1.5 text-xs font-semibold text-ink"
                >
                  +
                </button>
              </div>
              <div className="flex flex-wrap gap-1 pt-1">
                {colours.map((c) => (
                  <span
                    key={c}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-0.5 text-[11px] text-muted"
                  >
                    <span>{c}</span>
                    <button type="button" onClick={() => removeTag(c, colours, setColours)}>
                      <X className="size-2.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Wholesale Parameters & Pricing */}
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
          <h2 className="font-display text-base font-semibold text-ink">Wholesale Terms & Capacity</h2>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <label htmlFor="prod-seg" className="block text-xs font-semibold text-ink">Price Segment</label>
              <select
                id="prod-seg"
                value={priceSegment}
                onChange={(e) => setPriceSegment(e.target.value as PriceSegment)}
                className="w-full rounded-xl border border-border bg-canvas px-3 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              >
                <option value="budget">Budget</option>
                <option value="mid">Mid</option>
                <option value="mid_premium">Mid-Premium</option>
                <option value="premium">Premium</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="prod-pmin" className="block text-xs font-semibold text-ink">Wholesale Price Min</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-muted">$</span>
                <input
                  id="prod-pmin"
                  type="number"
                  min="0"
                  step="0.01"
                  value={priceMin}
                  onChange={(e) => setPriceMin(e.target.value)}
                  placeholder="85"
                  className="w-full rounded-xl border border-border bg-canvas pl-7 pr-3 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="prod-pmax" className="block text-xs font-semibold text-ink">Wholesale Price Max</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-muted">$</span>
                <input
                  id="prod-pmax"
                  type="number"
                  min="0"
                  step="0.01"
                  value={priceMax}
                  onChange={(e) => setPriceMax(e.target.value)}
                  placeholder="140"
                  className="w-full rounded-xl border border-border bg-canvas pl-7 pr-3 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="prod-curr" className="block text-xs font-semibold text-ink">Currency</label>
              <input
                id="prod-curr"
                type="text"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                className="w-full rounded-xl border border-border bg-canvas px-3 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label htmlFor="prod-moq" className="block text-xs font-semibold text-ink">
                Minimum Order Quantity (MOQ) <span className="text-rose-600">*</span>
              </label>
              <input
                id="prod-moq"
                type="number"
                min="1"
                required
                value={moq}
                onChange={(e) => setMoq(e.target.value)}
                placeholder="12"
                className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="prod-cap" className="block text-xs font-semibold text-ink">
                Monthly Studio Capacity (Units)
              </label>
              <input
                id="prod-cap"
                type="number"
                min="1"
                value={monthlyCapacity}
                onChange={(e) => setMonthlyCapacity(e.target.value)}
                placeholder="150"
                className="w-full rounded-xl border border-border bg-canvas px-3.5 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
              {isCapWarning && (
                <p className="text-[11px] text-amber-700">
                  Note: Monthly capacity is lower than opening MOQ. Consider studio lead times.
                </p>
              )}
            </div>
          </div>

          {/* Target Retailer Types */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-ink">Target Retailer Channels</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={retailerTypeInput}
                onChange={(e) => setRetailerTypeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag(retailerTypeInput, targetRetailerTypes, setTargetRetailerTypes, setRetailerTypeInput);
                  }
                }}
                placeholder="e.g. Museum Design Store (press Enter)"
                className="flex-1 rounded-xl border border-border bg-canvas px-3.5 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
              />
              <button
                type="button"
                onClick={() => addTag(retailerTypeInput, targetRetailerTypes, setTargetRetailerTypes, setRetailerTypeInput)}
                className="rounded-xl border border-border bg-surface-subtle px-3 py-2 text-xs font-semibold text-ink"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {targetRetailerTypes.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface-subtle px-2.5 py-1 text-xs font-medium text-ink"
                >
                  <span>{t}</span>
                  <button type="button" onClick={() => removeTag(t, targetRetailerTypes, setTargetRetailerTypes)}>
                    <X className="size-3 text-muted hover:text-rose-600" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Product Imagery Card */}
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-4">
          <h2 className="font-display text-base font-semibold text-ink">Lookbook & Product Imagery</h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {images.map((img, idx) => (
              <div
                key={idx}
                className="group relative aspect-square overflow-hidden rounded-xl border border-border bg-surface-subtle"
              >
                <img src={img} alt={`Product asset ${idx + 1}`} className="h-full w-full object-cover" />
                <button
                  type="button"
                  onClick={() => setImages(images.filter((_, i) => i !== idx))}
                  className="absolute right-2 top-2 rounded-lg bg-black/70 p-1 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove image"
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ))}

            <label className="flex aspect-square cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface-subtle/50 p-4 text-center hover:border-primary hover:bg-primary-light/10 transition-colors">
              <Upload className="size-6 text-muted" />
              <span className="mt-2 text-xs font-semibold text-ink">Upload Photo</span>
              <span className="text-[10px] text-muted">PNG, JPG or WEBP</span>
              <input type="file" accept="image/*" onChange={handleImageUpload} className="sr-only" />
            </label>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
          <Link
            to="/app/products"
            className="rounded-xl border border-border bg-surface px-5 py-2.5 text-xs sm:text-sm font-semibold text-ink hover:bg-surface-subtle transition-colors"
          >
            Cancel
          </Link>

          <button
            type="submit"
            disabled={isSaving}
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-xl px-6 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs disabled:opacity-50 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            {isSaving ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                <span>Saving Passport...</span>
              </>
            ) : (
              <>
                <Check className="size-4" />
                <span>{isEditMode ? "Update Product Passport" : "Save Product Passport"}</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* AI Extraction Modal */}
      <ExtractProfileModal
        isOpen={isExtractModalOpen}
        onClose={() => setIsExtractModalOpen(false)}
        onApply={handleApplyExtracted}
      />
    </div>
  );
}

