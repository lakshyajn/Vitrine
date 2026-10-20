-- ==============================================================================
-- Migration 001: Initial Schema (Contract v0.2)
-- PostgreSQL DDL for all core tables with UUIDs, timestamps, checks, and RLS.
-- ==============================================================================

-- Enable pgcrypto for gen_random_uuid() if not already available
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. profiles
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    business_name TEXT NOT NULL,
    country TEXT,
    website TEXT,
    contact_email TEXT,
    about TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own profile" ON profiles;
CREATE POLICY "Users can manage their own profile"
    ON profiles
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 2. products
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    materials JSONB NOT NULL DEFAULT '[]'::jsonb,
    style JSONB NOT NULL DEFAULT '[]'::jsonb,
    motifs JSONB NOT NULL DEFAULT '[]'::jsonb,
    colours JSONB NOT NULL DEFAULT '[]'::jsonb,
    price_segment TEXT NOT NULL DEFAULT 'mid_premium',
    price_min NUMERIC,
    price_max NUMERIC,
    currency TEXT NOT NULL DEFAULT 'USD',
    moq INTEGER NOT NULL DEFAULT 1,
    monthly_capacity INTEGER,
    target_retailer_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_demo BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_products_price CHECK (price_min IS NULL OR price_max IS NULL OR price_min <= price_max),
    CONSTRAINT chk_products_moq CHECK (moq >= 1)
);

CREATE INDEX IF NOT EXISTS idx_products_owner_id ON products(owner_id);

ALTER TABLE products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own products" ON products;
CREATE POLICY "Users can manage their own products"
    ON products
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 3. research_runs
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued',
    stage TEXT NOT NULL DEFAULT 'planning',
    inputs JSONB NOT NULL DEFAULT '{}'::jsonb,
    plan JSONB,
    provider_modes JSONB NOT NULL DEFAULT '{"taste": "mock", "search": "mock", "ai": "mock"}'::jsonb,
    error JSONB,
    idempotency_key TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    heartbeat_at TIMESTAMPTZ,
    active_elapsed_seconds INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_runs_owner_product ON research_runs(owner_id, product_id);
CREATE INDEX IF NOT EXISTS idx_research_runs_status ON research_runs(status);

ALTER TABLE research_runs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own research runs" ON research_runs;
CREATE POLICY "Users can manage their own research runs"
    ON research_runs
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 4. taste_anchors
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS taste_anchors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    run_id UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'brand',
    external_id TEXT,
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    rationale TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_demo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_taste_anchors_run_id ON taste_anchors(run_id);

ALTER TABLE taste_anchors ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own taste anchors" ON taste_anchors;
CREATE POLICY "Users can manage their own taste anchors"
    ON taste_anchors
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 5. market_hypotheses
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_hypotheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    run_id UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    rationale TEXT,
    region_hint TEXT,
    signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'proposed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_market_hypotheses_run_id ON market_hypotheses(run_id);

ALTER TABLE market_hypotheses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own market hypotheses" ON market_hypotheses;
CREATE POLICY "Users can manage their own market hypotheses"
    ON market_hypotheses
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 6. leads
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    run_id UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    website TEXT NOT NULL,
    canonical_domain TEXT NOT NULL,
    location JSONB,
    retailer_type TEXT NOT NULL DEFAULT 'boutique',
    website_verified BOOLEAN NOT NULL DEFAULT false,
    website_checked_at TIMESTAMPTZ,
    tier TEXT NOT NULL DEFAULT 'needs_review',
    scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    assessment JSONB,
    cultural_affinity JSONB,
    review_status TEXT NOT NULL DEFAULT 'new',
    notes TEXT,
    duplicate_of UUID REFERENCES leads(id) ON DELETE SET NULL,
    is_demo BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_leads_owner_product_domain UNIQUE (owner_id, product_id, canonical_domain)
);

CREATE INDEX IF NOT EXISTS idx_leads_owner_product ON leads(owner_id, product_id);
CREATE INDEX IF NOT EXISTS idx_leads_run_id ON leads(run_id);
CREATE INDEX IF NOT EXISTS idx_leads_review_status ON leads(review_status);
CREATE INDEX IF NOT EXISTS idx_leads_tier ON leads(tier);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own leads" ON leads;
CREATE POLICY "Users can manage their own leads"
    ON leads
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 7. lead_evidence
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lead_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'official_site',
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    domain_matches_lead BOOLEAN NOT NULL DEFAULT true,
    provenance TEXT NOT NULL DEFAULT 'verified_fact',
    is_demo BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lead_evidence_lead_id ON lead_evidence(lead_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_lead_evidence_lead_url_excerpt ON lead_evidence (lead_id, url, md5(excerpt));

ALTER TABLE lead_evidence ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own lead evidence" ON lead_evidence;
CREATE POLICY "Users can manage their own lead evidence"
    ON lead_evidence
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 8. outreach_drafts
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outreach_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    facts_used JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    followup_notes TEXT,
    parent_draft_id UUID REFERENCES outreach_drafts(id) ON DELETE SET NULL,
    is_demo BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_outreach_drafts_lead_version UNIQUE (lead_id, version)
);

CREATE INDEX IF NOT EXISTS idx_outreach_drafts_lead_id ON outreach_drafts(lead_id);
CREATE INDEX IF NOT EXISTS idx_outreach_drafts_owner_product ON outreach_drafts(owner_id, product_id);

ALTER TABLE outreach_drafts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their own outreach drafts" ON outreach_drafts;
CREATE POLICY "Users can manage their own outreach drafts"
    ON outreach_drafts
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 9. provider_calls (WS2 Section 7.2)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    run_id UUID REFERENCES research_runs(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    cache_key TEXT,
    status TEXT NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    response JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_provider_calls_lookup ON provider_calls(provider, endpoint, cache_key);
CREATE INDEX IF NOT EXISTS idx_provider_calls_run_id ON provider_calls(run_id);

ALTER TABLE provider_calls ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own provider calls" ON provider_calls;
CREATE POLICY "Users can view their own provider calls"
    ON provider_calls
    FOR ALL
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- ------------------------------------------------------------------------------
-- 10. ai_call_logs
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID,
    run_id UUID REFERENCES research_runs(id) ON DELETE SET NULL,
    task TEXT NOT NULL,
    model_id TEXT NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    validation_ok BOOLEAN NOT NULL DEFAULT true,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_call_logs_run_id ON ai_call_logs(run_id);

ALTER TABLE ai_call_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own AI logs" ON ai_call_logs;
CREATE POLICY "Users can view their own AI logs"
    ON ai_call_logs
    FOR ALL
    USING (owner_id IS NULL OR owner_id = auth.uid())
    WITH CHECK (owner_id IS NULL OR owner_id = auth.uid());
