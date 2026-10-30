# 🪟 Vitrine — Devpost Hackathon Submission Package

> **Submission for the Nebius × NVIDIA Global AI Hackathon on Devpost**  
> **Track:** Best Apps and Agents Track  
> **Primary Infrastructure:** Nebius Token Factory (Inference) & Supabase (Auth & Data)  
> **Models:** NVIDIA Nemotron 3 Ultra (550B) & NVIDIA Nemotron 3.5 Super VL (120B)

---

## 📋 Quick Submission Metadata

| Field | Submission Details |
| :--- | :--- |
| **Project Title** | **Vitrine** |
| **Tagline** | Boutique Wholesale Atelier for Independent Craft Brands, powered by NVIDIA Nemotron on Nebius Token Factory. |
| **Category / Track** | **Best Apps and Agents Track** |
| **Track Description Fit** | Leverages **Nemotron 3 Ultra (550B)** for deep strategic reasoning & outreach pitch generation, and **Nemotron 3.5 Super VL (120B)** for rapid multimodal structuring and concurrent lead evaluation on **Nebius Token Factory**, with Supabase for authentication and relational storage. |
| **Built With** | Nebius Token Factory, NVIDIA Nemotron, Supabase, FastAPI, React 18, TypeScript, Tailwind CSS, Qloo Taste Graph, Tavily Search API, PostgreSQL/SQLite. |
| **Repository URL** | [https://github.com/lakshyajn/Vitrine](https://github.com/lakshyajn/Vitrine) |

---

## 💡 Project Description

### 1. Inspiration
Independent artisan workshops, heritage textile ateliers, and ceramicists make extraordinary physical goods, but scaling into international wholesale is fraught with friction:
* **The Cold Spam Trap:** Generic AI B2B tools scrape massive email lists and blast buyers with robotic, hallucinated pitches. Wholesale buyers report them as spam, destroying the maker’s reputation.
* **Cultural Context Blindness:** Independent concept boutiques and design stores curate based on **aesthetic affinity, provenance, and tactile curation**—not generic keywords indexed by standard search engines.
* **Manual Discovery Overhead:** Finding authentic international stockists aligned with an atelier's design ethos takes hundreds of hours of manual research.

We built **Vitrine** to give independent makers an agentic boutique wholesale studio that pairs **multimodal product extraction** with **cultural taste mapping** and **live web verification**—grounding every recommendation in verified retailer facts, with zero automated spam.

---

### 2. What It Does
Vitrine is an autonomous boutique discovery and wholesale preparation platform:

1. **Multimodal Product Passport:** The maker uploads product photography or pastes atelier notes. **NVIDIA Nemotron 3.5 Super VL (120B)** structures materials, artisan motifs, price segment, and export MOQ.
2. **Market Hypothesis & Anchor Planning:** **NVIDIA Nemotron 3 Ultra (550B)** formulates strategic market hypotheses and proposes cultural/design anchors (e.g., *wabi-sabi homewares, botanical dyes, artisan tableware*).
3. **Cultural Taste Graph Resolution:** Confirmed taste anchors resolve through the **Qloo Taste Graph**, mapping design movements to boutique demographics across target regions.
4. **Selective Web Discovery:** The **Tavily Pipeline** searches live web sources for authentic independent boutiques, canonicalizes domains, and deduplicates retailers.
5. **Seller-in-the-Loop Confirmation & Selective Scraping:** The artisan reviews candidate stockists. Vitrine prioritizes live excerpt scraping *only for confirmed boutiques*, ensuring fast execution.
6. **Concurrent Fit Assessment:** **Nemotron 3.5 Super VL** concurrently assesses category alignment, aesthetic vector, and commercial compatibility against stored web excerpts.
7. **Strict Grounded Outreach:** **Nemotron 3 Ultra (550B)** drafts personalized, fluent buyer correspondence citing real store context without technical IDs or hallucinated claims. The maker reviews, edits, copies to clipboard, and tracks status manually.

---

### 3. How We Built It: Nebius Token Factory & Supabase

#### A. Dual-Model Nemotron Architecture on Nebius Token Factory
Vitrine routes inference through the standard **Nebius Token Factory API** (`https://api.tokenfactory.nebius.com/v1`), matching the track prompt's model allocation:
- **NVIDIA Nemotron 3 Ultra (550B) on Nebius Token Factory:** Reserved for high-touch reasoning tasks:
  - *Task B (Research Planning):* Derives nuanced international market hypotheses.
  - *Task D (Outreach Copywriting):* Crafts compelling, human-fluent wholesale pitches.
- **NVIDIA Nemotron 3.5 Super VL (120B) on Nebius Token Factory:** Deployed for high-throughput fast calls:
  - *Task A (Product Passport):* Rapid multimodal extraction (<2s) of product attributes.
  - *Task C (Lead Assessment):* High-throughput, concurrent per-lead assessment across candidate batches.

#### B. Supabase Auth & Relational Persistence
Vitrine integrates **Supabase** for secure JWT authentication, user session management, and PostgreSQL cloud storage (with persistent SQLite for local development). Contract-first validation ensures 100% type safety between backend and frontend.

---

### 4. Challenges We Overcame
1. **Zero Hallucination Enforcement:** LLMs tend to invent stockist details. We implemented deterministic claim validators (`validate_lead_assessment_claims`, `validate_and_ground_outreach_draft`) that strictly cross-examine every assertion against stored excerpts.
2. **Preserving "Unknown" Truths:** In B2B wholesale, missing evidence is not a negative finding. If a retailer's MOQ isn't public, Vitrine reports *"Not enough evidence"* rather than coercing scores to zero.
3. **Hackathon Pipeline Concurrency:** Scraping dozens of websites sequentially is too slow. We introduced seller-in-the-loop candidate confirmation so live scraping only targets confirmed boutiques, evaluated concurrently with async semaphores.

---

### 5. Accomplishments That We're Proud Of
- **135/135 Passing Tests:** 122 backend unit/integration tests and 13 frontend tests verifying contracts, scoring, and secret redaction.
- **Production-Grade Architecture:** Full separation of concerns with contract-first schemas ([contracts/schemas.py](../contracts/schemas.py)).
- **Anti-Spam Pledge:** Real wholesale buyers appreciate genuine craftsmanship; Vitrine protects buyer goodwill by keeping the artisan in control with zero automated emailing.

---

## 🎥 3-Minute Video Demo Script

Follow this structured script when recording your demonstration video:

### Scene 1: The Problem & The Solution (0:00 - 0:30)
- **On Screen:** Vitrine Landing / Dashboard.
- **Script:** *"Independent artisan workshops craft incredible physical goods, but reaching overseas boutiques is almost impossible without spending hundreds of hours searching, or worse, using AI spam tools that ruin buyer relationships. Meet Vitrine: a boutique wholesale atelier powered by NVIDIA Nemotron models on Nebius Token Factory."*

### Scene 2: Product Passport & Nemotron Super VL (0:30 - 1:00)
- **On Screen:** Navigate to `/app/products/new`. Upload product photo or paste description (e.g., Hand block-printed linen cushions).
- **Script:** *"First, the maker sets up their Product Passport. Using NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory, Vitrine extracts materials, motifs, price segment, and export capacity in under two seconds. The maker confirms their specifications."*

### Scene 3: Research Run & Qloo Cultural Mapping (1:00 - 1:40)
- **On Screen:** Launch Research Run, review proposed anchors.
- **Script:** *"Next, Nemotron 3 Ultra formulates market hypotheses. Instead of generic keyword searches, confirmed anchors resolve through the Qloo Taste Graph to map cultural design movements in target markets like Western Europe and Japan."*

### Scene 4: Live Web Discovery & Fit Scoring (1:40 - 2:20)
- **On Screen:** Live discovery queue, candidate confirmation, and Lead Detail page.
- **Script:** *"Vitrine queries live web sources via Tavily, finding authentic independent concept boutiques. The maker confirms candidate boutiques, and Vitrine extracts verified store text. Nemotron Super VL concurrently scores each retailer across Category Alignment, Aesthetic Vector, and Commercial Wholesale Compatibility. Notice how unknown data is transparently flagged rather than faked."*

### Scene 5: Grounded Outreach Studio with Nemotron Ultra 550B (2:20 - 2:50)
- **On Screen:** Navigate to Outreach Studio for a qualified lead.
- **Script:** *"Finally, in the Outreach Studio, Nemotron 3 Ultra on Nebius Token Factory drafts a human-fluent wholesale inquiry. Every paragraph cites verified store excerpts and approved product facts. There's no automated send button—the artisan reviews, personalizes, and copies the pitch directly to their clipboard."*

### Scene 6: Nebius Token Factory & Conclusion (2:50 - 3:00)
- **On Screen:** Show the architecture diagram or Dashboard with Nebius Token Factory indicator.
- **Script:** *"Powered by NVIDIA Nemotron on Nebius Token Factory. Empowering independent makers to reach the international boutiques where their craftsmanship belongs."*

---

## 🚀 How to Run the Working Demo

### Quick Local Verification (3 Minutes):
```bash
# Clone and enter directory
git clone https://github.com/lakshyajn/Vitrine.git
cd Vitrine

# Configure environment with Nebius Token Factory template
cp .env.example .env
cp .env.example frontend/.env

# Start Backend
python -m uvicorn backend.app.main:app --port 8000 --reload

# Start Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** to explore the running atelier.

