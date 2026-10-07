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
