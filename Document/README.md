# Document: Architecture Details & AI Testing Framework

This directory houses the comprehensive architectural specifications and quality assurance documentation for the **Jinder Platform**.

## Document Index

| Document | Area | Description |
|---|---|---|
| [**`SYSTEM_ARCHITECTURE_DIAGRAMS.md`**](SYSTEM_ARCHITECTURE_DIAGRAMS.md) | System Blueprints | End-to-end architecture diagrams, Mermaid specifications, and publication-ready PNG diagram exports. |
| [**`FRONTEND_ARCHITECTURE_DETAIL.md`**](FRONTEND_ARCHITECTURE_DETAIL.md) | Client Tier | Zero-build Vanilla ES6 SPA, reactive stores (Session, CompareStore), hash routing, and CSP compliance. |
| [**`BACKEND_ARCHITECTURE_DETAIL.md`**](BACKEND_ARCHITECTURE_DETAIL.md) | Server Tier | Python standard library REST API, route dispatcher, sliding-window rate limiting, and RBAC guards. |
| [**`DATA_MODELING_ARCHITECTURE_DETAIL.md`**](DATA_MODELING_ARCHITECTURE_DETAIL.md) | Persistence Tier | SQLite WAL relational schemas (`users`, `talents`, `employers`, `jobs`, `applications`) and in-memory taxonomy inverted index. |
| [**`FORMULA_ARCHITECTURE_DETAIL.md`**](FORMULA_ARCHITECTURE_DETAIL.md) | Intelligence Engine | Mathematical definitions, variables, bounds, and worked examples for Formulas F-01 to F-06. |
| [**`PLAN_TEST_FOR_AI.md`**](PLAN_TEST_FOR_AI.md) | AI Test Plan | 5-tier QA hierarchy, risk-based validation matrix, and behavioral eval suite benchmarked on Project-Aegis. |

---

## Interactive Presentation & Administrative Portals

For live interactive inspection and demonstration, see the zero-build HTML applications in [`Presentation/`](../Presentation/README.md):

1. [**`Presentation/formulas_presentation.html`**](../Presentation/formulas_presentation.html) — **Canonical Mathematical Engine Deck (ASD-STE100)**:
   - **All 6 Formulas Grid:** 100vh single-screen view displaying all 6 canonical formulas (F-01 through F-06) simultaneously with zero page scrolling.
   - **Live Parameter Workbench:** Interactive simulation panel on the left with continuous gradient sliders (`#6868f7` $\to$ `#a855f7` $\to$ `#ffa340`), real-time calculation, and step-by-step worked numerical examples.
   - **KaTeX Variable Table:** Crisp vector mathematical variables with calibrated Australian industry values.
   - **Strict Standards:** 100% Australian English (`en-AU`), Talent / Employer terminology, and official Jinder SVG branding.

2. [**`Presentation/admin.html`**](../Presentation/admin.html) — **Admin Control Center & Data Flow Telemetry**:
   - **Live SQLite WAL Metrics:** Active page count, database file size (0.95 MB), journal mode, and verified role breakdown (**51 Talents**, **1 Demo Employer**).
   - **5-Stage Data Flow Pipeline Chart:** Visual pipeline (Ingestion $\to$ Taxonomy Translation $\to$ Mathematical Engine $\to$ SQLite WAL $\to$ Shortlist Delivery) with interactive stage inspection and live query telemetry.
   - **22 Tables SQLite Explorer:** Filter, search, and paginate through all 22 database tables with a built-in Safe SQL runner.
   - **Safe SQL Runner:** In-browser query terminal with syntax checks and safe read-only query execution.

