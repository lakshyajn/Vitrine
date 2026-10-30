/**
 * Authoritative TypeScript wire types matching contracts/schemas.py and openapi.json.
 * All fields use snake_case.
 */

export type PriceSegment =
  | "budget"
  | "mid"
  | "mid_premium"
  | "premium"
  | "luxury";

export type ResearchRunStatus =
  | "queued"
  | "running"
  | "awaiting_review"
  | "completed"
  | "failed";

export type ResearchRunStage =
  | "planning"
  | "anchor_proposal"
  | "anchor_review"
  | "discovery"
  | "assessment"
  | "scoring"
  | "done";

export type LeadReviewStatus = "new" | "saved" | "rejected" | "contacted";

export type LeadTier = "qualified" | "needs_review" | "unqualified";

export type OutreachDraftStatus = "draft" | "ready" | "contacted";

export type TasteAnchorStatus = "proposed" | "confirmed" | "rejected";

export type TasteAnchorSource = "ai_proposed" | "user_added" | "qloo" | "demo";

export type MarketHypothesisStatus = "proposed" | "confirmed" | "rejected";

export type DimensionLabel = "high" | "medium" | "low" | "unknown";

export type EvidenceSourceType =
  | "official_site"
  | "product_page"
  | "social"
  | "directory"
  | "press"
  | "marketplace"
  | "other";

export type ProvenanceTag =
  | "verified_fact"
  | "ai_assessment"
  | "unknown"
  | "demo_data";

export type IntegrationState = "live" | "mock" | "pending" | "disabled";

export interface Profile {
  id: string;
  user_id: string;
  business_name: string;
  country: string | null;
  website: string | null;
  contact_email: string | null;
  about: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdate {
  business_name?: string | null;
  country?: string | null;
  website?: string | null;
  contact_email?: string | null;
  about?: string | null;
}

export interface Product {
  id: string;
  owner_id?: string;
  name: string;
  category: string;
  description: string;
  materials: string[];
  style: string[];
  motifs: string[];
  colours: string[];
  price_segment: PriceSegment;
  price_min: number | null;
  price_max: number | null;
  currency: string;
  moq: number;
  monthly_capacity: number | null;
  target_retailer_types: string[];
  images: string[];
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  category: string;
  description: string;
  materials?: string[];
  style?: string[];
  motifs?: string[];
  colours?: string[];
  price_segment?: PriceSegment;
  price_min?: number | null;
  price_max?: number | null;
  currency?: string;
  moq?: number;
  monthly_capacity?: number | null;
  target_retailer_types?: string[];
  images?: string[];
  is_demo?: boolean;
}

export interface ProductUpdate {
  name?: string | null;
  category?: string | null;
  description?: string | null;
  materials?: string[] | null;
  style?: string[] | null;
  motifs?: string[] | null;
  colours?: string[] | null;
  price_segment?: PriceSegment | null;
  price_min?: number | null;
  price_max?: number | null;
  currency?: string | null;
  moq?: number | null;
  monthly_capacity?: number | null;
  target_retailer_types?: string[] | null;
  images?: string[] | null;
  is_demo?: boolean | null;
}

export interface ProductAttributes {
  style: string[];
  materials: string[];
  motifs: string[];
  colours: string[];
  price_segment: PriceSegment | null;
  target_retailer_types: string[];
  uncertain_fields: string[];
  assumptions: string[];
  category?: string | null;
  price_min?: number | null;
  price_max?: number | null;
  currency?: string | null;
  moq?: number | null;
  monthly_capacity?: number | null;
}

export interface ExtractProfileRequest {
  description: string;
  known?: Partial<ProductCreate> | null;
}

export interface ResearchPlan {
  target_regions: string[];
  target_retailer_types: string[];
  aesthetic_candidates: string[];
  search_queries: string[];
  hypotheses_rationale: string | null;
  notes: string | null;
}

export interface ResearchRunInputs {
  regions: string[];
  retailer_types: string[];
  notes?: string | null;
  anchor_ids?: string[];
}

export interface ProviderModes {
  taste: IntegrationState;
  search: IntegrationState;
  ai: IntegrationState;
}

export interface RunError {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ResearchRun {
  id: string;
  owner_id?: string | null;
  product_id: string;
  status: ResearchRunStatus;
  stage: ResearchRunStage;
  inputs: ResearchRunInputs;
  plan?: ResearchPlan | null;
  error?: RunError | null;
  provider_modes: ProviderModes;
  started_at: string | null;
  finished_at: string | null;
  heartbeat_at: string | null;
  created_at: string;
}

export interface CreateResearchRunRequest {
  product_id: string;
  inputs: ResearchRunInputs;
}

export interface TasteAnchor {
  id: string;
  owner_id?: string | null;
  run_id: string;
  label: string;
  entity_type: string;
  external_id?: string | null;
  source: TasteAnchorSource;
  status: TasteAnchorStatus;
  rationale?: string | null;
  metadata?: Record<string, unknown>;
  is_demo: boolean;
}

export interface CreateAnchorRequest {
  label: string;
  entity_type?: string;
  rationale?: string | null;
}

export interface UpdateAnchorRequest {
  label?: string | null;
  entity_type?: string | null;
  status?: TasteAnchorStatus | null;
  rationale?: string | null;
}

export interface ConfirmAnchorsRequest {
  proceed_without_anchors?: boolean;
}

export interface HypothesisSignal {
  type: string;
  text: string;
  source: string;
  source_ref?: string | null;
  is_demo: boolean;
}

export interface MarketHypothesis {
  id: string;
  owner_id?: string | null;
  run_id: string;
  title: string;
  rationale?: string | null;
  region_hint?: string | null;
  signals: HypothesisSignal[];
  status: MarketHypothesisStatus;
}

export interface CulturalAffinity {
  provider: string;
  is_demo: boolean;
  retrieved_at: string;
  anchor_ids: string[];
  signals: Record<string, unknown>[];
}

export interface LeadLocation {
  city?: string | null;
  region?: string | null;
  country?: string | null;
}

export interface LeadScores {
  category_fit: number | null;
  aesthetic_fit: number | null;
  evidence_quality: number | null;
  seller_compat: number | null;
  overall: number | null;
  completeness: number | null;
  tier_reasons: string[];
}

export interface DimensionAssessment {
  label: DimensionLabel;
  reasons: string[];
  evidence_ids: string[];
}

export interface LeadAssessment {
  category_fit: DimensionAssessment;
  aesthetic_fit: DimensionAssessment;
  seller_compat: DimensionAssessment;
  summary: string;
  unknowns: string[];
  model_id?: string | null;
  generated_at: string;
}

export interface EvidenceItem {
  id: string;
  owner_id?: string | null;
  lead_id: string;
  url: string;
  excerpt: string;
  source_type: EvidenceSourceType;
  retrieved_at: string;
  published_at?: string | null;
  domain_matches_lead: boolean;
  provenance: ProvenanceTag;
  is_demo: boolean;
}

export type RetailerKind =
  | "retailer"
  | "maker_brand"
  | "marketplace"
  | "media_reference"
  | "institution"
  | "other"
  | "unknown";

export interface Lead {
  id: string;
  owner_id?: string | null;
  run_id: string;
  product_id: string;
  name: string;
  website: string;
  canonical_domain: string;
  location?: LeadLocation | null;
  retailer_type?: string | null;
  retailer_kind?: RetailerKind | null;
  website_verified: boolean;
  website_checked_at?: string | null;
  tier: LeadTier;
  scores: LeadScores;
  assessment?: LeadAssessment | null;
  cultural_affinity?: CulturalAffinity | null;
  review_status: LeadReviewStatus;
  notes?: string | null;
  duplicate_of?: string | null;
  contact_email?: string | null;
  is_demo: boolean;
  created_at: string;
}

export interface LeadPagedResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export interface UpdateLeadRequest {
  review_status?: LeadReviewStatus | null;
  notes?: string | null;
  contact_email?: string | null;
}

export interface ContactScrapeResult {
  lead_id: string;
  email: string;
  source: string;
  source_url?: string | null;
  is_fallback: boolean;
  confidence: number;
  all_candidates: string[];
}

export interface FactUsed {
  fact_id: string;
  text: string;
  source_url?: string | null;
}

export interface OutreachDraft {
  id: string;
  owner_id?: string | null;
  lead_id: string;
  product_id: string;
  version: number;
  subject: string;
  body: string;
  facts_used: FactUsed[];
  warnings: string[];
  status: OutreachDraftStatus;
  followup_notes?: string | null;
  parent_draft_id?: string | null;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateOutreachDraftRequest {
  subject?: string | null;
  body?: string | null;
  status?: OutreachDraftStatus | null;
  followup_notes?: string | null;
}

export interface IntegrationStatusResponse {
  nebius?: IntegrationState;
  tavily?: IntegrationState;
  qloo?: IntegrationState;
  [key: string]: IntegrationState | undefined;
}

export interface DemoSeedSummary {
  products_seeded: number;
  leads_seeded: number;
  runs_seeded: number;
  drafts_seeded: number;
}
