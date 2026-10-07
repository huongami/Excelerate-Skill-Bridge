# Jinder System Architecture Guide

## 1. High-Level Architectural Decomposition

The repository is modularized into specialized tiers:

```
Excelerate-Skill-Bridge/
│
├── AI Rule/                # AI boundaries, capabilities, 10 core safety rules
├── Skill/                  # Modular AI skills (Extraction, Gap Analysis, Formulas, PII Masking)
├── SDD/                    # Software Design Description (PRD, Specs, User Flows, Stories)
├── Prompt/                 # Prompt Engineering principles, system templates, API contract
├── Readme/                 # Comprehensive documentation guides and walkthroughs
├── Presentation/           # Interactive HTML pitch decks and mathematical formula presentations
├── Data/                   # Verified synthetic benchmarks and Australian legal provenance statement
├── Document/               # Deep Architecture Details (Frontend, Backend, Data, Formulas, AI Test Plan)
│
├── jinder_platform/        # Running Python HTTP/REST Backend Server & SQLite Database
├── jinder_frontend/        # Client Single Page Application (HTML/CSS/JS)
├── jinder_backend_engine/  # Intelligence Engine (Formulas F-01 to F-06) & reference taxonomy
└── old_version/            # Archived legacy prototype components
```

---

## 2. Core Functional Modules

### A. Intelligence Engine (`jinder_backend_engine`)
Contains pure mathematical implementations of Formulas F-01 to F-06:
- Implemented as stateless pure Python functions.
- Fully unit-tested with mathematical bounds verification ($[0, 100]$).
- Imports the Australian ICT Taxonomy from `data/reference/ict_taxonomy.json`.

### B. Platform Server (`jinder_platform`)
- High-performance, zero-dependency HTTP server utilizing Python's `http.server`.
- In-memory routing engine with regex URL matching.
- SQLite transactional database (`jinder.db`) configured with Write-Ahead Logging (`WAL`) mode.
- RESTful JSON API handling authentication, job postings, candidate applications, and side-by-side comparisons.

### C. Frontend Web Application (`jinder_frontend/app`)
- Single Page Application (SPA) driven by vanilla JavaScript ES6 modules.
- Modern responsive layout utilizing CSS variables and the Jinder Design System.
- Rich interactive data visualizations (SVGs for radar charts, skill breakdown bars, match badges).
- No build step required (runs directly in modern browsers).

### D. Interactive Presentation & Administrative Portals (`Presentation/`)
- **Canonical Mathematical Formulas Deck (`formulas_presentation.html`):** 100vh single-screen layout presenting all 6 canonical formulas (F-01 to F-06) simultaneously with zero page scrolling. Features an interactive parameter workbench with continuous gradient sliders (`#6868f7` $\to$ `#a855f7` $\to$ `#ffa340`), real-time calculation, and step-by-step arithmetic verification.
- **Admin Control Center & Data Flow Telemetry (`admin.html`):** Enterprise administration dashboard displaying live SQLite WAL performance metrics, a 5-stage interactive Data Flow Pipeline chart, a 22-table database relational explorer, and a safe read-only SQL runner.
- **Architecture Pitch Deck (`project_presentation.html`):** Multi-slide interactive presentation covering Australian skilled migration challenges, capability alignment architecture, and ethical AI principles.

