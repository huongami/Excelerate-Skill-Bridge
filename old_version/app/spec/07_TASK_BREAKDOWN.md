# 07 — Task Breakdown, Agent Allocation & Definition of Done

Source: [`app/spec/01_REQUIREMENTS_TRACEABILITY.md`](01_REQUIREMENTS_TRACEABILITY.md) through [`app/spec/06_CONTENT_SPEC.md`](06_CONTENT_SPEC.md)
Document standard: Strict task dependencies, concrete acceptance criteria, and agent role assignments.

---

## 1. Agent Roles & Responsibilities

| Role | Primary Responsibilities | Target Code Areas |
| :--- | :--- | :--- |
| **Lead Architect** | Overall system orchestration, specification governance, cross-cutting integration, and final review. | `app/spec/*`, `next.config.ts`, `package.json` |
| **Backend & Data Agent** | SQLite database schema, data seeding from `data/`, intelligence engine wiring, REST API routes, OAuth2 PKCE mock. | `product_api/*`, `intelligence_engine/*` |
| **Frontend UI/UX Agent** | Next.js App Router UI, Organic/Natural Design System components, responsive layouts, Recharts charts, state stores. | `app/*`, `frontend/*`, `globals.css` |
| **QA & Verification Agent** | Automated end-to-end testing, visual audit, compliance checklist verification, performance benchmarking. | `tests/*`, Playwright, curl validation |

---

## 2. Work Breakdown Structure (Tasks T-01 through T-18)

```
[Phase 1: Foundation]
  T-01: Next.js & App Router Project Scaffolding
  T-02: Organic/Natural Design Tokens & Global CSS (Fraunces + Nunito + Paper Noise)
  T-03: UI Primitive Components (Pill Buttons, Cards, Inputs, Badges, Modals)

[Phase 2: Data & Backend Engine]
  T-04: SQLite Database Initialization & Migration Engine
  T-05: Seeding Pipeline (461 AU Jobs + 320 Candidate CVs Reconciled)
  T-06: Intelligence Engine Wiring & Formula API Integration (Formulas 1–6)
  T-07: Authentication & Protocol Mock Google OAuth2 Server

[Phase 3: Landing & Candidate Portal]
  T-08: CV Upload & Scanning Engine with Animated Review
  T-09: Seeker Feed & Search with Dynamic FRS Ranking & Behavioural Loop
  T-10: Job Detail View with Dual Projection Line Charts & Explanations
  T-11: Seeker Sidebar, Account Settings, Skills AI-Correction & Application Tracker
  T-12: Job vs Job Comparison Dashboard & Overlay Radar Chart

[Phase 4: Recruiter / HR Portal]
  T-13: HR Registration & JD Upload/Extraction
  T-14: HR KPI Dashboard & Managed Jobs Management with Real-Time Metrics
  T-15: HR Sidebar, Account Settings & JD Editor with Versioning
  T-16: Candidate Shortlist Board, PII-Redacted Profiles & Lifecycle Transition Actions
  T-17: Candidate vs Candidate Benchmarking & Overlay Radar Chart

[Phase 5: Quality Assurance & Launch]
  T-18: End-to-End User Simulation & Acceptance Verification
```

---

## 3. Detailed Task Specifications

### Phase 1: Foundation & Design System

#### T-01: Next.js & App Router Project Scaffolding
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-G01`, `REQ-G04`
- **Output:** Clean App Router structure in `app/` (`/`, `/signin`, `/signup/*`, `/seeker/*`, `/hr/*`), proxy rewrite to backend at `http://localhost:8095/api/:path*`.
- **DoD:** All top-level routes render, Next.js build succeeds with zero TypeScript errors.

#### T-02: Organic/Natural Design Tokens & Typography
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-G02`, `REQ-G03`
- **Output:** `app/globals.css` updated with exact CSS variables, Google Fonts (`Fraunces`, `Nunito`, `JetBrains Mono`), paper noise SVG overlay, and blob utilities.
- **DoD:** Wabi-sabi organic palette active, 4.5:1 text contrast verified, no sharp 90-degree corners.

#### T-03: Reusable Component Library
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-G02`, `REQ-G03`, `REQ-A04`
- **Output:** `frontend/components/`: Pill Button, CardNatural, PillInput, StatusPill, TermsModal, FloatingAddButton.
- **DoD:** Accessible focus rings, 44px minimum touch targets, SVG icons via Lucide React.

---

### Phase 2: Data & Backend Engine

#### T-04: SQLite Database Initialization
- **Agent:** Backend & Data Agent
- **Covers:** `REQ-G05`, `REQ-A07`
- **Output:** `product_api/db.py` creating tables in `product_api/var/app.db` matching schema in `04_DATA_AND_SCORING_SPEC.md`.
- **DoD:** Schema created, foreign keys and indexes operational.

#### T-05: Ingestion & Seeding Pipeline
- **Agent:** Backend & Data Agent
- **Covers:** `REQ-G05`, `REQ-S07`
- **Output:** `product_api/seed_db.py` parsing `data/australian_jobs.json` (461 jobs), `data/australian_jobs_dataset.csv`, and `data/australian_candidates.json` (320 CVs).
- **DoD:** 461 jobs and 320 candidates populated with normalized salaries, relative dates, and clean short descriptions.

#### T-06: Intelligence Engine Wiring & Formula API
- **Agent:** Backend & Data Agent
- **Covers:** `REQ-G06`, `REQ-S03`, `REQ-S05`, `REQ-S06`, `REQ-S15`, `REQ-S16`
- **Output:** API module importing Formulas 1 through 6 from `intelligence_engine/`, returning scores and behavioural adjustments.
- **DoD:** Score endpoints execute in < 20ms per job/candidate pair.

#### T-07: Auth & Protocol Mock Google OAuth2 Server
- **Agent:** Backend & Data Agent
- **Covers:** `REQ-L02`, `REQ-A03`, `REQ-A04`, `REQ-A05`
- **Output:** Email/password session endpoints, Terms & Conditions persistence, RFC 7636 PKCE local authorization server.
- **DoD:** Full auth loop functions without external Google network calls.

---

### Phase 3: Landing & Job Seeker Portal

#### T-08: CV Upload & Extraction Wizard
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-A01`, `REQ-A02`, `REQ-A06`, `REQ-A07`
- **Output:** Sign-up CV dropzone, staged extraction animation, review screen with AI badges, and empty-state **+** button.
- **DoD:** Candidate can upload file, review extracted competencies, set alias, and create account.

#### T-09: Seeker Job Feed & Search Interface
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-S01`, `REQ-S02`, `REQ-S03`, `REQ-S04`, `REQ-S05`, `REQ-S06`, `REQ-S07`, `REQ-S13`, `REQ-S14`, `REQ-S18`
- **Output:** `/seeker` feed with debounced search, filter chips, job cards with overall gauge, relative age, save/report/ignore actions.
- **DoD:** Ignore animates card removal with Undo; Save updates favourites instantly; search filters live.

#### T-10: Job Detail View & Mathematical Projections
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-S08`, `REQ-S09`, `REQ-S10`, `REQ-S11`, `REQ-S12`, `REQ-S17`
- **Output:** `/seeker/jobs/[id]` two-column layout: match progression line chart, gap reduction area chart, plain-English breakdown, apply drawer.
- **DoD:** Both line charts render with smooth curves; Apply logs application to HR; Ignore returns to feed.

#### T-11: Seeker Sidebar, Skills Correction & Applications
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-S19`, `REQ-S20`, `REQ-S21`, `REQ-S22`, `REQ-S23`, `REQ-S24`, `REQ-S25`, `REQ-S26`
- **Output:** Left sidebar navigation, `/seeker/account/skills` with AI verification badges, `/seeker/saved`, `/seeker/applications` with 8-stage interactive timeline.
- **DoD:** Seeker can edit AI skills and track application progress from Submitted to Hired.

#### T-12: Job vs Job Comparison Dashboard
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-S27`
- **Output:** `/seeker/compare` comparing 2–4 jobs with multi-layered radar chart, metric matrix, and Formula 3 JPI proximity advice.
- **DoD:** Concentric radar chart overlays job polygons with clean legend and tooltips.

---

### Phase 4: Recruiter / HR Portal

#### T-13: HR Registration & JD Parser
- **Agent:** Frontend UI/UX Agent + Backend
- **Covers:** `REQ-H01`, `REQ-H02`
- **Output:** `/signup/hr` with JD upload/paste parsing, or skip to empty-state **+ Add Job** homepage.
- **DoD:** Recruiter can register with or without JD.

#### T-14: HR KPI Dashboard & Job Manager
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-H03`, `REQ-H04`, `REQ-H05`
- **Output:** `/hr` KPI cards (Total, Active, Expired, Hired, Rejected) and `/hr/jobs` listing with Appearances, Views, and Applicants metrics.
- **DoD:** Real-time metrics compute accurately from database events.

#### T-15: HR Sidebar, Settings & JD Editor [COMPLETED]
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-H06`, `REQ-H07`, `REQ-H08`
- **Output:** HR sidebar, company settings, `/hr/jobs/[id]/edit` allowing modification of extracted requirements with change history.
- **DoD:** Edits persist and trigger re-ranking of applicant shortlist.

#### T-16: Candidate Shortlist Board & Lifecycle Actions [COMPLETED]
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-H09`, `REQ-H10`, `REQ-H11`
- **Output:** `/hr/candidates` board showing applicant cards with alias, ANZSCO match, gap pill, TSS score; accordion expand with PII-redacted CV and lifecycle transition buttons.
- **DoD:** HR can shortlist, schedule interview, make offer, or reject applicant; updates reflect in seeker timeline immediately.

#### T-17: Candidate vs Candidate Benchmarking [COMPLETED]
- **Agent:** Frontend UI/UX Agent
- **Covers:** `REQ-H12`
- **Output:** `/hr/compare` multi-candidate radar chart overlaying skills, experience, and merit + Formula 4 Head-to-Head delta.
- **DoD:** Overlaid radar chart renders accurately for candidates applying for the same job.

---

### Phase 5: Verification & Delivery

#### T-18: End-to-End Simulation & Acceptance Testing
- **Agent:** QA & Verification Agent
- **Covers:** All `REQ-*` requirements
- **Output:** Verification against `08_QA_ACCEPTANCE.md` checklist across desktop, tablet, and mobile viewports.
- **DoD:** 100% of acceptance criteria verified and functional.
