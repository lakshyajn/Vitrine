# Vitrine: Project Submission & Technical Dossier

> **Core Capability:** Boutique stockist discovery, cultural taste evaluation, and wholesale outreach preparation for craft studios and physical product brands.  
> **Architecture & Stack:** **Qloo Taste Graph API** (cultural taste & consumer affinity) &bull; **Dual NVIDIA Nemotron Models on Nebius Token Factory** (550B Ultra &amp; 120B Super VL) &bull; **Tavily AI Search** (live web discovery &amp; store evidence) &bull; **FastAPI** &bull; **Supabase** &bull; **React 18** &bull; **TypeScript 5.7**

---

## Submission Metadata

<div align="justify">

* **Project Title:** **Vitrine**
* **Tagline:** Boutique wholesale studio for independent craft brands, combining cultural taste intelligence, dual foundation models, and live web discovery.
* **Category / Focus Areas:** Autonomous AI Agents, Cultural Taste Intelligence, Grounded Web Discovery
* **Built With:** Qloo Taste Graph API, NVIDIA Nemotron (120B & 550B), Nebius Token Factory, Tavily Search API, Supabase, FastAPI, React 18, TypeScript, Tailwind CSS v4, SQLite/PostgreSQL
* **Repository URL:** [https://github.com/lakshyajn/Vitrine](https://github.com/lakshyajn/Vitrine)

</div>

---

## Project Description

### 1. Inspiration

<div align="justify">

Independent craft studios, textile ateliers, and ceramicists make physical products, but finding overseas stockists manually is slow and difficult:

* **Cold email spam hurts reputations:** Generic sales tools scrape directory lists and blast retail buyers with mass templates. Independent concept stores report them as spam, which burns the maker's reputation before a conversation even starts.
* **Keyword search misses aesthetic context:** Curated concept boutiques and design stores choose collections based on aesthetic alignment, craft traditions, and design philosophy (such as wabi-sabi, botanical dyeing, or mid-century modern). Traditional search engines index keyword density rather than curated retail aesthetics.
* **Manual verification takes weeks:** Researching individual stores across different countries, checking whether they are currently open, reviewing their price tiers against wholesale margins, and finding the right contact details takes hours for each store.

We built Vitrine to give independent makers a structured wholesale workspace. It connects multimodal product attribute extraction with cultural taste mapping and live web verification, grounding every recommendation in verified store facts without automated mass-mailing.

</div>

<div align="center">
  <img src="../diagrams/01-vitrine-maker-journey.png" alt="Vitrine End-to-End Maker Journey" width="100%" />
</div>

---

### 2. What It Does

<div align="justify">

Vitrine is a boutique discovery and wholesale preparation platform:

1. **Multimodal Product Passport:** The maker uploads product photography or pastes workshop notes. **NVIDIA Nemotron 3.5 Super VL (120B)** extracts materials, motifs, price tiers (in `USD`, `EUR`, and `GBP`), and export capacity in under two seconds.
2. **Market Hypothesis & Anchor Planning:** **NVIDIA Nemotron 3 Ultra (550B)** formulates strategic market hypotheses and proposes cultural design anchors (such as wabi-sabi homewares, botanical dyes, or heritage tableware).
3. **Cultural Taste Graph Resolution:** Confirmed taste anchors resolve through the **Qloo Taste Graph API**, mapping design movements to boutique demographics, cultural entities, and aesthetic affinities across target regions (Western Europe, North America, Scandinavia, Japan).
4. **Targeted Web Discovery:** The **Tavily Pipeline** searches live web sources for independent boutiques, canonicalizes domains, and removes duplicate retailers.
5. **Seller-in-the-Loop Confirmation & Selective Scraping:** The artisan reviews candidate stockists. Vitrine extracts live website text only for confirmed boutiques, keeping pipeline execution fast.
6. **Concurrent Fit Assessment:** **Nemotron 3.5 Super VL** concurrently evaluates category alignment, aesthetic vector, and commercial compatibility against stored web excerpts.
7. **Strict Grounded Outreach:** **Nemotron 3 Ultra (550B)** drafts personalized, human-fluent buyer correspondence citing real store context without technical IDs or unsupported claims. The maker reviews, edits, copies to clipboard, and tracks status manually. No automated emails are ever sent.

</div>

---

### 3. Technical Architecture

<div align="center">
  <img src="../diagrams/02-vitrine-system-architecture.png" alt="Vitrine Full-Stack System Architecture" width="100%" />
</div>

#### A. Cultural Taste Graph & Aesthetic Affinity (Qloo API)

<div align="justify">

Curated concept stores in cities like London, Paris, Tokyo, and Stockholm stock products based on aesthetic resonance and cultural overlap rather than generic keywords. Vitrine integrates the **Qloo Taste Graph API** (`backend/integrations/qloo.py` & `backend/research/pipeline.py`) to connect physical craftsmanship with retail culture:

- **Entity Resolution & Taste Anchors:** Artisan design motifs extracted by our vision models (such as madder root dyes, wabi-sabi ceramics, or Bauhaus tableware) resolve through Qloo's `/search` and `/v2/insights` endpoints into structured cultural anchors.
- **Cross-Domain Demographic Mapping:** Qloo identifies overlaps between cultural design movements, high-affinity destinations, and boutique consumer demographics.
- **Hypothesis Attachment:** Discovered cultural taste signals attach directly to each `MarketHypothesis` and populate the `cultural_affinity` metadata on discovered buyer leads, giving makers clear context on why a specific stockist aligns with their collection.

</div>

#### B. Dual-Model Foundation AI (NVIDIA Nemotron on Nebius Token Factory)

<div align="center">
  <img src="../diagrams/04-nemotron-nebius-model-routing.png" alt="Dual Nemotron Model Routing on Nebius Token Factory" width="100%" />
</div>

<div align="justify">

Vitrine routes inference through the OpenAI-compatible **Nebius Token Factory API** (`https://api.tokenfactory.nebius.com/v1`), matching computational capacity to specific pipeline tasks:

- **NVIDIA Nemotron 3 Ultra (550B) on Nebius Token Factory:** Reserved for high-touch reasoning tasks: market hypothesis generation (Task B) and human-fluent wholesale outreach copywriting (Task D) citing verified store excerpts.
- **NVIDIA Nemotron 3.5 Super VL (120B) on Nebius Token Factory:** Deployed for high-throughput calls: fast multimodal extraction (<2s) of product attributes (Task A) and concurrent lead assessment across candidate batches using async worker semaphores (Task C).
- **Model Fallback Resilience:** In the event of transient upstream rate limits, Vitrine features automated cross-model fallback between 550B and 120B endpoints to prevent failed runs.

</div>

#### C. Live Web Discovery & Store Evidence Extraction (Tavily AI Search)

<div align="center">
  <img src="../diagrams/05-evidence-and-deterministic-scoring.png" alt="Evidence Grounding and Deterministic Lead Scoring" width="100%" />
</div>

<div align="justify">

To prevent outdated directories or fabricated store details, Vitrine integrates **Tavily AI Search**:

- **Targeted Boutique Search:** Executes queries combining confirmed product categories, target regions, and Qloo-derived taste vectors to discover operational boutique stockists.
- **Domain Canonicalization & Deduplication:** Normalizes domain names (stripping subdomains, trailing paths, and tracking parameters) and identifies secondary branch stores or sister domains to eliminate duplicates.
- **Untrusted Web Isolation:** Scraped retailer text is strictly encapsulated inside `<untrusted_retailer_evidence>` envelopes within prompt templates to safeguard against prompt injection.
- **Zero Hallucination Grounding:** Real store excerpts are stored in database records (`lead_evidence`) and directly linked to every generated fit score and outreach claim.

</div>

#### D. Full-Stack Foundation, Security & UI (FastAPI, Supabase & React 18)

<div align="justify">

- **FastAPI Asynchronous Backend:** High-performance async Python 3.11 with SQLAlchemy 2.0 and Pydantic v2 schemas.
- **Supabase Authentication & Multi-Tenant Data Isolation:** Secure JWT authentication supporting asymmetric ES256/RS256 with PyJWKClient dynamic key retrieval, and multi-tenant scoping (`WHERE owner_id = :caller_id`) across all data entities.
- **Centralized Viewport Modal Architecture:** Built with React portals mounted directly to `document.body` with focus trapping and body scroll locking, completely eliminating CSS transform containing-block bugs.
- **Contract-First Synchronization:** Both frontend and backend adhere strictly to shared wire schemas defined in `contracts/schemas.py`.

</div>

---

### 4. Challenges We Overcame

<div align="justify">

1. **Enforcing Zero Hallucinations:** Language models can invent stockist details or make claims about wholesale policies that do not exist. We wrote deterministic claim validators (`validate_lead_assessment_claims`, `validate_and_ground_outreach_draft`) that strictly cross-examine every assertion against stored web excerpts.
2. **Preserving Unknown Truths:** In wholesale evaluation, absent information is not a negative score. If a retailer's minimum order quantity or wholesale margin is not publicly disclosed on their website, Vitrine explicitly reports *"Not enough evidence"* (`null`) rather than coercing scores to zero.
3. **Connecting Physical Craft to Cultural Taste:** Raw textile terms like *"indigo dabu mud resist"* mean nothing to keyword search algorithms. Integrating Qloo allows Vitrine to map artisan heritage techniques into cultural affinity vectors and boutique taste demographics.
4. **Pipeline Concurrency & Efficiency:** Scraping dozens of websites sequentially is slow. We introduced seller-in-the-loop candidate confirmation so live scraping only targets confirmed boutiques, evaluated concurrently with async semaphores.
5. **Production Fallback Safeguards:** Many platforms silently switch to mock fixtures when API keys are absent in production. We implemented strict production safeguards in `backend/research/pipeline.py` and `backend/ai/service.py` that raise explicit HTTP 503 errors (`upstream_unavailable`, `ai_generation_failed`) in production, guaranteeing zero fabricated data reaches real users.
6. **Viewport-Centered Modal Architecture:** Resolved a subtle CSS transform containing-block issue where ancestor animations trapped fixed modals. Built a shared React portal modal framework mounted to `document.body` with focus trapping and body scroll locking.

</div>

---

### 5. Verified Accomplishments

<div align="justify">

- **167/167 Passing Tests:** 130 backend unit/integration tests and 37 frontend unit/integration tests verifying contracts, scoring, security, and component workflows.
- **Tri-Engine Synergy:** Cohesive integration of Qloo Taste Graph API, NVIDIA Nemotron foundation models on Nebius Token Factory, and Tavily Live Search into an intuitive maker workspace.
- **Direct Maker Control:** Real wholesale buyers appreciate genuine craftsmanship. Vitrine keeps the artisan in control with zero automated emailing.
- **Production-Grade Architecture:** Full separation of concerns with contract-first schemas ([contracts/schemas.py](../contracts/schemas.py)), zero lint errors, and 0 TypeScript errors.

</div>

<div align="center">
  <img src="../diagrams/06-grounded-outreach-workflow.png" alt="Grounded Wholesale Outreach Studio Workflow" width="100%" />
</div>

---

## How to Run the Working Demo

### Quick Local Verification (3 Minutes):

```bash
# Clone and enter directory
git clone https://github.com/lakshyajn/Vitrine.git
cd Vitrine

# Configure environment with template
cp .env.example .env
cp .env.example frontend/.env

# Start Backend (FastAPI on port 8000)
uvicorn backend.app.main:app --port 8000 --reload

# Start Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)** to explore the running atelier.
