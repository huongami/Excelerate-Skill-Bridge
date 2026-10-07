# 04 — Data & Scoring Integration Specification

Source of truth for data models, database schema, data seeding, formula wiring to `intelligence_engine/`, behavioural ranking adjustments, and analytical chart mathematics.

---

## 1. Storage Architecture

The Product API utilizes an embedded **SQLite 3 database** with WAL (Write-Ahead Logging) enabled, located at `product_api/var/app.db`. SQLite provides instantaneous local queries (< 2ms), zero external infrastructure dependencies, full transactional ACID guarantees, and seamless portability across evaluation environments.

---

## 2. Relational Database Schema

```sql
-- 1. Users and Authentication
CREATE TABLE users (
    id TEXT PRIMARY KEY,                       -- UUID
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,                       -- NULL for pure Google OAuth users
    role TEXT NOT NULL CHECK(role IN ('seeker', 'hr', 'admin')),
    auth_provider TEXT NOT NULL DEFAULT 'local', -- 'local' or 'google'
    google_sub TEXT UNIQUE,
    terms_version TEXT NOT NULL,
    terms_accepted_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Job Seeker Profiles
CREATE TABLE seeker_profiles (
    id TEXT PRIMARY KEY,                       -- Matches users.id
    alias TEXT UNIQUE NOT NULL,                -- Public identity for HR view (REQ-A07)
    legal_name TEXT NOT NULL,                  -- PII (scrubbed from HR view)
    phone TEXT,
    origin_country TEXT NOT NULL,
    current_title TEXT NOT NULL,
    years_experience REAL NOT NULL,
    highest_education TEXT,
    target_anzsco_code TEXT NOT NULL,
    target_anzsco_title TEXT NOT NULL,
    preferred_location TEXT NOT NULL DEFAULT 'Sydney',
    cv_file_name TEXT,
    cv_raw_text TEXT,
    profile_completeness REAL NOT NULL DEFAULT 85.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Seeker Skills & Provenance
CREATE TABLE seeker_skills (
    id TEXT PRIMARY KEY,                       -- UUID
    seeker_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    skill_type TEXT NOT NULL CHECK(skill_type IN ('Direct', 'Transferable')),
    evidence_quote TEXT,
    source TEXT NOT NULL CHECK(source IN ('AI_EXTRACTED', 'USER_CONFIRMED', 'USER_EDITED', 'USER_ADDED')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id) ON DELETE CASCADE
);

-- 4. Employers / HR Profiles
CREATE TABLE hr_profiles (
    id TEXT PRIMARY KEY,                       -- Matches users.id
    company_name TEXT NOT NULL,
    company_website TEXT,
    company_about TEXT,
    recruiter_name TEXT NOT NULL,
    recruiter_title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Job Listings (Seeded from Australian Jobs Corpus)
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,                       -- e.g. 'adzuna_5901612689' or UUID
    employer_id TEXT,                          -- Linked HR profile (or NULL for seeded unmanaged jobs)
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    short_description TEXT NOT NULL,           -- Clean excerpt <= 160 chars (REQ-S04)
    full_description TEXT NOT NULL,
    location TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    category TEXT NOT NULL,                    -- 8 Australian Sectors
    anzsco_code TEXT NOT NULL,                 -- 6-digit code
    anzsco_title TEXT NOT NULL,
    employment_type TEXT NOT NULL DEFAULT 'Full-time',
    salary_min REAL NOT NULL,
    salary_max REAL NOT NULL,
    salary_display TEXT NOT NULL,
    requirements_json TEXT NOT NULL,           -- JSON array of strings
    source_platform TEXT NOT NULL,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'expired', 'closed', 'under_review')),
    posted_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. User Engagement & Tracking (Feeds HR Metrics REQ-H05)
CREATE TABLE job_impressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    user_id TEXT,                              -- Optional (tracks unique seeker views)
    session_id TEXT NOT NULL,
    viewed_date DATE NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE job_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    seeker_id TEXT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

-- 7. Seeker Saved Jobs (Favourites REQ-S13, REQ-S23)
CREATE TABLE saved_jobs (
    seeker_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(seeker_id, job_id),
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 8. Seeker Ignored Jobs (Feed Exclusions REQ-S12, REQ-S18)
CREATE TABLE ignored_jobs (
    seeker_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    ignored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(seeker_id, job_id),
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 9. Job Discrepancy Reports (REQ-S14)
CREATE TABLE job_reports (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    seeker_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    details TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'resolved_corrected', 'resolved_dismissed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id)
);

-- 10. Job Applications & Timeline Checkpoints (REQ-S17, REQ-S24, REQ-H09)
CREATE TABLE applications (
    id TEXT PRIMARY KEY,                       -- UUID
    job_id TEXT NOT NULL,
    seeker_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted' CHECK(status IN (
        'submitted', 'cv_scanning', 'under_review', 'shortlisted', 
        'interview', 'final_assessment', 'offer', 'hired', 'rejected', 'withdrawn'
    )),
    overall_score_snapshot REAL NOT NULL,      -- FRS at time of application
    anzsco_match_snapshot REAL NOT NULL,       -- SMF score
    skill_gap_snapshot REAL NOT NULL,          -- GSI score
    tss_score_snapshot REAL NOT NULL,          -- Recruiter TSS score
    message_to_employer TEXT,
    share_gaps_consent INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id) ON DELETE CASCADE
);

CREATE TABLE application_timeline_events (
    id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    checkpoint TEXT NOT NULL,                  -- Status stage name
    note TEXT,
    actor TEXT NOT NULL,                       -- 'Candidate', 'Employer', or 'System'
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interview_date TIMESTAMP,                  -- Populated for interview checkpoint
    interview_mode TEXT,                       -- 'Video', 'Phone', 'On-site'
    interview_link TEXT,
    FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- 11. Multi-Job / Multi-Candidate Comparison Tray (REQ-S27, REQ-H12)
CREATE TABLE compare_tray (
    user_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,                   -- job_id or candidate_id
    tray_type TEXT NOT NULL CHECK(tray_type IN ('jobs', 'candidates')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, entity_id)
);
```

---

## 3. Data Ingestion & Seeding Pipeline

### 3.1 Source File Inventory

1. `data/australian_jobs.json`: 461 real vacancies across 8 standard Australian industry sectors.
2. `data/australian_jobs_dataset.csv`: Historical publication timestamps (`date_posted`).
3. `data/australian_candidates.json`: 320 real, sanitized international candidates across 11 source countries.

### 3.2 Job Schema Reconciliation

The jobs dataset contains two historical JSON format variants:
- **Variant A (390 jobs):** Fields include `id`, `title`, `company`, `location`, `category`, `anzsco` ("ANZSCO 254411 (Registered Nurse)"), `requirements` (list), `description`, `created` (ISO timestamp).
- **Variant B (71 jobs):** Fields include `job_id`, `title`, `company`, `location`, `industry_category`, `anzsco_code`, `salary_min`, `salary_max`, `ingested_at`.

The ingestion script (`product_api/seed_db.py`) automatically standardizes both variants:
1. **ANZSCO Code Normalization:** Extracts 6-digit standard code (e.g. `254411`) and maps to the official ABS ANZSCO Title from `intelligence_engine/01_skill_matching_model.py`.
2. **Salary Normalization:** Where numeric bounds exist, values are preserved. For rows stating "Market Competitive (AUD)", midpoints are calibrated against Australian Sector Benchmarks:
   - Technology & Data: $125,000 AUD
   - Healthcare & Nursing: $95,000 AUD
   - Engineering & Construction: $120,000 AUD
   - Finance & Accounting: $105,000 AUD
   - Supply Chain & Logistics: $92,000 AUD
   - Marketing & Communications: $90,000 AUD
   - Operations & Administration: $80,000 AUD
   - Hospitality & Service: $65,000 AUD
3. **Posting Timestamp Calibration (REQ-S07):** Timestamps from `data_posted` or `created` are imported directly. If missing, dates are assigned deterministically between 1 and 28 days prior to the current system date, enabling clean relative age labels ("Posted 3 days ago", "Posted 13 days ago").
4. **Short Description Generation (REQ-S04):** Clean, sentence-bounded text summary truncated at 160 characters.

---

## 4. Formula Integration with Intelligence Engine

Skill Bridge 2.0 directly imports and executes the peer-reviewed mathematical modules located in `intelligence_engine/`:

```
┌────────────────────────────────────────────────────────┐
│               INTELLIGENCE ENGINE SUITE                │
├────────────────────────────────────────────────────────┤
│  01_skill_matching_model.py          --> Formula 1 (SMF)│
│  02_skill_gap_analysis.py            --> Formula 2 (SGF)│
│  03_job_to_job_comparison.py         --> Formula 3 (JJF)│
│  04_candidate_benchmarking.py        --> Formula 4 (CCF)│
│  05_job_seeker_ranking_feed.py       --> Formula 5 (JFR)│
│  06_recruiter_candidate_ranking.py   --> Formula 6 (TSR)│
└────────────────────────────────────────────────────────┘
```

### 4.1 Formula 1: Candidate vs ANZSCO Match (SMF)
- Module: `intelligence_engine.01_skill_matching_model.evaluate_skill_match(candidate, anzsco_code)`
- Produces: Match Score (0–100%), Match Tier (`Direct Industry Alignment`, `Transferable Cross-Sector`, `Emerging Career Bridge`), and sub-metrics ($S_{\text{tree}}, S_{\text{direct}}, S_{\text{trans}}, \Phi$).

### 4.2 Formula 2: Skill Gap Severity (SGF)
- Module: `intelligence_engine.02_skill_gap_analysis.evaluate_skill_gaps(candidate, job)`
- Produces: Gap Severity Index ($GSI$), Job Readiness Score ($JRS = 100 - GSI$), Estimated Duration in Months ($T_{\text{bridge}}$), and Categorized Gap Items (CAT-1 Statutory Licences through CAT-4 Local Regulations).

### 4.3 Formula 3: Job vs Job Proximity (JJF)
- Module: `intelligence_engine.03_job_to_job_comparison.compare_multiple_jobs(job_list)`
- Produces: $N \times N$ Job Proximity Matrix ($JPI$), Salary Parity Delta ($\Delta_{\text{sal}} = M_b - M_a$), and Shared vs Unique Requirement Token Sets.

### 4.4 Formula 4: Candidate Benchmarking (CCF)
- Module: `intelligence_engine.04_candidate_benchmarking.compare_two_candidates(cand_a, cand_b)`
- Produces: Relative Merit Scores ($RMS_a, RMS_b$), Head-to-Head Delta ($\Delta = RMS_a - RMS_b$), and Selection Recommendation Verdict.

### 4.5 Formula 5: Job Seeker Feed Ranking (JFR)
- Module: `intelligence_engine.05_job_seeker_ranking_feed.compute_feed_job_score(candidate, job)`
- Produces: Base Feed Ranking Score ($FRS$).

### 4.6 Formula 6: Recruiter Talent Search Ranking (TSR)
- Module: `intelligence_engine.06_recruiter_candidate_ranking.compute_talent_search_score(candidate, job)`
- Produces: Talent Search Score ($TSS$) balancing Requisition Fit (40%), Seniority Parity (25%), Evidence Rigour (15%), Regulatory Compliance (15%), and Contract Audit (5%).

---

## 5. Behavioural Ranking Feedback Loop (REQ-S16)

To fulfill **REQ-S16**, the seeker feed adjusts the baseline Formula 5 score dynamically based on user engagement signals:

$$FRS^\star(J \mid C) = \min\left(100.0, \; FRS(J \mid C) \times \left(1.0 + \Delta_{\text{save}} - \Delta_{\text{ignore}}\right)\right)$$

Where:
1. **Save Affinity Boost ($\Delta_{\text{save}}$):**
   - If the candidate has saved jobs with the **same employer**, add $+10\%$ ($\Delta_{\text{save}} += 0.10$).
   - If the candidate has saved jobs in the **same occupational category**, add $+5\%$ ($\Delta_{\text{save}} += 0.05$).
2. **Ignore Demotion Penalty ($\Delta_{\text{ignore}}$):**
   - If the job is explicitly ignored by the candidate, it is completely removed from the query ($FRS^\star = 0$).
   - If the candidate has ignored $\ge 3$ jobs from the **same employer**, apply a $-25\%$ diversity/brand penalty to remaining jobs from that employer ($\Delta_{\text{ignore}} = 0.25$).
3. **Report Disqualification:**
   - Any job reported by the candidate with the flag "Also hide from my feed" is immediately purged from their feed.
   - If a job receives $\ge 3$ distinct seeker reports, its status transitions to `under_review` and is hidden platform-wide pending HR resolution.

---

## 6. Analytical Chart Mathematical Formulations

### 6.1 Projected ANZSCO Match Progression (Line Chart A, REQ-S09)

Models how the candidate's ANZSCO match percentage improves over calendar months $t \in [0, T_{\text{bridge}}]$ as missing competencies are acquired:

$$SMF(t) = \min\left(95.0, \; SMF_0 + \left(85.0 - SMF_0\right) \times \left(1.0 - e^{-\frac{t}{\tau}}\right) + \Delta_{\text{linear}} \cdot t\right)$$

- $SMF_0$: Initial match score from Formula 1.
- $\tau$: Upskilling time constant ($\tau = \frac{T_{\text{bridge}}}{2.5}$).
- Yields a realistic diminishing-returns learning curve that surpasses the 85.0% Direct Alignment threshold.

### 6.2 Gap Severity Reduction Over Time (Line Chart B, REQ-S10)

Models the remaining Gap Severity Index ($GSI$) declining towards zero:

$$GSI(t) = GSI_0 \times \exp\left(-\frac{2.3 \cdot t}{T_{\text{bridge}}}\right)$$

- At $t = 0$: $GSI(0) = GSI_0$.
- At $t = T_{\text{bridge}}$: $GSI(T_{\text{bridge}}) \le 0.10 \times GSI_0$ (low residual gap).

### 6.3 Job Comparison Radar Chart Axes (REQ-S27)

Normalized values $[0, 100]$ across 6 standardized dimensions:
1. **ANZSCO Fit:** $S_{\text{tree}}$ (Hierarchical occupational distance).
2. **Capability Parity:** $S_{\text{req}}$ (Requirements Jaccard overlap).
3. **Salary Parity:** $S_{\text{comp}}$ (Relative compensation midpoint ratio).
4. **Sector Affinity:** $S_{\text{sec}}$ (100% same sector, 25% divergent).
5. **Location Proximity:** $S_{\text{geo}}$ (Same metro area 100%, same state 75%, interstate 50%).
6. **Overall Score:** $JPI$ composite proximity index.

### 6.4 Candidate Comparison Radar Chart Axes (REQ-H12)

Normalized values $[0, 100]$ across 7 candidate dimensions:
1. **Skill Depth:** Density of verified technical competencies.
2. **Experience Maturity:** Career longevity scaled to 8-year senior benchmark.
3. **Seniority Parity:** $S_{\text{sen}} = \max(25.0, 100.0 - 12.5 |Y_C - Y_{\text{req}}|)$.
4. **Evidence Rigour:** Verified documentation and excerpt quotes.
5. **Transferable Agility:** Cross-sector leadership and agile methodologies.
6. **Regulatory Readiness:** Absence of statutory licensing blockers ($100 - \text{GapPen}$).
7. **Overall Merit:** Relative Merit Score ($RMS$) from Formula 4.

---

## 7. Application Lifecycle State Machine (REQ-S25, S26, H09)

Applications progress through 8 deterministic lifecycle checkpoints:

```
[1. SUBMITTED] ──────────▶ [2. CV_SCANNING] ──────────▶ [3. UNDER_REVIEW]
                                                               │
                                                               ▼
[6. FINAL_ASSESSMENT] ◀── [5. INTERVIEW] ◀──────────── [4. SHORTLISTED]
       │
       ▼
  [7. OFFER] ────────────▶ [8. HIRED]
       │
       ├─────────────────▶ [REJECTED]   (Any stage by Employer)
       └─────────────────▶ [WITHDRAWN]  (Any stage prior to Offer by Seeker)
```

Each stage records:
- Checkpoint title
- Timestamp
- Responsible actor (`Candidate`, `Employer`, or `System`)
- Operational note (e.g. "Interview scheduled: Video link generated", "Offer extended: $125,000 AUD").
