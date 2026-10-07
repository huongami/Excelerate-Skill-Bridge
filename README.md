# Jinder (Skill Bridge 2.0) — Autonomous Capability Alignment Platform

> **Live Platform Repository & Source Code**  
> For complete instructions on how to start and test the platform, see [**`START_HERE.md`**](START_HERE.md).

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

The platform is organized into 4 side-by-side core folders:

```
Excelerate-Skill-Bridge/
│
├── START_HERE.md              # 👈 Start here: Complete setup and running instructions
├── README.md                  # Master repository overview
│
├── jinder_platform/           # 🚀 The Running Platform Backend
│   ├── start.py               # Launcher: python3 start.py [--demo] [--port 8095]
│   ├── run_tests.py           # 729 automated tests (integration, DB, formulas)
│   ├── jinder/                # Platform core: REST API, SQLite models, CV reader, server
│   ├── var/                   # SQLite database (jinder.db) & upload storage
│   └── docs/                  # Platform documentation, API notes, database spec
│
├── Skill Bridge/              # 🎨 The Frontend & Application Specifications
│   ├── app/                   # Web frontend (HTML, CSS, JS) served by jinder_platform
│   ├── Docs/                  # Design system (DESIGN.md), feature specs, user stories
│   ├── AI_Rule.md             # Architecture, security & privacy rules
│   └── prompt.md              # API contract between frontend & backend
│
├── jinder_backend_engine/     # 📐 Intelligence Engine & Data Taxonomies
│   ├── intelligence_engine/   # 6 exact mathematical formulas (F-01 to F-06)
│   ├── data/
│   │   ├── reference/         # ICT Taxonomy (ict_taxonomy.json, 115KB)
│   │   └── synthetic/         # 50 jobs, 50 talent profiles, 4 demo jobs
│   └── formulas_presentation.html # Interactive formula visual presentation
│
├── spec/                      # 📋 Product Feature Specifications & User Flows
│   ├── Skill_Bridge_Feature_Specs.md
│   ├── Skill_Bridge_User_Flow_Spec.md
│   └── Skill_Bridge_User_Stories.md
│
└── old_version/               # 📦 Archived Legacy Files (Pre-Jinder prototype)
```

---

## 📐 The 6 Core Mathematical Formulas

Located in `jinder_backend_engine/intelligence_engine/`:

1. **F-01 (SMF):** Candidate vs ANZSCO Skill Match Model.
2. **F-02 (GSI & JRS):** Skill Gap Severity & Job Readiness Score (distinguishes statutory blockers from learnable tools).
3. **F-03 (JPI):** Job Proximity Index & Multi-Job Distance Matrix.
4. **F-04 (RMS):** Candidate Benchmarking & Relative Merit Score (Zero-PII).
5. **F-05 (FRS):** Job Seeker Feed Ranking Score + Behavioral Affinity Loop.
6. **F-06 (TSS):** Recruiter Talent Search Score + Wildlife Animal Aliases.

For interactive equation sliders and ASD-STE100 technical documentation, open:
[`jinder_backend_engine/formulas_presentation.html`](jinder_backend_engine/formulas_presentation.html) in your browser.
