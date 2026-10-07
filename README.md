# Jinder — Autonomous Capability Alignment Platform

> **Live Platform Repository & Source Code**  
> For complete instructions on how to start and test the platform, see [**`Document/guides/01_GETTING_STARTED.md`**](Document/guides/01_GETTING_STARTED.md).

---

## 🚀 Quick Start

You only need **Python 3.9+** (tested on Python 3.12). No external dependencies or `pip install` required.

```bash
cd jinder_platform
python3 start.py --demo
```
- Open **`http://localhost:8095/`** in your browser.
- Write down the demo passwords printed in the terminal:
  - **Employer:** `recruiter@demo.jinder.app`
  - **Talent:** `candidate@demo.jinder.app`

### Run Autonomous Tests
```bash
cd jinder_platform
python3 run_tests.py
```
*(Runs all 729 unit & integration tests in ~24s with full `OK` status).*

---

## 📁 Repository Structure

The repository is organized into a clean, modular structure centered around the unified `Document/` hub:

```
Excelerate-Skill-Bridge/
│
├── Document/                  # 📚 Master Documentation Hub (guides, architecture, sdd, prompt, ai_rule)
│   ├── guides/                # 🚀 Quick start, system architecture guide, demo walkthroughs
│   ├── architecture/          # 📐 Deep specifications, schemas, formulas, diagrams, AI test plan
│   ├── sdd/                   # 📋 Software Design Description (PRD, specs, user flows, stories)
│   ├── prompt/                # 💬 Prompt engineering principles, guardrails & API contracts
│   └── ai_rule/               # 🛡️ AI governance boundaries, ethical limits & 10 core safety rules
├── Presentation/              # 🎨 Interactive Portals (Pitch Deck, Formulas Deck, Admin Telemetry)
├── Skill/                     # ⚡ 5 Antigravity & Agentic Skills
├── Data/                      # 📊 Verified Synthetic Benchmarks & Australian Legal Provenance
│
├── jinder_platform/           # 🚀 The Running Platform Backend & SQLite Database
├── jinder_frontend/           # 🎨 Client Web Application (HTML/CSS/JS)
├── jinder_backend_engine/     # 📐 Intelligence Engine (Formulas F-01 to F-06)
└── old_version/               # 📦 Archived Legacy Files & Historical Prototypes
```

---

## 🖥️ Interactive Presentation & Administrative Portals

The `Presentation/` directory hosts two zero-build, standalone web applications built with the **Jinder Design System**:

1. [**`Presentation/formulas_presentation.html`**](Presentation/formulas_presentation.html) — **Canonical Mathematical Engine Deck (ASD-STE100)**:
   - **All 6 Formulas Grid:** 100vh single-screen view displaying all 6 canonical formulas (F-01 through F-06) simultaneously with zero page scrolling.
   - **Live Parameter Workbench:** Interactive simulation panel on the left with continuous gradient sliders (`#6868f7` $\to$ `#a855f7` $\to$ `#ffa340`), real-time calculation, and step-by-step worked numerical examples.
   - **KaTeX Variable Table:** Crisp vector mathematical variables with calibrated Australian industry values.
   - **Strict Standards:** 100% Australian English (`en-AU`), Talent / Employer terminology, and official Jinder SVG branding.

2. [**`Presentation/admin.html`**](Presentation/admin.html) — **Admin Control Center & Data Flow Telemetry**:
   - **Live SQLite WAL Metrics:** Active page count, database file size (0.95 MB), journal mode, and verified role breakdown (**51 Talents**, **1 Demo Employer**).
   - **5-Stage Data Flow Pipeline Chart:** Visual pipeline (Ingestion $\to$ Taxonomy Translation $\to$ Mathematical Engine $\to$ SQLite WAL $\to$ Shortlist Delivery) with interactive stage inspection and live query telemetry.
   - **22 Tables SQLite Explorer:** Filter, search, and paginate through all 22 database tables with a built-in Safe SQL runner.

---

## 📐 The 6 Canonical Mathematical Formulas

Documented in [**`Document/architecture/FORMULA_ARCHITECTURE_DETAIL.md`**](Document/architecture/FORMULA_ARCHITECTURE_DETAIL.md) and implemented in `jinder_backend_engine/intelligence_engine/`:

1. **F-01 (SMF):** Skill Match Frequency & Coverage (weighted mandatory $w=2.0$ vs preferred $w=1.0$ with proficiency depth).
2. **F-02 (GSI & JRS):** Gap Severity Index & Net Job Readiness Score (distinguishes statutory blockers $\beta=15.0$ from learnable tools $\beta=5.0$).
3. **F-03 (JPI):** Job Proximity Index (cross-career mobility using Jaccard vector similarity with ICT domain affinity modifiers).
4. **F-04 (RMS):** Relative Merit Score (Zero-PII Gaussian Z-score standardization against active applicant pool).
5. **F-05 (FRS):** Feed Ranking Score (multi-objective ranking for talent opportunity feed, incorporating work modes and experience brackets).
6. **F-06 (TSS):** Employer Talent Search Score (anonymized talent ranking factoring capability match, seniority alignment, certifications, and recency).

To explore the formulas interactively, open:
```bash
open Presentation/formulas_presentation.html
```
