import { apiRequest } from "./client";
import type {
  OutreachDraft,
  UpdateOutreachDraftRequest,
} from "./types";
import { MOCK_OUTREACH_DRAFTS, MOCK_LEADS, MOCK_PRODUCTS } from "./mock-data";
import { updateLead } from "./leads";

let mockDraftsStore: OutreachDraft[] = [...MOCK_OUTREACH_DRAFTS];

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export interface GetOutreachDraftsParams {
  status?: string;
  product_id?: string;
  lead_id?: string;
}

export async function getOutreachDrafts(
  params: GetOutreachDraftsParams = {}
): Promise<OutreachDraft[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    let filtered = [...mockDraftsStore];
    if (params.status && params.status !== "all") {
      filtered = filtered.filter((d) => d.status === params.status);
    }
    if (params.product_id) {
      filtered = filtered.filter((d) => d.product_id === params.product_id);
    }
    if (params.lead_id) {
      filtered = filtered.filter((d) => d.lead_id === params.lead_id);
    }
    filtered.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    return filtered;
  }
  const query = new URLSearchParams();
  if (params.status && params.status !== "all") query.set("status", params.status);
  if (params.product_id) query.set("product_id", params.product_id);
  if (params.lead_id) query.set("lead_id", params.lead_id);
  const qs = query.toString();
  return apiRequest<OutreachDraft[]>(`/outreach-drafts${qs ? `?${qs}` : ""}`);
}

export async function getLeadOutreachDrafts(leadId: string): Promise<OutreachDraft[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    return mockDraftsStore.filter((d) => d.lead_id === leadId);
  }
  return apiRequest<OutreachDraft[]>(`/leads/${leadId}/outreach-drafts`);
}

export async function getOutreachDraft(id: string): Promise<OutreachDraft> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    const draft = mockDraftsStore.find((d) => d.id === id);
    if (!draft) throw new Error(`Outreach draft not found: ${id}`);
    return { ...draft };
  }
  return apiRequest<OutreachDraft>(`/outreach-drafts/${id}`);
}

export async function generateOutreachDraft(leadId: string): Promise<OutreachDraft> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 500));
    const lead = MOCK_LEADS.find((l) => l.id === leadId);
    const prod = MOCK_PRODUCTS.find((p) => p.id === lead?.product_id) || MOCK_PRODUCTS[0];

    const newDraft: OutreachDraft = {
      id: `draft-${Date.now()}`,
      owner_id: "user-vitrine-maker-1",
      lead_id: leadId,
      product_id: prod.id,
      version: 1,
      subject: `Artisanal craft inquiry: ${prod.name} for ${lead?.name || "Your Store"}`,
      body: `Hello ${lead?.name || "Buying Team"},

We have been following your curated work in ${lead?.location?.city || "your boutique"} with admiration.

At Atelier Solenne, we specialize in small-batch ${prod.name.toLowerCase()}, handcrafted using natural botanical dyes and time-honored weaving techniques.

Given your emphasis on thoughtful craftsmanship, we would love to share our line sheet and wholesale terms (minimum opening order: ${prod.moq} units).

Warm regards,

Elena Solenne
Atelier Solenne
studio@ateliersolenne.com`,
      facts_used: [
        {
          fact_id: "lead-loc",
          text: `Retail presence in ${lead?.location?.city || "boutique location"}`,
          source_url: lead?.website,
        },
        {
          fact_id: "prod-moq",
          text: `Minimum order quantity: ${prod.moq} units`,
          source_url: null,
        },
      ],
      warnings: [],
      status: "draft",
      followup_notes: null,
      parent_draft_id: null,
      is_demo: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockDraftsStore = [newDraft, ...mockDraftsStore];
    return newDraft;
  }
  return apiRequest<OutreachDraft>(`/leads/${leadId}/outreach-drafts`, {
    method: "POST",
  });
}

export async function updateOutreachDraft(
  id: string,
  payload: UpdateOutreachDraftRequest
): Promise<OutreachDraft> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    const idx = mockDraftsStore.findIndex((d) => d.id === id);
    if (idx === -1) throw new Error(`Outreach draft not found: ${id}`);

    const existing = mockDraftsStore[idx];
    const updated: OutreachDraft = {
      ...existing,
      subject: payload.subject !== undefined && payload.subject !== null ? payload.subject : existing.subject,
      body: payload.body !== undefined && payload.body !== null ? payload.body : existing.body,
      status: payload.status !== undefined && payload.status !== null ? payload.status : existing.status,
      followup_notes:
        payload.followup_notes !== undefined ? payload.followup_notes : existing.followup_notes,
      updated_at: new Date().toISOString(),
    };
    mockDraftsStore[idx] = updated;

    // DECISION-D11: When updated to "contacted", atomically update parent lead's review_status to "contacted"
    if (payload.status === "contacted" && existing.lead_id) {
      try {
        await updateLead(existing.lead_id, { review_status: "contacted" });
      } catch {
        // ignore in mock if lead not found
      }
    }

    return updated;
  }
  return apiRequest<OutreachDraft>(`/outreach-drafts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function regenerateOutreachDraft(id: string): Promise<OutreachDraft> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 500));
    const existing = mockDraftsStore.find((d) => d.id === id);
    if (!existing) throw new Error("Draft not found");
    const regenerated: OutreachDraft = {
      ...existing,
      id: `draft-${Date.now()}`,
      version: existing.version + 1,
      parent_draft_id: existing.id,
      subject: `Revised inquiry: Atelier Solenne bespoke collection for ${existing.lead_id}`,
      updated_at: new Date().toISOString(),
    };
    mockDraftsStore = [regenerated, ...mockDraftsStore];
    return regenerated;
  }
  return apiRequest<OutreachDraft>(`/outreach-drafts/${id}/regenerate`, {
    method: "POST",
  });
}

