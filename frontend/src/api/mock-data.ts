import type {
  Product,
  ResearchRun,
  TasteAnchor,
  MarketHypothesis,
  Lead,
  EvidenceItem,
  OutreachDraft,
  IntegrationStatusResponse,
  Profile,
} from "./types";

export const MOCK_PROFILE: Profile = {
  id: "prof-001",
  user_id: "user-vitrine-maker-1",
  business_name: "Atelier Solenne",
  country: "United Kingdom",
  website: "https://ateliersolenne.com",
  contact_email: "studio@ateliersolenne.com",
  about:
    "Independent London-based textile and craft studio producing botanical-dyed organic silks and bespoke woven garments in small batch runs.",
  created_at: "2026-09-01T10:00:00Z",
  updated_at: "2026-10-15T14:30:00Z",
};

export const MOCK_PRODUCTS: Product[] = [
  {
    id: "prod-001",
    owner_id: "user-vitrine-maker-1",
    name: "Botanical Plant-Dyed Habotai Silk Scarf",
    category: "Apparel & Accessories",
    description:
      "Hand-finished organic mulberry silk scarf kettle-dyed with madder root, logwood, and weld flowers. Each piece features subtle organic variegation and rolled hand-stitched hems.",
    materials: ["100% Mulberry Silk", "Madder Root Dye", "Weld Blossom", "Logwood Extract"],
    style: ["Minimalist", "Botanical Luxury", "Artisanal Heritage"],
    motifs: ["Floral Variegation", "Subtle Marbling"],
    colours: ["Madder Coral", "Earthy Plum", "Ochre Gold", "Soft Ecru"],
    price_segment: "mid_premium",
    price_min: 85.0,
    price_max: 140.0,
    currency: "USD",
    moq: 12,
    monthly_capacity: 150,
    target_retailer_types: [
      "Independent Design Boutique",
      "Museum Design Store",
      "Curated Lifestyle Concept Store",
    ],
    images: [
      "/images/vitrine-boutique-collection.webp",
      "/images/fashion-detail-textile.webp",
      "/images/fashion-detail-silhouette.webp",
    ],
    is_demo: true,
    created_at: "2026-10-10T09:30:00Z",
    updated_at: "2026-10-18T16:20:00Z",
  },
  {
    id: "prod-002",
    owner_id: "user-vitrine-maker-1",
    name: "Hand-Thrown Woodfired Stoneware Teapot",
    category: "Ceramics & Homeware",
    description:
      "Coarse stoneware teapot reduction-fired for 48 hours in a wood kiln. Features an unglazed iron-wash exterior and a smooth feldspathic interior glaze with hand-carved bamboo handle.",
    materials: ["Native Stoneware Clay", "Wood Ash Glaze", "Iron Oxide", "Steam-Bent Bamboo"],
    style: ["Wabi-Sabi", "Quiet Craft", "Functional Tableware"],
    motifs: ["Natural Ash Fly", "Unglazed Texture"],
    colours: ["Charcoal", "Warm Sand", "Ochre"],
    price_segment: "premium",
    price_min: 160.0,
    price_max: 220.0,
    currency: "USD",
    moq: 6,
    monthly_capacity: 40,
    target_retailer_types: [
      "Specialty Tea Merchant",
      "Contemporary Craft Gallery",
      "Design Homeware Boutique",
    ],
    images: ["/images/vitrine-boutique-collection.webp"],
    is_demo: true,
    created_at: "2026-10-14T11:00:00Z",
    updated_at: "2026-10-20T12:00:00Z",
  },
  {
    id: "prod-003",
    owner_id: "user-vitrine-maker-1",
    name: "Unstructured Vegetable-Tanned Daily Tote",
    category: "Leather & Goods",
    description:
      "Full-grain bridle leather tote cut from Tuscan vegetable-tanned hides. Solid brass saddle rivets, raw beveled edges, and internal lanyard pocket. Patinates with age.",
    materials: ["Full-Grain Tuscan Bridle Leather", "Solid Brass Hardware", "Beeswax Finish"],
    style: ["Utilitarian Luxury", "Architectural Simplicity"],
    motifs: ["Raw Edge", "Visible Saddle Stitch"],
    colours: ["Cognac Tan", "Espresso Black", "Olive Russet"],
    price_segment: "premium",
    price_min: 240.0,
    price_max: 310.0,
    currency: "USD",
    moq: 8,
    monthly_capacity: 60,
    target_retailer_types: [
      "Department Store Atelier Section",
      "Menswear & Goods Concept Shop",
      "Sustainable Goods Boutique",
    ],
    images: ["/images/fashion-detail-silhouette.webp"],
    is_demo: true,
    created_at: "2026-10-19T14:15:00Z",
    updated_at: "2026-10-22T10:45:00Z",
  },
];

export const MOCK_RUNS: ResearchRun[] = [
  {
    id: "run-001",
    owner_id: "user-vitrine-maker-1",
    product_id: "prod-001",
    status: "completed",
    stage: "done",
    inputs: {
      regions: ["United Kingdom", "France", "Japan"],
      retailer_types: [
        "Independent Design Boutique",
        "Museum Design Store",
        "Curated Lifestyle Concept Store",
      ],
      notes: "Focus on stockists carrying slow-fashion, botanical pigments, and artisan textiles.",
    },
    plan: {
      target_regions: ["United Kingdom", "France", "Japan"],
      target_retailer_types: ["Boutique", "Concept Store", "Gallery Shop"],
      aesthetic_candidates: ["Egg Trading", "Nose Shop Tokyo", "Toast UK", "Merci Paris"],
      search_queries: [
        "independent design boutique slow fashion botanical silk London",
        "curated artisan accessories store Paris Marais",
        "lifestyle concept store craft textiles Tokyo Daikanyama",
      ],
      hypotheses_rationale:
        "Independent lifestyle stockists bridging craft homeware and wearable textiles have higher margin elasticity and affinity for natural plant dyes.",
      notes: "Strict requirement for physical retail presence and verified buying directory.",
    },
    provider_modes: {
      taste: "live",
      search: "live",
      ai: "live",
    },
    started_at: "2026-10-21T08:00:00Z",
    finished_at: "2026-10-21T08:04:12Z",
    heartbeat_at: "2026-10-21T08:04:12Z",
    created_at: "2026-10-21T07:59:45Z",
  },
  {
    id: "run-002",
    owner_id: "user-vitrine-maker-1",
    product_id: "prod-001",
    status: "awaiting_review",
    stage: "anchor_review",
    inputs: {
      regions: ["United States - Northeast", "United States - Pacific NW"],
      retailer_types: ["Museum Design Store", "Contemporary Craft Gallery"],
      notes: "Targeting modern craft galleries and botanical concept spaces in Portland, Seattle, and Brooklyn.",
    },
    plan: {
      target_regions: ["Northeast US", "Pacific Northwest US"],
      target_retailer_types: ["Craft Gallery", "Boutique"],
      aesthetic_candidates: ["Makers Guild Seattle", "Object & Line Portland", "Consignment Brooklyn"],
      search_queries: [
        "independent contemporary craft gallery textiles Portland OR",
        "botanical natural dye clothing boutique Brooklyn NYC",
      ],
      hypotheses_rationale:
        "High regional preference for sustainable non-toxic dyes and transparent artisan provenance.",
      notes: "Verify stockist wholesale intake windows.",
    },
    provider_modes: {
      taste: "mock",
      search: "live",
      ai: "live",
    },
    started_at: "2026-10-24T18:00:00Z",
    finished_at: null,
    heartbeat_at: "2026-10-24T18:02:15Z",
    created_at: "2026-10-24T17:58:30Z",
  },
];

export const MOCK_ANCHORS: TasteAnchor[] = [
  {
    id: "anchor-001",
    run_id: "run-001",
    label: "Egg Trading London",
    entity_type: "brand",
    external_id: "qloo_ent_egg_trading",
    source: "ai_proposed",
    status: "confirmed",
    rationale:
      "Quintessential British slow-craft boutique curated by Maureen Doherty, focusing on tactile hand-loomed textiles, natural pigments, and understated luxury.",
    metadata: { city: "London", country: "United Kingdom" },
    is_demo: true,
  },
  {
    id: "anchor-002",
    run_id: "run-001",
    label: "Toast UK",
    entity_type: "brand",
    external_id: "qloo_ent_toast_uk",
    source: "ai_proposed",
    status: "confirmed",
    rationale:
      "Heritage lifestyle stockist celebrating thoughtful rhythm, traditional mending, and handcrafted natural fibers.",
    metadata: { city: "London", country: "United Kingdom" },
    is_demo: true,
  },
  {
    id: "anchor-003",
    run_id: "run-001",
    label: "Merci Paris",
    entity_type: "brand",
    external_id: "qloo_ent_merci_paris",
    source: "user_added",
    status: "confirmed",
    rationale:
      "Iconic Boulevard Beaumarchais concept store with dedicated artisan textile and botanical accessory sections.",
    metadata: { city: "Paris", country: "France" },
    is_demo: true,
  },
  {
    id: "anchor-004",
    run_id: "run-002",
    label: "Object & Line Portland",
    entity_type: "brand",
    external_id: null,
    source: "ai_proposed",
    status: "proposed",
    rationale:
      "Pacific Northwest concept studio showcasing Pacific Rim ceramics, organic textiles, and natural dyes.",
    metadata: { city: "Portland", region: "Oregon", country: "United States" },
    is_demo: true,
  },
  {
    id: "anchor-005",
    run_id: "run-002",
    label: "Makers Guild Seattle",
    entity_type: "brand",
    external_id: null,
    source: "ai_proposed",
    status: "proposed",
    rationale:
      "Curated guild representing contemporary North American handweavers and natural dye practitioners.",
    metadata: { city: "Seattle", region: "Washington", country: "United States" },
    is_demo: true,
  },
];

export const MOCK_HYPOTHESES: MarketHypothesis[] = [
  {
    id: "hyp-001",
    run_id: "run-001",
    title: "Slow-Craft & Botanical Pigment Retailers in London & Paris",
    rationale:
      "Retailers emphasizing sustainable fiber provenance have expanded floor allocation for small-batch silk scarves that complement unbleached linen silhouettes.",
    region_hint: "Western Europe",
    signals: [
      {
        type: "cultural_affinity",
        text: "Strong customer cross-affinity between independent ceramics, artisanal perfumery, and hand-dyed silks.",
        source: "qloo",
        source_ref: "affinity_vector_textiles_craft",
        is_demo: true,
      },
      {
        type: "retailer_catalog",
        text: "Average wholesale markup across targeted boutiques is 2.2x to 2.5x with typical opening orders of 8-15 units per SKU.",
        source: "tavily_web_extraction",
        source_ref: "https://eggtrading.com/about",
        is_demo: true,
      },
    ],
    status: "confirmed",
  },
];

export const MOCK_EVIDENCE: EvidenceItem[] = [
  {
    id: "ev-001",
    lead_id: "lead-001",
    url: "https://eggtrading.com/stockists-and-makers",
    excerpt:
      "We partner directly with weavers, dyers, and ceramicists who honor slow methods. All textiles in our Kinsman shop are made in limited batches with non-synthetic dyes.",
    source_type: "official_site",
    retrieved_at: "2026-10-21T08:02:10Z",
    published_at: "2026-06-15T00:00:00Z",
    domain_matches_lead: true,
    provenance: "verified_fact",
    is_demo: true,
  },
  {
    id: "ev-002",
    lead_id: "lead-001",
    url: "https://eggtrading.com/journal/botanical-dye-exhibition",
    excerpt:
      "In conversation with natural dye artisans: why madder and weld root provide an optical luminosity impossible to duplicate with petrochemical dyes.",
    source_type: "official_site",
    retrieved_at: "2026-10-21T08:02:40Z",
    published_at: "2026-04-10T00:00:00Z",
    domain_matches_lead: true,
    provenance: "verified_fact",
    is_demo: true,
  },
  {
    id: "ev-003",
    lead_id: "lead-002",
    url: "https://merci-merci.com/en/concept/artisan-makers",
    excerpt:
      "Merci supports independent creators worldwide. Our fashion floor curates accessories with tactile narrative and genuine artisanal pedigree.",
    source_type: "official_site",
    retrieved_at: "2026-10-21T08:03:05Z",
    published_at: "2026-01-20T00:00:00Z",
    domain_matches_lead: true,
    provenance: "verified_fact",
    is_demo: true,
  },
  {
    id: "ev-004",
    lead_id: "lead-003",
    url: "https://thebrokenarm.com/pages/designers",
    excerpt:
      "Selected contemporary labels and limited edition craft objects curated in Paris 3rd arrondissement.",
    source_type: "official_site",
    retrieved_at: "2026-10-21T08:03:25Z",
    published_at: "2025-11-05T00:00:00Z",
    domain_matches_lead: true,
    provenance: "verified_fact",
    is_demo: true,
  },
  {
    id: "ev-005",
    lead_id: "lead-004",
    url: "https://directory.craftcouncil.org.uk/stockists/artisan-loft-london",
    excerpt:
      "Artisan Loft operates a shared studio and retail space stocking small-run jewelry and botanical textiles.",
    source_type: "directory",
    retrieved_at: "2026-10-21T08:03:45Z",
    published_at: null,
    domain_matches_lead: false,
    provenance: "unknown",
    is_demo: true,
  },
];

export const MOCK_LEADS: Lead[] = [
  {
    id: "lead-001",
    run_id: "run-001",
    product_id: "prod-001",
    name: "Egg Trading London",
    website: "https://eggtrading.com",
    canonical_domain: "eggtrading.com",
    location: {
      city: "London",
      region: "Greater London",
      country: "United Kingdom",
    },
    retailer_type: "Independent Design Boutique",
    website_verified: true,
    website_checked_at: "2026-10-21T08:02:10Z",
    tier: "qualified",
    scores: {
      category_fit: 94.0,
      aesthetic_fit: 98.0,
      evidence_quality: 92.0,
      seller_compat: 90.0,
      overall: 95.0,
      completeness: 100.0,
      tier_reasons: [
        "Verified retail stockist with physical location at Kinnerton Street, London",
        "Active commitment to botanical and natural dyes explicitly documented on website",
        "Wholesale inventory aligns with silk accessory price points ($85 - $140)",
      ],
    },
    assessment: {
      category_fit: {
        label: "high",
        reasons: [
          "Curates slow-fashion scarves, shawls, and handmade garments",
          "Carries 10+ independent textile makers in small batches",
        ],
        evidence_ids: ["ev-001"],
      },
      aesthetic_fit: {
        label: "high",
        reasons: [
          "Shares an understated, organic color palette with botanical dye focus",
          "Dedicated editorial pieces on natural dyes and slow handcraft",
        ],
        evidence_ids: ["ev-002"],
      },
      seller_compat: {
        label: "high",
        reasons: [
          "Low minimum order quantity requirement fits Atelier Solenne's 12-unit batch model",
          "Direct buying team reachable via official studio address",
        ],
        evidence_ids: ["ev-001"],
      },
      summary:
        "Egg Trading is one of Europe's premier craft stockists with an exceptional aesthetic alignment with Atelier Solenne's botanical silks.",
      unknowns: [
        "Spring/Summer buying window cutoff date not publicly listed",
      ],
      model_id: "nemotron-70b-instruct",
      generated_at: "2026-10-21T08:03:00Z",
    },
    cultural_affinity: {
      provider: "qloo",
      is_demo: false,
      retrieved_at: "2026-10-21T08:02:30Z",
      anchor_ids: ["anchor-001"],
      signals: [
        {
          entity_name: "Egg Trading London",
          affinity_score: 0.94,
          correlated_categories: ["Handmade Ceramics", "Botanical Fragrance", "Textile Art"],
        },
      ],
    },
    review_status: "saved",
    notes: "High priority for Spring 2027 collection outreach. Reach out with tactile fabric swatch card.",
    duplicate_of: null,
    is_demo: true,
    created_at: "2026-10-21T08:02:10Z",
  },
  {
    id: "lead-002",
    run_id: "run-001",
    product_id: "prod-001",
    name: "Merci Paris",
    website: "https://merci-merci.com",
    canonical_domain: "merci-merci.com",
    location: {
      city: "Paris",
      region: "Île-de-France",
      country: "France",
    },
    retailer_type: "Curated Lifestyle Concept Store",
    website_verified: true,
    website_checked_at: "2026-10-21T08:03:05Z",
    tier: "qualified",
    scores: {
      category_fit: 88.0,
      aesthetic_fit: 86.0,
      evidence_quality: 89.0,
      seller_compat: 82.0,
      overall: 87.0,
      completeness: 100.0,
      tier_reasons: [
        "High international visibility and celebrated textile department",
        "Regularly hosts limited artisan trunk shows and maker capsules",
      ],
    },
    assessment: {
      category_fit: {
        label: "high",
        reasons: ["Extensive fashion accessories department with seasonal scarves"],
        evidence_ids: ["ev-003"],
      },
      aesthetic_fit: {
        label: "high",
        reasons: ["Curates high-end tactile crafts alongside contemporary design"],
        evidence_ids: ["ev-003"],
      },
      seller_compat: {
        label: "medium",
        reasons: ["Larger volume requirements may test small studio monthly capacity"],
        evidence_ids: [],
      },
      summary:
        "Merci represents a strong volume expansion partner with prominent Parisian foot traffic.",
      unknowns: ["May require 30-50 unit minimums per style"],
      model_id: "nemotron-70b-instruct",
      generated_at: "2026-10-21T08:03:20Z",
    },
    cultural_affinity: {
      provider: "qloo",
      is_demo: false,
      retrieved_at: "2026-10-21T08:02:50Z",
      anchor_ids: ["anchor-003"],
      signals: [
        {
          entity_name: "Merci Paris",
          affinity_score: 0.88,
          correlated_categories: ["Linen Bedding", "Artisan Tableware", "Curated Books"],
        },
      ],
    },
    review_status: "new",
    notes: null,
    duplicate_of: null,
    is_demo: true,
    created_at: "2026-10-21T08:03:05Z",
  },
  {
    id: "lead-003",
    run_id: "run-001",
    product_id: "prod-001",
    name: "The Broken Arm",
    website: "https://thebrokenarm.com",
    canonical_domain: "thebrokenarm.com",
    location: {
      city: "Paris",
      region: "Île-de-France",
      country: "France",
    },
    retailer_type: "Avant-Garde Boutique & Cafe",
    website_verified: true,
    website_checked_at: "2026-10-21T08:03:25Z",
    tier: "needs_review",
    scores: {
      category_fit: 70.0,
      aesthetic_fit: 60.0,
      evidence_quality: 75.0,
      seller_compat: 50.0,
      overall: 64.0,
      completeness: 85.0,
      tier_reasons: [
        "Carries luxury accessories but emphasizes runway and directional fashion over traditional botanicals",
      ],
    },
    assessment: {
      category_fit: {
        label: "medium",
        reasons: ["Stocks high-end scarves and wraps"],
        evidence_ids: ["ev-004"],
      },
      aesthetic_fit: {
        label: "medium",
        reasons: ["Aesthetic leans sharper and more architectural than rustic botanical"],
        evidence_ids: ["ev-004"],
      },
      seller_compat: {
        label: "low",
        reasons: ["High price ceiling ($300+) compared to entry product"],
        evidence_ids: [],
      },
      summary:
        "Borderline aesthetic alignment; may suit an elevated or limited capsule rather than primary line.",
      unknowns: ["Direct buyer contact details need verification"],
      model_id: "nemotron-70b-instruct",
      generated_at: "2026-10-21T08:03:35Z",
    },
    cultural_affinity: null,
    review_status: "new",
    notes: null,
    duplicate_of: null,
    is_demo: true,
    created_at: "2026-10-21T08:03:25Z",
  },
  {
    id: "lead-004",
    run_id: "run-001",
    product_id: "prod-001",
    name: "Artisan Loft London",
    website: "https://artisanloftlondon.co.uk",
    canonical_domain: "artisanloftlondon.co.uk",
    location: {
      city: "London",
      country: "United Kingdom",
    },
    retailer_type: "Shared Studio & Retail Space",
    website_verified: false,
    website_checked_at: "2026-10-21T08:03:45Z",
    tier: "unqualified",
    // CRITICAL: Unknown / missing evidence yields null scores, never zero
    scores: {
      category_fit: null,
      aesthetic_fit: null,
      evidence_quality: 30.0,
      seller_compat: null,
      overall: null,
      completeness: 20.0,
      tier_reasons: [
        "Official website inaccessible or offline during verification",
        "Insufficient retail evidence to establish commercial fit",
      ],
    },
    assessment: {
      category_fit: {
        label: "unknown",
        reasons: ["No active product catalog found"],
        evidence_ids: ["ev-005"],
      },
      aesthetic_fit: {
        label: "unknown",
        reasons: ["Unable to inspect current seasonal collection"],
        evidence_ids: [],
      },
      seller_compat: {
        label: "unknown",
        reasons: ["No buyer or wholesale policy on record"],
        evidence_ids: [],
      },
      summary: "Incomplete evidence due to unverified primary domain.",
      unknowns: [
        "Website DNS failed resolution",
        "Physical retail operations unconfirmed",
      ],
      model_id: "nemotron-70b-instruct",
      generated_at: "2026-10-21T08:03:55Z",
    },
    cultural_affinity: null,
    review_status: "rejected",
    notes: "Site offline; do not contact.",
    duplicate_of: null,
    is_demo: true,
    created_at: "2026-10-21T08:03:45Z",
  },
  {
    id: "lead-005",
    run_id: "run-001",
    product_id: "prod-001",
    name: "Egg Shop London (Secondary Annex)",
    website: "https://eggtrading.com/annex",
    canonical_domain: "eggtrading.com",
    location: {
      city: "London",
      country: "United Kingdom",
    },
    retailer_type: "Secondary Outlet",
    website_verified: true,
    website_checked_at: "2026-10-21T08:04:00Z",
    tier: "qualified",
    scores: {
      category_fit: 90.0,
      aesthetic_fit: 95.0,
      evidence_quality: 85.0,
      seller_compat: 90.0,
      overall: 92.0,
      completeness: 95.0,
      tier_reasons: ["Secondary location of Egg Trading primary lead"],
    },
    assessment: null,
    cultural_affinity: null,
    review_status: "new",
    notes: null,
    // Duplicate match reference (DECISION-D9)
    duplicate_of: "lead-001",
    is_demo: true,
    created_at: "2026-10-21T08:04:00Z",
  },
];

export const MOCK_OUTREACH_DRAFTS: OutreachDraft[] = [
  {
    id: "draft-001",
    owner_id: "user-vitrine-maker-1",
    lead_id: "lead-001",
    product_id: "prod-001",
    version: 1,
    subject: "Artisanal botanical silks for Egg Trading / Atelier Solenne",
    body: `Dear Maureen and the Buying Team at Egg Trading,

I have long admired your dedicated curation of tactile, slow-crafted textiles on Kinnerton Street. Your journal feature highlighting the depth of natural madder root resonated deeply with our studio's philosophy.

At Atelier Solenne, we produce limited-edition mulberry silk scarves kettle-dyed with raw botanical extracts—madder root, logwood, and wild weld flowers. Each piece is hand-rolled with hand-stitched hems in our London studio, creating organic shade variegation that complements Egg Trading's quiet, architectural silhouettes.

Our wholesale minimum is modest (12 units per order), allowing for curated assortment testing ahead of the upcoming season.

I would love to send a small fabric sample card and wholesale line sheet for your consideration.

Warm regards,

Elena Solenne
Founder & Dyer, Atelier Solenne
studio@ateliersolenne.com
https://ateliersolenne.com`,
    facts_used: [
      {
        fact_id: "ev-001",
        text: "Egg Trading curates slow-method textiles at Kinnerton Street shop",
        source_url: "https://eggtrading.com/stockists-and-makers",
      },
      {
        fact_id: "ev-002",
        text: "Editorial focus on madder and weld root natural plant dyes",
        source_url: "https://eggtrading.com/journal/botanical-dye-exhibition",
      },
      {
        fact_id: "prod-001-moq",
        text: "Atelier Solenne low minimum order quantity of 12 units",
        source_url: null,
      },
    ],
    warnings: [],
    status: "ready",
    followup_notes: "Sample card prepared with madder coral and ochre swatches.",
    parent_draft_id: null,
    is_demo: true,
    created_at: "2026-10-22T10:00:00Z",
    updated_at: "2026-10-22T14:15:00Z",
  },
  {
    id: "draft-002",
    owner_id: "user-vitrine-maker-1",
    lead_id: "lead-002",
    product_id: "prod-001",
    version: 1,
    subject: "Wholesale Inquiry: Botanical Silk Accessories for Merci Paris",
    body: `Hello to the Merci Buying Team,

Following your commitment to thoughtful maker narratives and curated artisanal accessories on Boulevard Beaumarchais, I am writing to introduce Atelier Solenne.

We handcraft small-batch mulberry silk scarves dyed exclusively with whole plant matter—madder root, weld, and logwood. The resulting palette carries subtle natural variations and an organic hand feel that aligns with Merci's lifestyle and home aesthetic.

Our studio accommodates initial wholesale orders from 12 to 50 pieces with dedicated lead times.

We would be delighted to share our Spring lookbook and wholesale terms.

Best regards,

Elena Solenne
Atelier Solenne
studio@ateliersolenne.com`,
    facts_used: [
      {
        fact_id: "ev-003",
        text: "Merci curates artisan makers and accessories on Boulevard Beaumarchais",
        source_url: "https://merci-merci.com/en/concept/artisan-makers",
      },
    ],
    warnings: [
      "Merci typically reviews seasonal collections 4 months in advance.",
    ],
    status: "draft",
    followup_notes: null,
    parent_draft_id: null,
    is_demo: true,
    created_at: "2026-10-23T11:30:00Z",
    updated_at: "2026-10-23T11:30:00Z",
  },
];

export const MOCK_INTEGRATION_STATUS: IntegrationStatusResponse = {
  nebius: "live",
  tavily: "live",
  qloo: "live",
};

