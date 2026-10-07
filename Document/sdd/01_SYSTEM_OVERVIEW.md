# Software Design Description (SDD) — Jinder Platform

## 1. Introduction

### 1.1 Purpose
The purpose of this Software Design Description (SDD) is to provide a comprehensive architectural and behavioural specification for **Jinder** — an Autonomous Capability Alignment Platform designed to connect international students and skilled migrants with Australian technology employers.

### 1.2 System Scope
Jinder acts as a two-sided marketplace and intelligence alignment layer:
- **Talent Side:** Candidates upload unstructured international resumes, which are parsed and translated into standardized Australian ICT skills, accompanied by personalized learning pathways and job proximity calculations.
- **Employer Side:** Hiring managers and recruiters post technical job requisitions with explicit skill weightings and review anonymized talent profiles (using Wildlife Animal Aliases) matched via deterministic mathematical algorithms (F-01 to F-06).

---

## 2. System Architecture & High-Level Design

### 2.1 Architectural Pattern
Jinder implements a decoupled, event-driven client-server architecture:
```
+-------------------------------------------------------------------------+
|                           CLIENT TIER (SPA)                             |
|  - Vanilla HTML5 / ES6 Modules / CSS3 Custom Properties                 |
|  - Modern Dark Jinder Theme (Navy #0E1726, Violet Gradient, Coral Accent)|
|  - State Management: Session Controller & CompareStore (Reactive)      |
+-------------------------------------------------------------------------+
                                    |
                            HTTP/1.1 REST API
                            Bearer Token Auth
                                    v
+-------------------------------------------------------------------------+
|                        APPLICATION SERVER TIER                          |
|  - Python 3.9+ Zero-Dependency Lightweight REST Service                 |
|  - Role-Based Access Control (RBAC: Talent vs Employer vs Public)       |
|  - CV Ingestion Pipeline & PII Stripping Filter                         |
|  - Deterministic Intelligence Engine (Formulas F-01 to F-06)            |
+-------------------------------------------------------------------------+
                                    |
                            SQLite Transaction Engine
                            WAL Mode / Foreign Keys
                                    v
+-------------------------------------------------------------------------+
|                           DATA PERSISTENCE TIER                         |
|  - Relational Models: Users, Talents, Employers, Jobs, Applications     |
|  - Knowledge Base: Australian ICT Taxonomy (172 Skills, 53 Roles)       |
|  - Synthetic Test Bench: 50 Australian Jobs & 50 Talent Profiles        |
+-------------------------------------------------------------------------+
```

---

## 3. Documents in the SDD Package

| Section | Document | Summary |
|---|---|---|
| **01** | [**`01_SYSTEM_OVERVIEW.md`**](01_SYSTEM_OVERVIEW.md) | This document: Architecture overview, goals, and system decomposition. |
| **02** | [**`02_PRODUCT_REQUIREMENTS_DOCUMENT.md`**](02_PRODUCT_REQUIREMENTS_DOCUMENT.md) | Product vision, target personas, problem definition, and KPIs. |
| **03** | [**`03_FEATURE_SPECIFICATIONS.md`**](03_FEATURE_SPECIFICATIONS.md) | Detailed specifications for all 7 platform features and acceptance criteria. |
| **04** | [**`04_USER_FLOW_SPECIFICATION.md`**](04_USER_FLOW_SPECIFICATION.md) | End-to-end screen-by-screen navigation and interaction flows. |
| **05** | [**`05_USER_STORIES_AND_ACCEPTANCE_CRITERIA.md`**](05_USER_STORIES_AND_ACCEPTANCE_CRITERIA.md) | Complete agile user stories broken down by feature. |
| **06** | [**`06_TECHNICAL_REQUIREMENTS.md`**](06_TECHNICAL_REQUIREMENTS.md) | Non-functional requirements, security, latency, and accessibility. |
