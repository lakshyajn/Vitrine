import { apiRequest } from "./client";
import type {
  Product,
  ProductCreate,
  ProductUpdate,
  ProductAttributes,
  ExtractProfileRequest,
} from "./types";
import { MOCK_PRODUCTS } from "./mock-data";

// In-memory mock store for session mutations
let mockProductsStore: Product[] = [...MOCK_PRODUCTS];

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export async function getProducts(): Promise<Product[]> {
  if (USE_MOCK) {
    // Simulate brief network latency (150ms)
    await new Promise((r) => setTimeout(r, 150));
    return [...mockProductsStore];
  }
  return apiRequest<Product[]>("/products");
}

export async function getProduct(id: string): Promise<Product> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    const prod = mockProductsStore.find((p) => p.id === id);
    if (!prod) {
      throw new Error(`Product not found: ${id}`);
    }
    return { ...prod };
  }
  return apiRequest<Product>(`/products/${id}`);
}

export async function createProduct(payload: ProductCreate): Promise<Product> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    const newProduct: Product = {
      id: `prod-${Date.now()}`,
      owner_id: "user-vitrine-maker-1",
      name: payload.name,
      category: payload.category,
      description: payload.description,
      materials: payload.materials || [],
      style: payload.style || [],
      motifs: payload.motifs || [],
      colours: payload.colours || [],
      price_segment: payload.price_segment || "mid_premium",
      price_min: payload.price_min ?? null,
      price_max: payload.price_max ?? null,
      currency: payload.currency || "USD",
      moq: payload.moq || 1,
      monthly_capacity: payload.monthly_capacity ?? null,
      target_retailer_types: payload.target_retailer_types || [],
      images: payload.images || [],
      is_demo: payload.is_demo ?? true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mockProductsStore = [newProduct, ...mockProductsStore];
    return newProduct;
  }
  return apiRequest<Product>("/products", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateProduct(
  id: string,
  payload: ProductUpdate
): Promise<Product> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    const idx = mockProductsStore.findIndex((p) => p.id === id);
    if (idx === -1) {
      throw new Error(`Product not found: ${id}`);
    }
    const existing = mockProductsStore[idx];
    const updated: Product = {
      ...existing,
      name: payload.name ?? existing.name,
      category: payload.category ?? existing.category,
      description: payload.description ?? existing.description,
      materials: payload.materials !== undefined && payload.materials !== null ? payload.materials : existing.materials,
      style: payload.style !== undefined && payload.style !== null ? payload.style : existing.style,
      motifs: payload.motifs !== undefined && payload.motifs !== null ? payload.motifs : existing.motifs,
      colours: payload.colours !== undefined && payload.colours !== null ? payload.colours : existing.colours,
      price_segment: payload.price_segment ?? existing.price_segment,
      price_min: payload.price_min !== undefined ? payload.price_min : existing.price_min,
      price_max: payload.price_max !== undefined ? payload.price_max : existing.price_max,
      currency: payload.currency ?? existing.currency,
      moq: payload.moq ?? existing.moq,
      monthly_capacity: payload.monthly_capacity !== undefined ? payload.monthly_capacity : existing.monthly_capacity,
      target_retailer_types: payload.target_retailer_types !== undefined && payload.target_retailer_types !== null ? payload.target_retailer_types : existing.target_retailer_types,
      images: payload.images !== undefined && payload.images !== null ? payload.images : existing.images,
      updated_at: new Date().toISOString(),
    };
    mockProductsStore[idx] = updated;
    return updated;
  }
  return apiRequest<Product>(`/products/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteProduct(id: string): Promise<void> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    mockProductsStore = mockProductsStore.filter((p) => p.id !== id);
    return;
  }
  return apiRequest<void>(`/products/${id}`, {
    method: "DELETE",
  });
}

export async function uploadProductImage(
  id: string,
  file: File
): Promise<string[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    let localUrl = "/placeholder-product.png";
    try {
      if (typeof window !== "undefined" && file instanceof Blob) {
        localUrl = URL.createObjectURL(file);
      }
    } catch (e) {
      console.warn("Could not create object URL for mock product image:", e);
    }
    const prod = mockProductsStore.find((p) => p.id === id);
    if (prod) {
      prod.images = [...prod.images, localUrl];
      return prod.images;
    }
    return [localUrl];
  }
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<string[]>(`/products/${id}/images`, {
    method: "POST",
    body: formData,
  });
}

/**
 * AI Task A: Extract structured product attributes from descriptive text or artisan notes.
 * Field-by-field review required in UI; never silently saved.
 */
export async function extractProductProfile(
  payload: ExtractProfileRequest
): Promise<ProductAttributes> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 600)); // simulate AI generation time
    const text = payload.description.toLowerCase();

    const materials: string[] = [];
    if (text.includes("silk")) materials.push("Organic Mulberry Silk");
    if (text.includes("dye") || text.includes("madder")) materials.push("Plant Dyes (Madder & Weld)");
    if (text.includes("linen")) materials.push("Belgian Washed Linen");
    if (text.includes("cotton")) materials.push("Organic Cotton Voile");
    if (text.includes("wool") || text.includes("cashmere")) materials.push("Fine Merino Wool");
    if (text.includes("clay") || text.includes("ceramic") || text.includes("stoneware")) materials.push("Stoneware Clay");
    if (text.includes("leather")) materials.push("Vegetable-Tanned Leather");
    if (materials.length === 0) materials.push("Natural Artisan Fiber");

    const style: string[] = ["Handcrafted", "Tactile Heritage"];
    if (text.includes("minimal") || text.includes("clean")) style.push("Minimalist");
    if (text.includes("vintage") || text.includes("antique")) style.push("Archival Retro");
    if (text.includes("botanical") || text.includes("organic")) style.push("Botanical Luxury");

    return {
      style,
      materials,
      motifs: ["Organic Variation", "Artisanal Edge"],
      colours: ["Raw Ecru", "Earthy Mineral", "Botanical Plum"],
      price_segment: text.includes("luxury") ? "luxury" : "mid_premium",
      target_retailer_types: [
        "Independent Design Boutique",
        "Curated Lifestyle Concept Store",
        "Museum Design Store",
      ],
      uncertain_fields: ["price_min", "price_max", "moq"],
      assumptions: [
        "Assumed small-batch artisan handcraft model based on natural dye and fiber mentions.",
        "Assumed independent retail distribution rather than wholesale mass market.",
      ],
      category: text.includes("ceramic") || text.includes("pot")
        ? "Ceramics & Homeware"
        : text.includes("bag") || text.includes("tote")
        ? "Leather & Goods"
        : "Apparel & Accessories",
      price_min: 75,
      price_max: 150,
      currency: "USD",
      moq: 10,
      monthly_capacity: 100,
    };
  }
  return apiRequest<ProductAttributes>("/products/extract-profile", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
