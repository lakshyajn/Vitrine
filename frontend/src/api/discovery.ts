import { apiRequest } from "./client";
import type {
  ResearchRun,
  CreateResearchRunRequest,
  TasteAnchor,
  CreateAnchorRequest,
  UpdateAnchorRequest,
  ConfirmAnchorsRequest,
  MarketHypothesis,
} from "./types";
import {
  MOCK_RUNS,
  MOCK_ANCHORS,
  MOCK_HYPOTHESES,
} from "./mock-data";

let mockRunsStore: ResearchRun[] = [...MOCK_RUNS];
let mockAnchorsStore: TasteAnchor[] = [...MOCK_ANCHORS];
const mockHypothesesStore: MarketHypothesis[] = [...MOCK_HYPOTHESES];

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export async function getResearchRuns(productId?: string): Promise<ResearchRun[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    if (productId) {
      return mockRunsStore.filter((r) => r.product_id === productId);
    }
    return [...mockRunsStore];
  }
  const query = productId ? `?product_id=${encodeURIComponent(productId)}` : "";
  return apiRequest<ResearchRun[]>(`/research-runs${query}`);
}

export async function getResearchRun(id: string): Promise<ResearchRun> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    const run = mockRunsStore.find((r) => r.id === id);
    if (!run) {
      throw new Error(`Research run not found: ${id}`);
    }
    return { ...run };
  }
  return apiRequest<ResearchRun>(`/research-runs/${id}`);
}

export async function createResearchRun(
  payload: CreateResearchRunRequest
): Promise<ResearchRun> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    const newRunId = `run-${Date.now()}`;
    const newRun: ResearchRun = {
      id: newRunId,
      owner_id: "user-vitrine-maker-1",
      product_id: payload.product_id,
      status: "awaiting_review", // transitions to awaiting_review with proposed anchors
      stage: "anchor_review",
      inputs: payload.inputs,
      plan: {
        target_regions: payload.inputs.regions,
        target_retailer_types: payload.inputs.retailer_types,
        aesthetic_candidates: ["Boutique Studio", "Curated Concept Shop"],
        search_queries: payload.inputs.regions.map(
          (reg) => `independent boutique artisanal natural dye ${reg}`
        ),
        hypotheses_rationale: "Synthesized regional maker ecosystem hypotheses.",
        notes: payload.inputs.notes || null,
      },
      provider_modes: {
        taste: "live",
        search: "live",
        ai: "live",
      },
      started_at: new Date().toISOString(),
      finished_at: null,
      heartbeat_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };

    // Automatically seed proposed anchors for this new run
    const proposedAnchors: TasteAnchor[] = [
      {
        id: `anchor-${Date.now()}-1`,
        run_id: newRunId,
        label: "Toast Workshop & Stockists",
        entity_type: "brand",
        external_id: "qloo_ent_toast_sample",
        source: "ai_proposed",
        status: "proposed",
        rationale: "High affinity match with natural pigments and woven fiber craftsmanship.",
        metadata: { region: payload.inputs.regions[0] || "UK" },
        is_demo: true,
      },
      {
        id: `anchor-${Date.now()}-2`,
        run_id: newRunId,
        label: "Nose Shop Craft Concept",
        entity_type: "brand",
        external_id: "qloo_ent_noseshop",
        source: "ai_proposed",
        status: "proposed",
        rationale: "Lifestyle stockist bridging botanical extracts with modern design.",
        metadata: { region: payload.inputs.regions[1] || "Japan" },
        is_demo: true,
      },
    ];

    mockRunsStore = [newRun, ...mockRunsStore];
    mockAnchorsStore = [...mockAnchorsStore, ...proposedAnchors];
    return newRun;
  }
  return apiRequest<ResearchRun>("/research-runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function rerunResearchRun(id: string): Promise<ResearchRun> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    const run = mockRunsStore.find((r) => r.id === id);
    if (!run) throw new Error("Run not found");
    const updated: ResearchRun = {
      ...run,
      status: "completed",
      stage: "done",
      finished_at: new Date().toISOString(),
      heartbeat_at: new Date().toISOString(),
    };
    mockRunsStore = mockRunsStore.map((r) => (r.id === id ? updated : r));
    return updated;
  }
  return apiRequest<ResearchRun>(`/research-runs/${id}/rerun`, {
    method: "POST",
  });
}

export async function getAnchors(runId: string): Promise<TasteAnchor[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    return mockAnchorsStore.filter((a) => a.run_id === runId);
  }
  return apiRequest<TasteAnchor[]>(`/research-runs/${runId}/anchors`);
}

export async function createAnchor(
  runId: string,
  payload: CreateAnchorRequest
): Promise<TasteAnchor> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    const newAnchor: TasteAnchor = {
      id: `anchor-${Date.now()}`,
      run_id: runId,
      label: payload.label,
      entity_type: payload.entity_type || "brand",
      external_id: null,
      source: "user_added",
      status: "confirmed",
      rationale: payload.rationale || "User-added brand reference",
      metadata: {},
      is_demo: false,
    };
    mockAnchorsStore = [...mockAnchorsStore, newAnchor];
    return newAnchor;
  }
  return apiRequest<TasteAnchor>(`/research-runs/${runId}/anchors`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAnchor(
  anchorId: string,
  payload: UpdateAnchorRequest
): Promise<TasteAnchor> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150));
    const idx = mockAnchorsStore.findIndex((a) => a.id === anchorId);
    if (idx === -1) throw new Error("Anchor not found");
    const updated: TasteAnchor = {
      ...mockAnchorsStore[idx],
      label: payload.label ?? mockAnchorsStore[idx].label,
      entity_type: payload.entity_type ?? mockAnchorsStore[idx].entity_type,
      status: payload.status ?? mockAnchorsStore[idx].status,
      rationale: payload.rationale !== undefined ? payload.rationale : mockAnchorsStore[idx].rationale,
    };
    mockAnchorsStore[idx] = updated;
    return updated;
  }
  return apiRequest<TasteAnchor>(`/taste-anchors/${anchorId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function confirmAnchors(
  runId: string,
  payload: ConfirmAnchorsRequest = { proceed_without_anchors: false }
): Promise<{ id: string; status: string }> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    const runIdx = mockRunsStore.findIndex((r) => r.id === runId);
    if (runIdx !== -1) {
      mockRunsStore[runIdx] = {
        ...mockRunsStore[runIdx],
        status: "completed",
        stage: "done",
        finished_at: new Date().toISOString(),
      };
    }
    return { id: runId, status: "completed" };
  }
  return apiRequest<{ id: string; status: string }>(
    `/research-runs/${runId}/confirm-anchors`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function getHypotheses(runId: string): Promise<MarketHypothesis[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 100));
    return mockHypothesesStore.filter((h) => h.run_id === runId);
  }
  return apiRequest<MarketHypothesis[]>(`/research-runs/${runId}/hypotheses`);
}

