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
