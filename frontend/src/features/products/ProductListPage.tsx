import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, Compass, Edit, Trash2, Package, Sparkles, CheckCircle, X } from "lucide-react";
import { getProducts, deleteProduct, type Product } from "@/api";
import { useSeedDemo } from "@/api/demo";
import { DemoBadge } from "@/components/shared/DemoBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

export function ProductListPage() {
  const navigate = useNavigate();
  const seedMutation = useSeedDemo();

  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [segmentFilter, setSegmentFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchProducts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getProducts();
      setProducts(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load products.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSeedDemo = async () => {
    try {
      const res = await seedMutation.mutateAsync();
      await fetchProducts();
      setNotification(
        `Demo catalogue loaded: ${res.products_seeded} products, ${res.leads_seeded} leads, and ${res.runs_seeded} discovery run.`
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to seed demo data.");
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteProduct(id);
      setProducts((prev) => prev.filter((p) => p.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete product.");
    } finally {
      setDeletingId(null);
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
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by product name, category, or material..."
              className="w-full rounded-xl border border-border bg-surface pl-9 pr-4 py-2 text-xs sm:text-sm text-ink placeholder:text-subtle focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
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
        /* Empty Catalog: Show Load Demo Catalogue as primary action */
        <EmptyState
          title="No products in your catalog yet"
          description="Create your first Product Passport or load our curated demo scenario to explore wholesale research and buyer matching."
          icon={Package}
          action={{
            label: "Load demo catalogue",
            onClick: handleSeedDemo,
            icon: Sparkles,
            loading: seedMutation.isPending,
          }}
          secondaryAction={{
            label: "Add First Product",
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
              {/* Card Header & Thumbnail */}
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="size-16 flex-shrink-0 overflow-hidden rounded-xl border border-border bg-surface-subtle">
                    {product.images[0] ? (
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
                      {product.is_demo && <DemoBadge />}
                    </div>
                    <h3 className="mt-1 font-display text-base font-semibold leading-snug text-ink truncate">
                      {product.name}
                    </h3>
                    <p className="text-xs text-muted font-medium">
                      {product.price_segment.replace("_", " ").toUpperCase()}{" "}
                      {product.price_min !== null && product.price_max !== null
                        ? `· $${product.price_min} – $${product.price_max} ${product.currency}`
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
                  onClick={() => navigate(`/app/discovery?product_id=${product.id}`)}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-primary/20 bg-primary-light px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary-light/80 transition-colors"
                >
                  <Compass className="size-3.5" />
                  <span>Start Discovery</span>
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
                    disabled={deletingId === product.id}
                    onClick={() => handleDelete(product.id, product.name)}
                    className="rounded-lg p-1.5 text-muted hover:bg-rose-50 hover:text-rose-600 transition-colors disabled:opacity-50"
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
    </div>
  );
}
