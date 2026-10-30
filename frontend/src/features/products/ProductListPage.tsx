import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, Compass, Edit, Trash2, Package, CheckCircle, X, Loader2, AlertTriangle } from "lucide-react";
import { getProducts, deleteProduct, createResearchRun, type Product } from "@/api";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ConfirmationModal } from "@/components/shared/Modal";

export function ProductListPage() {
  const navigate = useNavigate();

  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [segmentFilter, setSegmentFilter] = useState<string>("all");

  // Deletion modal state
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Discovery launch state
  const [startingDiscoveryId, setStartingDiscoveryId] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchProducts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getProducts();
      if (!isMountedRef.current) return;
      setProducts(data);
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      const msg = err instanceof Error ? err.message : "Failed to load products.";
      setError(msg);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // In-app deletion modal confirm
  const handleConfirmDelete = async () => {
    if (!deleteTarget || isDeleting) return;
    setIsDeleting(true);
    try {
      await deleteProduct(deleteTarget.id);
      setProducts((prev) => prev.filter((p) => p.id !== deleteTarget.id));
      setNotification(`"${deleteTarget.name}" was successfully removed.`);
      setDeleteTarget(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete product.");
    } finally {
      setIsDeleting(false);
    }
  };

  // Immediate start discovery from card
  const handleStartDiscovery = async (product: Product) => {
    if (startingDiscoveryId) return;
    setStartingDiscoveryId(product.id);
    setError(null);
    try {
      const targetRegions = ["United Kingdom", "France & Western Europe"];
      const targetRetailers = product.target_retailer_types?.length
        ? product.target_retailer_types
        : ["Independent Design Boutique", "Curated Lifestyle Concept Store"];

      const run = await createResearchRun({
        product_id: product.id,
        inputs: {
          regions: targetRegions,
          retailer_types: targetRetailers,
        },
      });

      navigate(`/app/discovery/${run.id}`);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? `Could not start discovery run: ${err.message}`
          : "Failed to start discovery run for this product."
      );
      setStartingDiscoveryId(null);
    }
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      searchQuery === "" ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.materials.some((m) => m.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesSegment =
      segmentFilter === "all" || p.price_segment === segmentFilter;

    return matchesSearch && matchesSegment;
  });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6 animate-fade-in">
      {/* Toast Notification Banner */}
      {notification && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 animate-fade-in shadow-xs"
        >
          <div className="flex items-center gap-2">
            <CheckCircle className="size-4 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{notification}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="rounded p-1 text-emerald-600 hover:text-emerald-900 transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="size-3.5" />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Product Passport
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Curate and verify your artisan catalog, materials, wholesale parameters, and brand assets.
          </p>
        </div>
        <div>
          <Link
            to="/app/products/new"
            data-btn-primary
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            <Plus className="size-4" />
            <span>Add New Product</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      {products.length > 0 && (
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between rounded-2xl border border-border bg-surface p-4 shadow-card">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, category, or material..."
              className="w-full rounded-xl border border-border bg-canvas pl-9 pr-4 py-2 text-xs sm:text-sm text-ink placeholder:text-subtle focus:border-primary focus:bg-surface focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted whitespace-nowrap">Segment:</span>
            <select
              value={segmentFilter}
              onChange={(e) => setSegmentFilter(e.target.value)}
              className="rounded-xl border border-border bg-surface px-3 py-2 text-xs sm:text-sm text-ink focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            >
              <option value="all">All Segments</option>
              <option value="budget">Budget</option>
              <option value="mid">Mid</option>
              <option value="mid_premium">Mid-Premium</option>
              <option value="premium">Premium</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <LoadingSkeleton variant="cards" count={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchProducts} />
      ) : products.length === 0 ? (
        /* Empty Catalog */
        <EmptyState
          title="No products in your catalogue yet"
          description="Create your first Product Passport with materials, wholesale specs, and brand assets to begin discovering stockists."
          icon={Package}
          action={{
            label: "Add Your First Product",
            onClick: () => navigate("/app/products/new"),
            icon: Plus,
          }}
        />
      ) : filteredProducts.length === 0 ? (
        /* Filter returned empty */
        <EmptyState
          title="No matching products found"
          description="Try adjusting your search criteria or clearing filters."
          icon={Package}
          action={{
            label: "Clear Filters",
            onClick: () => {
              setSearchQuery("");
              setSegmentFilter("all");
            },
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProducts.map((product) => (
            <div
              key={product.id}
              className="flex flex-col justify-between rounded-2xl border border-border bg-surface p-5 shadow-card transition-all hover:border-border-strong hover:shadow-elevated"
            >
              <div className="space-y-4">
                {/* Product Header & Image */}
                <div className="flex items-start gap-4">
                  <div className="size-20 flex-shrink-0 overflow-hidden rounded-xl border border-border bg-surface-subtle">
                    {product.images && product.images.length > 0 ? (
                      <img
                        src={product.images[0]}
                        alt={product.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-muted">
                        <Package className="size-6" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="rounded bg-surface-subtle px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted border border-border">
                        {product.category}
                      </span>
                    </div>
                    <h3 className="mt-1 font-display text-base font-semibold leading-snug text-ink truncate">
                      {product.name}
                    </h3>
                    <p className="text-xs text-muted font-medium">
                      {(product.price_segment || "mid_premium").replace("_", " ").toUpperCase()}{" "}
                      {product.price_min !== null && product.price_max !== null
                        ? `· ${product.currency} ${product.price_min} – ${product.price_max}`
                        : ""}
                    </p>
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs leading-relaxed text-muted line-clamp-2">
                  {product.description}
                </p>

                {/* Materials Tags */}
                {product.materials.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {product.materials.slice(0, 3).map((mat, i) => (
                      <span
                        key={i}
                        className="rounded-md border border-border-subtle bg-surface-subtle px-1.5 py-0.5 text-[10px] text-muted font-mono"
                      >
                        {mat}
                      </span>
                    ))}
                    {product.materials.length > 3 && (
                      <span className="text-[10px] text-subtle font-mono">
                        +{product.materials.length - 3} more
                      </span>
                    )}
                  </div>
                )}

                {/* Wholesale Parameters */}
                <div className="grid grid-cols-2 gap-2 rounded-xl border border-border-subtle bg-surface-subtle/50 p-2 text-xs">
                  <div>
                    <span className="text-[10px] text-muted uppercase">Min Order (MOQ)</span>
                    <p className="font-semibold text-ink">{product.moq} units</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted uppercase">Monthly Cap</span>
                    <p className="font-semibold text-ink">
                      {product.monthly_capacity ? `${product.monthly_capacity} units` : "Flexible"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="mt-5 flex items-center justify-between border-t border-border pt-4">
                <button
                  type="button"
                  disabled={startingDiscoveryId !== null}
                  onClick={() => handleStartDiscovery(product)}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-primary/20 bg-primary-light px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary-light/80 disabled:opacity-50 transition-colors"
                >
                  {startingDiscoveryId === product.id ? (
                    <>
                      <Loader2 className="size-3.5 animate-spin" />
                      <span>Starting Discovery...</span>
                    </>
                  ) : (
                    <>
                      <Compass className="size-3.5" />
                      <span>Start Discovery</span>
                    </>
                  )}
                </button>

                <div className="flex items-center gap-1">
                  <Link
                    to={`/app/products/${product.id}`}
                    className="rounded-lg p-1.5 text-muted hover:bg-surface-subtle hover:text-ink transition-colors"
                    title="Edit product"
                  >
                    <Edit className="size-4" />
                  </Link>
                  <button
                    type="button"
                    onClick={() => setDeleteTarget(product)}
                    className="rounded-lg p-1.5 text-muted hover:bg-rose-50 hover:text-rose-600 transition-colors"
                    title="Delete product"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Accessible In-App Deletion Confirmation Modal */}
      {deleteTarget && (
        <ConfirmationModal
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Product Passport"
          subtitle="This action will remove the product from your catalog."
          variant="danger"
          isLoading={isDeleting}
          confirmText="Delete Product"
          cancelText="Cancel"
          icon={AlertTriangle}
          description={
            <p>
              Are you sure you want to permanently delete{" "}
              <strong className="text-ink font-semibold">&ldquo;{deleteTarget.name}&rdquo;</strong>? This will remove all associated wholesale specifications and lookbook images.
            </p>
          }
        />
      )}
    </div>
  );
}
