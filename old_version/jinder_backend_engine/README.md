# Jinder — Backend REST API, Mathematical Intelligence Engine & Data Handoff Package

> **A self-contained production handoff package containing the Jinder REST API backend, the 6 deterministic mathematical scoring engines, real Australian job & candidate datasets, and full technical documentation.**

---

## 🚀 2-Minute Quick Start

### 1. Launch the Backend API Server
```bash
python3 start_server.py
```
- Starts the REST API on `http://localhost:8095` (or custom `$PORT`).
- Automatically initializes and seeds the SQLite database (`backend/var/app.db`) with **461 Australian jobs** and **320 candidate profiles**.
- Zero external dependencies required (runs on pure Python 3.9+ standard library).

### 2. Run the Mathematical Verification Suite
```bash
python3 run_verification.py
```
- Tests all 6 intelligence engine formulas (SMF, GSI, JPI, RMS, FRS, TSS) and backend scoring wrappers in ~2 seconds.

### 3. Open the Interactive Visual Presentation
Open [`intelligence_engine/formulas_presentation.html`](intelligence_engine/formulas_presentation.html) in any web browser:
- Interactive KaTeX equations and formula explanations.
- Dynamic purple gradient sliders to simulate real-time scoring.
- ASD-STE100 technical documentation.
- Fixed sticky navigation header and smooth transitions.

---

## 📁 Package Directory Structure

```
jinder_backend_engine/
│
├── README.md                      # 👈 THIS MASTER HANDOFF GUIDE
├── start_server.py                # One-click launcher for backend API + DB
├── run_verification.py            # Automated test suite for all formulas & DB
├── requirements.txt               # Dependencies notice (Python 3.9+ standard library)
│
├── backend/                       # REST API Backend
│   ├── server.py                  # Full HTTP REST API Server (port 8095)
│   ├── scores.py                  # Scoring engine integration wrapper
│   ├── db.py                      # SQLite database operations & schemas
│   ├── seed_db.py                 # DB seeding pipeline (461 jobs, 320 candidates)
│   └── var/
│       └── app.db                 # SQLite database (WAL mode)
│
├── intelligence_engine/           # 6 Deterministic Mathematical Models
│   ├── 01_skill_matching_model.py # F-01: Candidate vs ANZSCO Match (SMF)
│   ├── 01_SKILL_MATCHING_MODEL.md
│   ├── 02_skill_gap_analysis.py   # F-02: Gap Severity & Job Readiness (GSI & JRS)
│   ├── 02_SKILL_GAP_ANALYSIS.md
│   ├── 03_job_to_job_comparison.py# F-03: Job Proximity Index (JPI)
│   ├── 03_JOB_TO_JOB_COMPARISON.md
│   ├── 04_candidate_benchmarking.py # F-04: Relative Merit Benchmarking (RMS)
│   ├── 04_CANDIDATE_BENCHMARKING.md
│   ├── 05_job_seeker_ranking_feed.py# F-05: Seeker Feed Ranking (FRS) + Feedback Loop
│   ├── 05_JOB_SEEKER_RANKING_FEED.md
│   ├── 06_recruiter_candidate_ranking.py # F-06: Recruiter Talent Search (TSS)
│   ├── 06_RECRUITER_CANDIDATE_RANKING.md
│   ├── MASTER_PLAN.md             # End-to-end mathematical architecture
│   └── formulas_presentation.html # Interactive visual simulator & formula reference
│
├── data/                          # Platform Datasets (No Crawled / Scraped Junk)
│   ├── australian_jobs.json       # 461 real Australian job requisitions
│   ├── australian_candidates.json # 320 international candidates with skill vectors
│   ├── australian_jobs_dataset.csv# Tabular CSV export of job postings
│   ├── international_candidates_dataset.csv # Tabular CSV export of candidates
│   ├── real_resumes_dataset.csv   # Real resume competency dataset
│   └── reference/                 # Official taxonomies & mappings
│       ├── target-roles.json      # Primary target career paths
│       ├── jd-skills.reference.json # Standard skill keyword definitions
│       └── role-mappings.reference.json # ANZSCO occupational tree mapping
│
└── docs/                          # Pure Technical Documentation
    ├── 01_BACKEND_DEVELOPMENT_GUIDE.md # 💻 Complete Guide for Backend Developers
    ├── 02_FORMULAS_MATHEMATICAL_SPEC.md# 📐 Mathematical Equations & Proofs
    ├── 03_API_SPEC.md             # Standard REST API contracts & routes
    └── 04_DATA_AND_SCORING_SPEC.md# Data pipeline & continuous scoring rules
```

---

## 🛠️ Backend Architecture & Endpoints

### 1. REST API Server (`backend/server.py`)
- Standard library HTTP server running on port `8095` with full CORS support.
- Key endpoints:
  - `GET /api/public/stats` — Platform stats (active jobs, candidate counts, sector distributions).
  - `GET /api/seeker/feed` — Ranked job recommendations (Formula 5 FRS).
  - `POST /api/seeker/swipe` — Swipe action: like or dismiss (records behavioral affinity).
  - `GET /api/seeker/profile` — Candidate profile and verified skills.
  - `GET /api/seeker/projection` — 12-Month Dual-Line curve coordinates (baseline vs accelerated bridge).
  - `POST /api/recruiter/search` — Talent search (Formula 6 TSS) with Zero-PII aliases.
  - `POST /api/benchmark/candidates` — Head-to-head comparison (Formula 4 RMS).
  - `POST /api/compare/jobs` — Job distance matrix (Formula 3 JPI).

### 2. Database Engine (`backend/db.py` & `backend/seed_db.py`)
- SQLite database in Write-Ahead Logging mode (`PRAGMA journal_mode=WAL;`).
- Pre-populated with **461 verified Australian jobs** and **320 international candidate profiles**.

### 3. Intelligence Engine Wrapper (`backend/scores.py`)
- Direct Python wrappers connecting API endpoints to `intelligence_engine/*.py`.
- Deterministic, zero LLM hallucination, execution time `< 5ms`.

---

## 📐 Mathematical Formulas Index

| ID | Formula Name | Objective | Key Mathematical Property |
| :--- | :--- | :--- | :--- |
| **F-01** | **SMF** (Skill Match) | Candidate vs ANZSCO benchmark | Continuous logarithmic experience scaling $\Phi(Y_C, L_O) \in [0.75, 1.15]$ |
| **F-02** | **GSI & JRS** (Gap Severity) | Statutory blockers vs software tools | Sub-linear parallel learning duration $T = \max(T) + 0.18\sum T$ |
| **F-03** | **JPI** (Job Proximity) | Career pivot & salary parity | Continuous exponential salary parity $S_{\text{comp}}$ |
| **F-04** | **RMS** (Candidate Merit) | Fair benchmarking without PII | Normalized continuous merit score & delta comparison $\Delta$ |
| **F-05** | **FRS** (Seeker Feed) | Personalized job recommendations | Behavioral feedback loop (+10% save affinity, -25% ignore penalty) |
| **F-06** | **TSS** (Recruiter Search) | Candidate ranking for recruiters | Gaussian continuous seniority parity $S_{\text{sen}}$ & statutory multiplier |

For exact mathematical proofs, LaTeX equations, and worked examples, see **[`docs/02_FORMULAS_MATHEMATICAL_SPEC.md`](docs/02_FORMULAS_MATHEMATICAL_SPEC.md)**.

---

## 📊 Platform Datasets (`data/`)

1. **`australian_jobs.json`**: 461 real Australian vacancies with titles, employers, salaries min/max, ANZSCO codes, and required skill matrices.
2. **`australian_candidates.json`**: 320 candidate profiles with verified skill inventories, target ANZSCO roles, and years of experience.
3. **`reference/`**:
   - `target-roles.json`: Standard benchmark roles.
   - `jd-skills.reference.json`: Canonical skill taxonomies.
   - `role-mappings.reference.json`: ABS ANZSCO 2026 hierarchy mappings.

---

## 📦 Sharing with Colleagues
- Send the folder [`jinder_backend_engine/`](jinder_backend_engine/) directly, or
- Send the pre-packaged zip archive [`jinder_backend_engine.zip`](../jinder_backend_engine.zip) (1.0 MB).
