# GREENMILE
### Bidirectional Last-Mile Logistics Optimizer

**FAR AWAY 2026 Hackathon** · Theme: Logistics & Transit  
**Product Requirements Document** · v2.0  
**Team:** 4–5 Members · **Build Window:** 4 Days

> *"The greenest mile is the one you don't drive twice."*

---

## 1. Executive Summary

Greenmile is an AI-augmented bidirectional logistics optimizer for Indian last-mile delivery fleets. It consolidates outbound deliveries and inbound returns into a single optimized loop, eliminating empty return legs while using an AI layer to detect fraud patterns, predict return probability, and surface natural-language route summaries for non-technical fleet managers.

> **One-line pitch:** Turn two separate delivery trips into one smart loop — same stops, one van, one driver, and a Gemini-powered AI co-pilot that flags problems before they happen.

### What makes this v2.0 different from a basic route optimizer

- **Core differentiator:** Bidirectional loop engine — competitors (Locus, FarEye) optimize deliveries OR returns separately, never combined.
- **AI hook:** Gemini AI Anomaly & Fraud Layer — flags stops with suspicious return patterns using Gemini API, adding genuine intelligence.
- **Unique UX:** Packing Sequencer — tells warehouse workers exactly what to load where so the driver never reshuffles.
- **Demo-first design:** Judges see savings in real-time on a before/after split dashboard with animated route morphing.

---

## 2. Problem Statement

### 2.1 The Two-Trip Waste

Indian e-commerce fleets run on a structurally inefficient two-trip model every single day:

| Trip | Direction | Cargo | Result |
|------|-----------|-------|--------|
| Morning run | Warehouse → Customers | Full on departure | Van returns empty |
| Evening run | Warehouse → Customers | Empty on departure | Returns collected |

This creates four compounding losses every day per van:

- ~40% of daily kilometers driven with zero payload (deadhead miles)
- Two fuel tanks burned for work one loop could cover
- Driver idle time between shifts at the warehouse
- Late return collections — SLA breaches, customer complaints

### 2.2 The Numbers (Delhi-NCR Baseline)

| Metric | Separate Trips | Greenmile Loop | Saving |
|--------|---------------|----------------|--------|
| Total stops | 16 (12 del + 4 ret) | 16 (same) | — |
| Trips made | 2 | 1 | 1 trip |
| Distance driven | 87 km | 52 km | 35 km (40%) |
| Fuel consumed | 7.25 L | 4.33 L | 2.92 L |
| Fuel cost (@₹90/L) | ₹653 | ₹390 | ₹263/day |
| Driver hours | 8.2 hrs | 5.1 hrs | 3.1 hrs |
| CO₂ emitted | 19.4 kg | 11.6 kg | 7.8 kg |

### 2.3 Why Existing Tools Fail

| Tool | What it does | Gap |
|------|-------------|-----|
| Locus / FarEye | Route optimization (delivery only) | No bidirectional consolidation |
| Fleetx / Tata Fleet Edge | Fleet GPS tracking | Plans nothing — just tracks |
| Google Maps Route Planner | Manual multi-stop routing | No capacity, no load sequencing, no returns |
| Excel macros (most SMBs) | Static distance estimates | No optimization, no AI |

---

## 3. The AI Layer (Winning Differentiator)

This is what separates Greenmile from a 2019-era route optimizer. Three AI features, all powered by the Gemini API, requiring no ML training data — ship in hours, not days.

### 3.1 Return Anomaly & Fraud Detector

The Gemini API analyses each return stop against its delivery history and flags suspicious patterns. This is a real, painful problem for Indian e-commerce fleet managers — fake returns cost the industry crores annually.

> **How it works:** On every route generation, the backend sends stop metadata to Gemini with a structured prompt: stop_id, address, return frequency in last 30 days, average delivery confirmation time, and whether the recipient has disputed before. Gemini returns a JSON `risk_score` (0–1) and a plain-English reason. Scores above 0.7 are flagged in the dashboard.

| Input to Gemini | Output from Gemini |
|----------------|-------------------|
| Stop ID, address, return frequency | `risk_score`: 0.0 – 1.0 |
| Delivery confirmation metadata | `flag`: true / false |
| Prior dispute history | `reason`: plain-English explanation |
| Pattern across other stops in cluster | `suggested_action`: HOLD / VERIFY / PROCEED |

### 3.2 Natural-Language Route Summary

After optimization, Gemini generates a 3-sentence briefing for the fleet manager in plain English (and optionally Hindi/Bengali). Non-technical managers should not need to read a table to understand their route.

> **Example output:** "Your Zone B loop covers 14 stops in Saket and Vasant Kunj. Load returns first (R1–R3 at the back), then deliveries front-to-back. Estimated completion by 2:45 PM. Flag: Stop D7 in Malviya Nagar has a 3rd return this month — verify before dispatch."

### 3.3 Return Probability Predictor *(Stretch Goal — Day 4)*

A lightweight heuristic model (no ML training required) that scores each delivery stop with a `return_probability` based on: product category, delivery time window adherence in the cluster, and day-of-week patterns. High-probability returns get pre-inserted as tentative stops in the loop, pre-loading the return bay.

- If `return_probability` > 0.6: pre-stage a return bay slot for that address
- Fleet manager confirms or cancels before dispatch
- Reduces mid-route reshuffles by ~20% (demo-able with seeded data)

---

## 4. Core Feature Set

Scoped for a 4-day build with a 4–5 person full-stack team. Every feature is demo-able with seeded Delhi-NCR data.

| # | Feature | Priority | Owner |
|---|---------|----------|-------|
| F1 | CSV upload & validation | MUST | Backend |
| F2 | DBSCAN geographic clustering | MUST | Backend |
| F3 | Bidirectional route optimizer (NN + 2-opt) | MUST | Backend |
| F4 | Before/after split dashboard with animated route morph | MUST | Frontend |
| F5 | Packing sequencer with 2D van diagram (SVG) | MUST | Frontend |
| F6 | Gemini API — Return Anomaly Detector | MUST | Backend + AI |
| F7 | Gemini API — Natural Language Route Summary | MUST | Backend + AI |
| F8 | Driver mobile view (responsive web) | SHOULD | Frontend |
| F9 | Fleet scaler (1–50 vans projection widget) | SHOULD | Frontend |
| F10 | Return Probability Predictor | STRETCH | Backend + AI |

---

## 5. Technical Architecture

### 5.1 Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI (Python 3.11) | Async, fast, easy deploy on Render free tier |
| Optimizer | Pure Python (scipy + custom NN/2-opt) | No external solver, runs in <1s for <100 stops |
| AI Layer | Gemini API (gemini-2.0-flash) | Fraud detection + NL summaries, no training data needed |
| Database | PostgreSQL 15 on Neon (free tier) | Persistent, easy schema, free |
| Geocoding | Nominatim (fallback: Haversine) | Free, no key needed, offline fallback |
| Routing distances | OSRM (fallback: Haversine) | Real road distances, offline fallback for demo |
| Frontend | React 18 + Vite + Tailwind + Leaflet.js | Fast build, great map support |
| Deploy | Backend: Render · Frontend: Vercel | Both free tier, one-click deploy |

### 5.2 System Flow

```
CSV Upload
    → FastAPI validates & stores stops
    → DBSCAN clusters by geography
    → NN + 2-opt generates bidirectional loop per cluster
    → Gemini API scores return anomalies
    → Gemini API generates NL summary
    → React dashboard renders before/after map + metrics + packing sequence
```

> **AI integration note for judges:** Gemini API calls are made server-side on every route generation. The anomaly detection prompt is structured (JSON in, JSON out) so results are deterministic and auditable. The natural language summary is a separate call with a strict 3-sentence constraint. Both calls are logged to the database for inspection.

### 5.3 Data Model (Key Tables)

| Table | Key Columns |
|-------|------------|
| `uploads` | id, filename, total_stops, delivery_count, return_count, status, created_at |
| `stops` | id, upload_id, stop_id, type (DELIVERY/RETURN), lat, lng, weight_kg, volume_l, time_window, cluster_id, route_sequence, eta, risk_score, risk_reason |
| `routes` | id, upload_id, cluster_id, total_distance_km, total_fuel_l, total_fuel_cost, total_co2_kg, nl_summary (Gemini output), stop_sequence (JSONB) |
| `anomalies` | id, stop_id, route_id, risk_score, flag, reason, suggested_action, gemini_model_version |

---

## 6. Gemini API Integration (Implementation Guide)

### 6.1 Anomaly Detection Prompt

Send this structured prompt to `gemini-2.0-flash` for each cluster of return stops:

```
System: You are a logistics fraud analyst for Indian last-mile delivery.
        Analyse stop return data and respond ONLY with valid JSON.
        No preamble. No markdown.

User:   {stop_id, address, return_count_30d, avg_delivery_confirm_minutes,
         dispute_history_count, cluster_return_rate}

Expected JSON:
{
  "risk_score": 0.0–1.0,
  "flag": bool,
  "reason": "string",
  "suggested_action": "HOLD|VERIFY|PROCEED"
}
```

### 6.2 Natural Language Summary Prompt

```
System: You are a dispatcher assistant. Write a 3-sentence route briefing
        for a fleet manager. Be direct. Include one flagged anomaly if any.

User:   {zone_id, stop_count, optimized_distance_km, estimated_completion_time,
         flagged_stops_count, top_anomaly_reason}
```

### 6.3 API Call Skeleton (FastAPI)

```python
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

async def analyse_anomaly(stop_data: dict) -> dict:
    prompt = ANOMALY_SYSTEM_PROMPT + "\n" + json.dumps(stop_data)
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=256,
        )
    )
    return json.loads(response.text)
```

---

## 7. 4-Day Sprint Plan (4–5 Person Team)

> **Team allocation:** 2 backend engineers own the optimizer and API. 2 frontend engineers own the dashboard and packing sequencer. 1 person (strongest full-stack) owns the Gemini API integration and end-to-end demo flow. Everyone ships to the same GitHub repo with meaningful commits from day 1.

| Day | Focus | Deliverables | Owner |
|-----|-------|--------------|-------|
| Day 1 AM | Data foundation | CSV parser, Pydantic models, DB schema, seeded Delhi-NCR demo data (28 deliveries + 14 returns) | Backend |
| Day 1 PM | Frontend scaffold + map | React project, Leaflet map, CSV upload dropzone, raw dot plot of seeded stops | Frontend |
| Day 2 AM | Core optimizer | DBSCAN clustering, NN + 2-opt bidirectional loop, distance matrix (Haversine fallback) | Backend |
| Day 2 PM | Dashboard shell | Before/after split map layout, route polylines (red/blue vs green), metric cards (static data) | Frontend |
| Day 3 AM | Gemini API integration | Anomaly detection endpoint, NL summary endpoint, anomaly badge on dashboard | Full-stack |
| Day 3 PM | Packing sequencer | Van SVG diagram, load order algorithm, worker checklist, route sequence → packing sync | Frontend |
| Day 4 AM | Polish + integration | Animated route morph on optimize click, fleet scaler widget (1–50 vans), driver mobile view | Frontend |
| Day 4 PM | Demo + submission | 3-min demo video, README with architecture diagram, commit cleanup, final submission | All |

---

## 8. Demo Script (3 Minutes)

Design the demo around the judge's attention span. Every 30 seconds must deliver one *wow* moment.

| Timestamp | Moment | What to show |
|-----------|--------|-------------|
| 0:00–0:20 | **The Waste** | Two animated routes: red van delivers & returns empty. Blue van leaves empty, collects returns. Ticker: 87 km, 8.2 hrs, ₹653. |
| 0:20–0:45 | **The Upload** | Drag CSV onto dashboard. System parses: 28 deliveries, 14 returns, 3 zones. Map fills with coloured dots. |
| 0:45–1:15 | **The Loop** | Click "Generate Greenmile Loop." Animation: dots connect, red/blue fades, green loop draws. Metrics update: 52 km, 5.1 hrs, ₹390. Savings pop in green: ₹263 saved · 3.1 hrs recovered · 7.8 kg CO₂ avoided. |
| 1:15–1:35 | **The AI Flag** | Anomaly badge on Stop R3: "Risk 0.82 — 3rd return from this address in 14 days. Recommended: VERIFY before dispatch." NL summary reads aloud. |
| 1:35–1:55 | **The Sequencer** | Switch to van diagram. Items animate into front/rear bays. "Returns load first — at the back. Driver never reshuffles." |
| 1:55–2:20 | **The Scale** | Toggle fleet: 1 van → 10 → 50 vans. Annual savings update live. CO₂ counter: 5.7 tonnes avoided → 260 trees. |
| 2:20–2:30 | **The Close** | Tagline on screen: *"The greenest mile is the one you don't drive twice."* |

---

## 9. Judge Q&A Prep

| Question | Answer |
|----------|--------|
| Why not just use Google Maps? | Google Maps plans one route at a time. Greenmile plans delivery+return loops simultaneously with van capacity constraints, load sequencing, and AI fraud detection — none of which Google Maps supports. |
| Why not just do this in Excel? | Excel has no optimization engine, no capacity constraints, no route geometry, and definitely no AI anomaly detection. A fleet manager using Excel for this spends 45 minutes manually — Greenmile does it in 4 seconds. |
| Is the AI layer real or just a wrapper? | It's a purposeful integration. The anomaly detector sends structured stop metadata to Gemini and gets back a risk score and plain-English reason that is stored in the DB and displayed in the UI. It solves a real problem — fake returns cost Indian e-commerce thousands of rupees per day per fleet. |
| How does it scale to 500 vans? | DBSCAN clusters stops geographically first, so optimization runs per cluster in O(n²) time. For 500 vans: pre-cluster at upload time, run clusters in parallel. Gemini API calls are batched per route, not per stop. |
| What's your go-to-market? | Phase 1: Direct to fleet managers at mid-size e-commerce 3PLs (20–100 vans). ROI is immediate and quantifiable — ₹263/van/day savings pays for the tool in 1 month. Phase 2: API integration into existing TMS platforms. |

---

## 10. GitHub & Submission Checklist

> ⚠️ **Commit history matters.** FAR AWAY judges may review commit history. Every team member must commit code from day 1. Do not push a finished repo on the last day. Aim for 5+ commits per person across the 4 days.

### Repository Structure

```
greenmile/
├── backend/
│   ├── app/          # main.py, models.py, routes/, optimizer/
│   └── ai/           # anomaly.py, summary.py, prompts.py
├── frontend/
│   └── src/
│       └── components/   # UploadDropzone, BeforeAfterMap, MetricCards,
│                         # PackingSequencer, VanDiagram, AnomalyBadge
├── data/
│   └── demo_stops.csv    # seeded Delhi-NCR data, always works offline
└── README.md             # architecture diagram, setup instructions, demo video link
```

### Submission Checklist

- [ ] GitHub repo with all source code
- [ ] README with setup instructions
- [ ] Architecture diagram in README
- [ ] Seeded demo CSV committed
- [ ] Demo video 2–3 min (problem → solution → AI feature → scale)
- [ ] Presentation (max 15 slides)
- [ ] Offline fallback: demo works without live APIs
- [ ] All 4–5 team members have commits

---

## 11. FAR AWAY Judging Criteria Map

| Judging Criterion | How Greenmile v2.0 Addresses It |
|------------------|--------------------------------|
| Innovation & Technical Depth | Bidirectional loop optimization is novel in Indian last-mile context. Gemini AI anomaly layer adds genuine intelligence beyond classical OR. |
| Engineering Quality | FastAPI + async DB + OSRM + custom 2-opt. Structured Gemini prompts with JSON schema output. Meaningful commit history across 4 days. |
| Real-World Impact | Quantifiable: ₹263/van/day savings. Scalable to entire fleet. Fraud detection prevents real revenue loss. Built for Indian logistics context (fuel prices, urban density, return culture). |
| Scalability | DBSCAN pre-clustering + parallel optimization + batched Gemini calls. Handles 500+ stops. Multi-depot roadmap documented. |
| Design & User Experience | Split dashboard with animated route morph. SVG packing sequencer. NL summary for non-technical managers. Driver mobile view. |
| Execution Quality & Completeness | Seeded demo data guarantees 100% demo reliability. Offline fallback for all APIs. All 6 features fully functional, not mocked. |

---

*Greenmile v2.0 PRD · FAR AWAY 2026 · Built for India's last mile*
