# Presentation Directory — Jinder Autonomous Capability Alignment Platform

This directory contains standalone, zero-build HTML5 presentations and administrative telemetry portals for the **Jinder Platform**, built in strict accordance with the **Jinder App Design System** (Deep Navy `#151531`, Jinder Violet `#6868f7`, Vibrant Coral `#ffa340`, Inter typography, and authentic Jinder SVG branding).

---

## Interactive Presentation & Telemetry Portals

| Portal / Document | Type | Primary Role & Capabilities |
|---|---|---|
| [**`Posters/`**](Posters/) | **Print & Marketing Posters** | **High-Resolution Print Deliverables:**<br>• [**`Posters/promo_poster_light.html`**](Posters/promo_poster_light.html) ([`PDF`](Posters/jinder_promo_poster_light.pdf) / [`PNG`](Posters/jinder_promo_poster_light.png)) — Promotional Poster (Light Mode, 1600×2300)<br>• [**`Posters/promo_poster.html`**](Posters/promo_poster.html) ([`PDF`](Posters/jinder_promo_poster.pdf) / [`PNG`](Posters/jinder_promo_poster.png)) — Promotional Poster (Dark Mode)<br>• [**`Posters/poster.html`**](Posters/poster.html) ([`PDF`](Posters/jinder_poster.pdf) / [`PNG`](Posters/jinder_poster.png)) — Technical Architecture Poster |
| [**`Video/`**](Video/) | **Live App Walkthrough Video** | **YouTube-Style Master Product Tour (.mp4):**<br>• [**`Video/jinder_demo_video.mp4`**](Video/jinder_demo_video.mp4) — 1080p Full HD master video (04:14, 15.9 MB, 12 steps) featuring authentic Australian voiceover (`en-AU-NatashaNeural`), burned-in Engsubs, transition bumpers, and ambient background music.<br>• [**`Video/demo_video.html`**](Video/demo_video.html) — Interactive 12-step cinema player with instant chapter seeking and download button. |
| [**`jinder_deck.html`**](jinder_deck.html) ([`PDF`](jinder_deck.pdf)) | **Canonical Master Pitch Deck** | **Comprehensive Master Executive Presentation:**<br>• Australian skilled migration & talent bottleneck problem framing.<br>• Two-sided capability alignment architecture and zero-bias matching engine.<br>• Business model, unit economics, and 6-month launch roadmap.<br>• *Canonical and only master slide presentation for the platform.* |
| [**`Jinder_Product_Plan.html`**](Jinder_Product_Plan.html) ([`PDF`](Jinder_Product_Plan.pdf)) | **Product & Marketing Strategy** | **Comprehensive 6-Month Execution Plan:**<br>• GTM strategy, campus ambassadors, university partnership rollout, and employer acquisition funnel.<br>• Financial projections, pricing tiers (Free Talent, Premium Employer, Enterprise Campus). |
| [**`formulas_presentation.html`**](formulas_presentation.html) | **Canonical Mathematical Engine Deck** | **100vh Single-Screen Deck (ASD-STE100 Certified):**<br>• Presents the 6 canonical deterministic formulas (F-01 SMF, F-02 GSI/JRS, F-03 JPI, F-04 RMS, F-05 FRS, F-06 TSS) from `Document/architecture/FORMULA_ARCHITECTURE_DETAIL.md`.<br>• **All 6 Formulas Grid (Default View):** Balanced 3×2 grid showing all mathematical equations, SLA latencies, and parameter weights simultaneously on one screen without vertical scrolling.<br>• **Live Parameter Workbench:** Interactive simulation panel positioned on the left with continuous gradient sliders (`#6868f7` $\to$ `#a855f7` $\to$ `#ffa340`), real-time score convergence, and step-by-step worked numerical examples.<br>• **High-Clarity Variable Table:** KaTeX-rendered variable symbols with styled operational calibration tags.<br>• **Branding & Terminology:** Official Jinder SVG logo mark, SVG tab favicon, and strict **Talent / Employer** Australian English (`en-AU`) terminology. |
| [**`admin.html`**](admin.html) | **Admin Control Center & Data Flow Telemetry** | **Enterprise Administration & WAL Telemetry Suite:**<br>• **Overview & System Health:** Live SQLite WAL metrics (pages, file size, journal mode), user breakdown (**51 Talents**, **1 Demo Employer**), and component SLAs.<br>• **Interactive 5-Stage Data Flow Pipeline Chart:** Real-time visual pipeline (Ingestion $\to$ Taxonomy Translation $\to$ Mathematical Scoring $\to$ SQLite WAL Concurrency $\to$ Shortlist Delivery) with interactive click-to-inspect stage analytics and sample data.<br>• **Traffic & Latency Telemetry:** Request rates, p50/p95/p99 latency percentiles, status distribution, and 31 top Australian tech employers directory.<br>• **22 Tables Relational Explorer:** Full pagination, live column search, text filters, and schema inspector across all SQLite tables.<br>• **Safe SQL Runner:** In-browser query terminal with syntax checks and safe read-only query execution.<br>• **Branding:** Official Jinder SVG logo and SVG browser tab favicon. |

---

## Viewing Instructions

Both portals are standalone HTML5 applications that run natively in any modern web browser without dependencies, Node.js, or build pipelines:

```bash
# Open the Master Pitch Presentation Deck
open Presentation/jinder_deck.html

# Open the Canonical Formulas Technical Presentation (100vh, All 6 Formulas on Screen)
open Presentation/formulas_presentation.html

# Open the Admin Control Center & Data Flow Telemetry Portal
open Presentation/admin.html
```

---

## Architectural & Governance Standards
- **Zero-PII Compliance:** Neither portal stores or displays identifiable demographic data (no names, dates of birth, photos, or nationality).
- **100% Australian English (`en-AU`):** All labels, tooltips, variable descriptions, and copy adhere strictly to Australian spelling and Australian ICT industry standards.
- **Strict Role Terminology:** Exclusively uses **`Talent`** and **`Employer`** across all telemetry cards, data tables, and variable explanations (zero legacy "Candidate" or "Recruiter" phrasing).
- **Authentic Branding:** Direct vector integration of `logo.svg` across headers, sidebars, and browser tab favicons.
