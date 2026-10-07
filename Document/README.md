# Master Documentation Hub — Jinder Platform

Welcome to the centralized documentation directory for the **Jinder Platform**. All product specifications, architectural blueprints, operational guides, governance rules, and prompt contracts are consolidated here.

---

## 🗂️ Documentation Sections

```
Document/
├── guides/          # 🚀 Getting started, system overview & live demo scripts
├── architecture/    # 📐 Deep technical architecture, database schemas, formulas & QA test plan
├── sdd/             # 📋 Software Design Description (PRD, feature specs, user flows, stories)
├── prompt/          # 💬 Prompt engineering principles, guardrails & API contracts
└── ai_rule/         # 🛡️ AI governance boundaries, ethical constraints & 10 core safety rules
```

---

## 1. 🚀 Guides & Operational Walkthroughs (`guides/`)

| Document | Purpose |
|---|---|
| [**`01_GETTING_STARTED.md`**](guides/01_GETTING_STARTED.md) | Prerequisites (Python 3.9+, zero `pip install`), quick launch commands, demo accounts, and test execution. |
| [**`02_SYSTEM_ARCHITECTURE_GUIDE.md`**](guides/02_SYSTEM_ARCHITECTURE_GUIDE.md) | High-level decomposition of frontend, backend, engine, persistence, and interactive presentation tiers. |
| [**`03_OPERATION_AND_DEMO_WALKTHROUGH.md`**](guides/03_OPERATION_AND_DEMO_WALKTHROUGH.md) | Step-by-step hackathon judging script for Talent Journey, Employer Journey, and Interactive Telemetry walkthroughs. |

---

## 2. 📐 Architecture Details & AI Testing (`architecture/`)

| Document | Area | Description |
|---|---|---|
| [**`SYSTEM_ARCHITECTURE_DIAGRAMS.md`**](architecture/SYSTEM_ARCHITECTURE_DIAGRAMS.md) | System Blueprints | End-to-end architecture diagrams, Mermaid specifications, and PNG diagram exports. |
| [**`FRONTEND_ARCHITECTURE_DETAIL.md`**](architecture/FRONTEND_ARCHITECTURE_DETAIL.md) | Client Tier | Zero-build Vanilla ES6 SPA, reactive stores (`Session`, `CompareStore`), hash routing, and CSP compliance. |
| [**`BACKEND_ARCHITECTURE_DETAIL.md`**](architecture/BACKEND_ARCHITECTURE_DETAIL.md) | Server Tier | Python standard library REST API, route dispatcher, sliding-window rate limiting, and RBAC guards. |
| [**`DATA_MODELING_ARCHITECTURE_DETAIL.md`**](architecture/DATA_MODELING_ARCHITECTURE_DETAIL.md) | Persistence Tier | The 22 SQLite tables (schema version 2) in 6 groups, an ERD built from `schema.sql`, the core columns, JSON shapes (snapshot, match, parse result), application status values, data rules and the taxonomy in memory. |
| [**`CLOUD_MIGRATION_PLAN.md`**](architecture/CLOUD_MIGRATION_PLAN.md) | Cloud (proposal) | Plan to move to AWS (Sydney): CloudFront, ECS Fargate, RDS PostgreSQL, S3, SQS, SES, Bedrock; a Bronze / Silver / Gold data lake; a 12-week migration plan and monthly cost estimates (Pilot, Growth, Scale). |
| [**`DATA_FLOW_ARCHITECTURE.md`**](architecture/DATA_FLOW_ARCHITECTURE.md) | Data Flow | How data moves from the source files to the screen: the five layers, read and write flows, file parsing, scores on read, the privacy projection, the steps after the interview (offer, answer, feedback), compare, export and delete, notifications, events, and data classes. |
| [**`FORMULA_ARCHITECTURE_DETAIL.md`**](architecture/FORMULA_ARCHITECTURE_DETAIL.md) | Intelligence Engine | Mathematical definitions, variables, bounds, and worked examples for Formulas F-01 to F-06. |
| [**`PLAN_TEST_FOR_AI.md`**](architecture/PLAN_TEST_FOR_AI.md) | AI Test Plan | 5-tier QA hierarchy, risk-based validation matrix, and behavioral eval suite benchmarked on Project-Aegis. |

---

## 3. 📋 Software Design Description (`sdd/`)

| Document | Description |
|---|---|
| [**`01_SYSTEM_OVERVIEW.md`**](sdd/01_SYSTEM_OVERVIEW.md) | High-level system goals, modular decomposition, and cross-cutting architectural patterns. |
| [**`02_PRODUCT_REQUIREMENTS_DOCUMENT.md`**](sdd/02_PRODUCT_REQUIREMENTS_DOCUMENT.md) | Product vision, target personas, problem statement, and success metrics. |
| [**`03_FEATURE_SPECIFICATIONS.md`**](sdd/03_FEATURE_SPECIFICATIONS.md) | Comprehensive engineering specifications for core features (feed, gap analysis, compare, telemetry). |
| [**`04_USER_FLOW_SPECIFICATION.md`**](sdd/04_USER_FLOW_SPECIFICATION.md) | End-to-end state machines and screen transition diagrams for Talent and Employer personas. |
| [**`05_USER_STORIES_AND_ACCEPTANCE_CRITERIA.md`**](sdd/05_USER_STORIES_AND_ACCEPTANCE_CRITERIA.md) | Formal agile user stories with Gherkin-style Given/When/Then acceptance criteria. |
| [**`06_TECHNICAL_REQUIREMENTS.md`**](sdd/06_TECHNICAL_REQUIREMENTS.md) | Security constraints, performance SLAs, browser compatibility matrices, and storage quotas. |

**Gap analysis:** [**`GAP_ANALYSIS.md`**](GAP_ANALYSIS.md) lists what the current app does not have yet, compared with `06_TECHNICAL_REQUIREMENTS.md` (P0, P1, P2, with code evidence). Checked on 8 October 2026.

---

## 4. 💬 Prompt Engineering & API Contracts (`prompt/`)

| Document | Description |
|---|---|
| [**`PROMPT_ENGINEERING_PRINCIPLES.md`**](prompt/PROMPT_ENGINEERING_PRINCIPLES.md) | 6 core prompt engineering principles, anti-hallucination constraints, injection quarantining, and production system prompts. |
| [**`API_CONTRACT_PROMPT.md`**](prompt/API_CONTRACT_PROMPT.md) | Definitive frontend-to-backend API contract specifications and request/response JSON schemas. |

---

## 5. 🛡️ AI Governance & Safety Boundaries (`ai_rule/`)

| Document | Description |
|---|---|
| [**`AI_GOVERNANCE_AND_BOUNDARIES.md`**](ai_rule/AI_GOVERNANCE_AND_BOUNDARIES.md) | Authoritative 10 Core Architectural Rules, ethical boundaries, Zero-PII masking, and human-in-the-loop requirements. |

---

## 6. 🎨 Interactive Presentation & Administrative Portals

For interactive demonstration and live telemetry, open the standalone HTML applications in [`Presentation/`](../Presentation/README.md):

1. [**`Presentation/formulas_presentation.html`**](../Presentation/formulas_presentation.html) — **Canonical Mathematical Engine Deck (ASD-STE100)**:
   - **All 6 Formulas Grid:** 100vh single-screen layout showing all 6 formulas simultaneously without page scrolling.
   - **Live Parameter Workbench:** Interactive simulation panel with continuous gradient sliders (`#6868f7` $\to$ `#a855f7` $\to$ `#ffa340`), real-time calculation, and step-by-step arithmetic verification.
   - **KaTeX Vector Equations:** High-clarity mathematical notation and calibrated Australian ICT benchmarks.
   - **Standards:** 100% Australian English (`en-AU`), Talent / Employer terminology, and official Jinder SVG vector branding.

2. [**`Presentation/admin.html`**](../Presentation/admin.html) — **Admin Control Center & Data Flow Telemetry**:
   - **Live SQLite WAL Telemetry:** Active database metrics (file size, page counts, journal mode) and verified entity population (**51 Talents**, **1 Demo Employer**, 54 Job Requisitions).
   - **5-Stage Interactive Data Flow Pipeline:** Click-to-inspect pipeline stages (Ingestion $\to$ Taxonomy Translation $\to$ Mathematical Engine $\to$ SQLite WAL $\to$ Shortlist Delivery) with live query telemetry.
   - **22 Tables SQLite Explorer:** Tabular explorer with instant search, schema inspection, pagination, and safe read-only SQL runner.

3. [**`Presentation/project_presentation.html`**](../Presentation/project_presentation.html) — **System Architecture Pitch Deck**:
   - Interactive slide deck covering Australian skilled migration challenges, capability alignment architecture, ethical AI principles, and platform demonstration.
