import { apiRequest } from "./client";
import type {
  Lead,
  LeadPagedResponse,
  UpdateLeadRequest,
  ContactScrapeResult,
  EvidenceItem,
} from "./types";
import { MOCK_LEADS, MOCK_EVIDENCE } from "./mock-data";

const mockLeadsStore: Lead[] = [...MOCK_LEADS];
const mockEvidenceStore: EvidenceItem[] = [...MOCK_EVIDENCE];

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export interface GetLeadsParams {
  product_id?: string;
  run_id?: string;
  tier?: string;
  review_status?: string;
  min_score?: number;
  location?: string;
  q?: string;
  sort?: "score_desc" | "name" | "newest" | string;
  page?: number;
  page_size?: number;
}

export async function getLeads(
  params: GetLeadsParams = {}
): Promise<LeadPagedResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    let filtered = [...mockLeadsStore];

    if (params.product_id) {
      filtered = filtered.filter((l) => l.product_id === params.product_id);
    }
    if (params.run_id) {
      filtered = filtered.filter((l) => l.run_id === params.run_id);
    }
    if (params.tier && params.tier !== "all") {
      filtered = filtered.filter((l) => l.tier === params.tier);
    }
    if (params.review_status && params.review_status !== "all") {
      filtered = filtered.filter((l) => l.review_status === params.review_status);
    }
    if (params.min_score !== undefined && params.min_score !== null) {
      // Per DECISION-D7: When min_score is specified, leads with overall == null are excluded
      filtered = filtered.filter(
        (l) => l.scores.overall !== null && l.scores.overall >= (params.min_score as number)
      );
    }
    if (params.location) {
      const loc = params.location.toLowerCase();
      filtered = filtered.filter(
        (l) =>
          l.location?.city?.toLowerCase().includes(loc) ||
          l.location?.country?.toLowerCase().includes(loc)
      );
    }
    if (params.q) {
      const q = params.q.toLowerCase();
      filtered = filtered.filter(
        (l) =>
          l.name.toLowerCase().includes(q) ||
          l.canonical_domain.toLowerCase().includes(q) ||
          l.retailer_type.toLowerCase().includes(q)
      );
    }

    // Sort: score_desc, name, newest
    if (params.sort === "name") {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    } else if (params.sort === "newest") {
      filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else {
      // default score_desc
      filtered.sort((a, b) => (b.scores.overall ?? -1) - (a.scores.overall ?? -1));
    }

    const page = params.page || 1;
    const pageSize = params.page_size || 10;
    const start = (page - 1) * pageSize;
    const items = filtered.slice(start, start + pageSize);

    return {
      items,
      total: filtered.length,
      page,
      page_size: pageSize,
    };
  }

  const query = new URLSearchParams();
  if (params.product_id) query.set("product_id", params.product_id);
  if (params.run_id) query.set("run_id", params.run_id);
  if (params.tier && params.tier !== "all") query.set("tier", params.tier);
  if (params.review_status && params.review_status !== "all") query.set("review_status", params.review_status);
  if (params.min_score !== undefined) query.set("min_score", String(params.min_score));
  if (params.location) query.set("location", params.location);
  if (params.q) query.set("q", params.q);
  if (params.sort) query.set("sort", params.sort);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));

  const qs = query.toString();
  return apiRequest<LeadPagedResponse>(`/leads${qs ? `?${qs}` : ""}`);
}

export async function getLead(id: string): Promise<Lead> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    const lead = mockLeadsStore.find((l) => l.id === id);
    if (!lead) throw new Error(`Lead not found: ${id}`);
    return { ...lead };
  }
  return apiRequest<Lead>(`/leads/${id}`);
}

export async function updateLead(
  id: string,
  payload: UpdateLeadRequest
): Promise<Lead> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    const idx = mockLeadsStore.findIndex((l) => l.id === id);
    if (idx === -1) throw new Error(`Lead not found: ${id}`);
    const updated: Lead = {
      ...mockLeadsStore[idx],
      review_status: payload.review_status ?? mockLeadsStore[idx].review_status,
      notes: payload.notes !== undefined ? payload.notes : mockLeadsStore[idx].notes,
    };
    mockLeadsStore[idx] = updated;
    return updated;
  }
  return apiRequest<Lead>(`/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getLeadEvidence(id: string): Promise<EvidenceItem[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    return mockEvidenceStore.filter((e) => e.lead_id === id);
  }
  return apiRequest<EvidenceItem[]>(`/leads/${id}/evidence`);
}


export async function scrapeLeadContact(id: string): Promise<ContactScrapeResult> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400));
    const lead = mockLeadsStore.find((l) => l.id === id);
    const email = lead?.contact_email || (lead ? `contact@${lead.canonical_domain}` : "wholesale@unknown.com");
    if (lead) {
      lead.contact_email = email;
    }
    return {
      lead_id: id,
      email,
      source: "tavily_scraped",
      source_url: lead?.website || null,
      is_fallback: false,
      confidence: 0.95,
      all_candidates: [email],
    };
  }
  return apiRequest<ContactScrapeResult>(`/leads/${id}/scrape-contact`, {
    method: "POST",
  });
}
