# Jinder — Backend Development & API Integration Guide

> **Note.** This document describes the earlier prototype (version 1). Its examples use jobs of other fields of work, and its `/api/seeker/projection` endpoint and the 12-month chart are removed in version 2.
> The product API is in `jinder_platform/docs/API_NOTES.md`. The formulas are in `02_FORMULAS_MATHEMATICAL_SPEC.md`. Keep this file only for the history of the prototype.

**Target Audience:** Backend Engineers, Fullstack Developers, Platform Architects  
**Architecture:** Python 3.9+ Standard Library / Zero-Dependency Mock Server + SQLite (WAL Mode) + Deterministic Mathematical Engine  

---

## 1. System Architecture Overview

**Jinder** ("Tinder for Jobs") uses an autonomous capability alignment engine driven by 6 exact mathematical scoring models. It eliminates coarse heuristics, keyword search limitations, and LLM non-determinism from candidate job matching.

```
                         [Client Applications / Frontend]
                                        │
                                        ▼ (HTTP / REST JSON)
                      ┌────────────────────────────────────┐
                      │    backend/server.py (Port 8095)   │
                      └─────────┬──────────────────┬───────┘
                                │                  │
            (SQLite DB)         ▼                  ▼   (Formulas Wrapper)
        ┌─────────────────────────┐        ┌───────────────────────────┐
        │     backend/db.py       │        │     backend/scores.py     │
        │     (var/app.db)        │        └─────────────┬─────────────┘
        └─────────────────────────┘                      │
                                                         ▼
                                            ┌──────────────────────────┐
                                            │   intelligence_engine/   │
                                            │   - 01_skill_matching    │
                                            │   - 02_skill_gap         │
                                            │   - 03_job_comparison    │
                                            │   - 04_candidate_bench   │
                                            │   - 05_seeker_feed_rank  │
                                            │   - 06_recruiter_search  │
                                            └──────────────────────────┘
```

### Core Architecture Commitments:
1. **Zero Third-Party Package Dependencies:** The REST API server and scoring models run entirely on Python's built-in standard library (`http.server`, `sqlite3`, `json`, `math`, `uuid`, `urllib`).
2. **Sub-5 Millisecond Execution:** Every formula (F-01 through F-06) executes deterministically in less than 5ms per candidate-job calculation.
3. **Pre-Populated Australian Datasets:** `seed_db.py` populates 461 real Australian job requisitions and 320 candidate profiles with verified skill matrices.
4. **Standard REST & CORS:** All endpoints respond with standard JSON and accept cross-origin requests (`Access-Control-Allow-Origin: *`).

---

## 2. Quickstart & Server Launch

### One-Command Server Start
From the root of `jinder_backend_engine/`, run:
```bash
python3 start_server.py
```
This script will:
1. Verify if `backend/var/app.db` exists. If not, it runs `backend/seed_db.py` to seed the database automatically.
2. Launch the HTTP server on `http://localhost:8095` (or custom `$PORT`).

### Verification Suite
Run the mathematical test suite:
```bash
python3 run_verification.py
```
This tests all 6 formulas and backend scoring calculations in ~2 seconds.

---

## 3. Database Schema (`backend/db.py`)

The SQLite database (`backend/var/app.db`) uses Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) and foreign keys.

### Tables Summary:
- **`users`**: Authentication credentials, roles (`seeker`, `hr`, `admin`), terms acceptance.
- **`seeker_profiles`**: Job seeker profile, legal name (PII), public alias (`SilverKangaroo84`), years experience, education, target ANZSCO code.
- **`hr_profiles`**: Recruiter account, company name, Australian ABN.
- **`jobs`**: 461 Australian vacancies with title, company, salary min/max, ANZSCO code, required skills JSON, location.
- **`seeker_saved_jobs`**: Liked jobs (swiped right). Triggers positive affinity (+10% employer, +5% category in FRS).
- **`seeker_dismissed_jobs`**: Ignored jobs (swiped left). Tracks ignore count (≥ 3 triggers -25% penalty).
- **`matches`**: Confirmed matches between candidates and employers.
- **`audit_logs`**: System event logs for compliance audit.

---

## 4. Key REST API Endpoints (`backend/server.py`)

All endpoints return JSON and accept standard HTTP headers (`Authorization: Bearer user_seeker_demo` for authenticated routes).

### 4.1 Public & Telemetry
- `GET /api/public/stats`
  - Returns total active jobs (461), verified candidates (320), average match score, platform uptime.

### 4.2 Job Seeker Experience (Jinder Feed)
- `GET /api/seeker/feed`
  - Returns personalized job cards ranked by **Formula 5 (FRS)** and behavioral affinity adjustments.
  - Query parameters: `?page=1&limit=20&sector=Technology&min_salary=100000`
- `POST /api/seeker/swipe`
  - Records a card swipe:
    ```json
    {
      "job_id": "job_001",
      "action": "like" // or "dismiss"
    }
    ```
- `GET /api/seeker/profile`
  - Returns candidate profile and verified competency matrix.
- `PUT /api/seeker/profile`
  - Updates candidate skills, target ANZSCO code, or preferred location.
- `GET /api/seeker/projection`
  - Returns 12-month dual-line projection curves (baseline vs accelerated bridge) based on candidate's skill gaps.

### 4.3 Recruiter Talent Search & Benchmark
- `POST /api/recruiter/search`
  - Ranks candidates against a requisition using **Formula 6 (TSS)**.
  - Body:
    ```json
    {
      "job_id": "job_042",
      "min_experience_years": 5.0,
      "required_skills": ["SQL", "Python", "Data Modeling", "Snowflake"],
      "limit": 10
    }
    ```
  - **Zero-PII Response:** Candidate names are masked as Australian Wildlife Aliases (`SilverKangaroo84`).
- `POST /api/benchmark/candidates`
  - Side-by-side candidate comparison using **Formula 4 (RMS)**.
  - Body: `{"candidate_ids": ["cand_001", "cand_002"]}`
- `POST /api/compare/jobs`
  - Multi-job career proximity comparison using **Formula 3 (JPI)**.
  - Body: `{"job_ids": ["job_001", "job_002", "job_003"]}`

---

## 5. Integrating the Intelligence Engine

The calculation engine is accessed via `backend/scores.py`.

```python
import scores

# 1. Formula 1: Candidate vs ANZSCO Skill Match
res_f1 = scores.get_skill_match_score(candidate_dict, anzsco_code="261313")
print("Overall Match:", res_f1["overall_score"])

# 2. Formula 2: Skill Gap Severity & Job Readiness
res_f2 = scores.get_skill_gap_analysis(candidate_dict, job_dict)
print("Readiness Score (JRS):", res_f2["job_readiness_score"])
print("Estimated Months to Close:", res_f2["estimated_bridge_months"])

# 3. Formula 5: Job Seeker Feed Ranking (FRS)
res_f5 = scores.calculate_feed_score(candidate_dict, job_dict)
print("Base FRS:", res_f5["feed_ranking_score"])

# Apply behavioral feedback (+10% save affinity, -25% ignore penalty)
final_score = scores.apply_behavioural_ranking(
    base_frs=res_f5["feed_ranking_score"],
    job=job_dict,
    saved_employer_ids={"Atlassian", "Canva"},
    saved_categories={"Technology"},
    ignored_employer_counts={"OldCorp": 4}
)
```

---

## 6. Extending or Porting to Another Stack

If your team is porting this to **FastAPI**, **Node.js (Nest/Express)**, or **Go**:
- The mathematical logic in `intelligence_engine/*.py` is pure arithmetic (logarithms, exponential penalties, Gaussian curves, weighted linear combinations).
- All formula formulas are fully documented with worked step-by-step examples in [`02_FORMULAS_MATHEMATICAL_SPEC.md`](02_FORMULAS_MATHEMATICAL_SPEC.md).
- The REST API contracts in [`03_API_SPEC.md`](03_API_SPEC.md) define the canonical request/response shapes.
