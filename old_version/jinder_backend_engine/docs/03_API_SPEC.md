# 05 — REST API Specification

Source: [`app/spec/02_PRODUCT_SPEC.md`](02_PRODUCT_SPEC.md) & [`app/spec/04_DATA_AND_SCORING_SPEC.md`](04_DATA_AND_SCORING_SPEC.md)
Document standard: Exact HTTP verbs, request/response JSON schemas, authentication requirements, and error codes.

Base URL: `http://localhost:8095/api` (proxied in Next.js via `/api/*` rewrites).
Standard Content-Type: `application/json; charset=utf-8`.
Authentication: Cookie-based session (`sb_session`).

---

## 1. Public & Authentication Endpoints

### 1.1 Live Platform Statistics
- `GET /public/stats`
- **Auth:** Public
- **Response (200 OK):**
```json
{
  "total_live_jobs": 461,
  "total_employers": 287,
  "total_candidates": 320,
  "anzsco_occupations_covered": 17,
  "top_sectors": [
    { "sector": "Healthcare & Nursing", "job_count": 66 },
    { "sector": "Technology & Data", "job_count": 55 }
  ]
}
```

### 1.2 Sign In
- `POST /auth/signin`
- **Request:**
```json
{
  "email": "sarah.jenkins@novon.com.au",
  "password": "Password123!"
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "user": {
    "id": "usr_991823",
    "email": "sarah.jenkins@novon.com.au",
    "role": "hr",
    "display_name": "Novon Recruitment"
  }
}
```
- **Error (401 Unauthorized):** `{"error": "Email or password is incorrect."}`
- **Error (429 Too Many Requests):** `{"error": "Too many failed attempts. Try again in 10 minutes."}`

### 1.3 Seeker Registration
- `POST /auth/signup/seeker`
- **Request:**
```json
{
  "email": "minh.nguyen@example.com",
  "password": "Password123!",
  "alias": "Pacific Triage Pro",
  "legal_name": "Minh Tuan Nguyen",
  "phone": "+61 400 123 456",
  "origin_country": "Vietnam",
  "current_title": "Registered Nurse",
  "years_experience": 10.0,
  "highest_education": "Bachelor of Nursing",
  "target_anzsco_code": "254411",
  "target_anzsco_title": "Registered Nurse",
  "preferred_location": "Sydney",
  "skills": [
    {
      "name": "Clinical Triage",
      "type": "Direct",
      "evidence": "Led acute triage unit in provincial general hospital.",
      "source": "AI_EXTRACTED"
    }
  ],
  "terms_version": "v2026.1"
}
```
- **Response (201 Created):** Sets `sb_session` cookie; returns user profile.

### 1.4 HR Registration
- `POST /auth/signup/hr`
- **Request:**
```json
{
  "email": "recruiter@healthcare-australia.com.au",
  "password": "Password123!",
  "company_name": "Healthcare Australia",
  "recruiter_name": "Sarah Jenkins",
  "recruiter_title": "Senior Talent Acquisition Specialist",
  "terms_version": "v2026.1"
}
```
- **Response (201 Created):** Sets `sb_session` cookie.

### 1.5 Alias Uniqueness Check (REQ-A07)
- `GET /aliases/check?alias={name}`
- **Response (200 OK):** `{"alias": "Pacific Triage Pro", "is_available": true}`

### 1.6 Protocol-Only Google OAuth2 Flow (REQ-A05)
- `GET /mock-google/authorize` (HTML view presenting demo identity chooser)
- `POST /auth/google/exchange`
  - **Request:** `{"code": "auth_code_xyz", "code_verifier": "...", "redirect_uri": "...", "nonce": "..."}`
  - **Response (200 OK):** Validates PKCE and returns existing session OR registration token for `/signup/google-complete`.

---

## 2. CV & JD Scanning Engines

### 2.1 CV Parse & Extraction (REQ-A01, REQ-A02)
- `POST /cv/scan`
- **Headers:** `Content-Type: multipart/form-data`
- **Body:** `file: [PDF / DOCX / TXT file]`
- **Response (200 OK):**
```json
{
  "status": "success",
  "file_name": "Minh_Nguyen_CV.pdf",
  "extracted_data": {
    "legal_name": "Minh Tuan Nguyen",
    "email": "minh.nguyen@example.com",
    "phone": "+61 400 000 000",
    "origin_country": "Vietnam",
    "current_title": "Registered Nurse",
    "years_experience": 10.0,
    "highest_education": "Bachelor of Nursing",
    "suggested_alias": "Pacific Triage Pro",
    "target_anzsco": {
      "code": "254411",
      "title": "Registered Nurse",
      "confidence": 0.94
    },
    "direct_skills": [
      {
        "name": "Clinical Triage",
        "type": "Direct",
        "evidence": "Managed acute patient intake and triage protocol compliance."
      }
    ],
    "transferable_skills": [
      {
        "name": "Cross-Functional SOP Coordination",
        "type": "Transferable",
        "evidence": "Coordinated medical and allied health teams under emergency procedures."
      }
    ],
    "known_gaps": [
      "Requires AHPRA (Australian Health Practitioner Regulation Agency) registration."
    ]
  }
}
```

### 2.2 JD Parse & Requirement Extraction (REQ-H01)
- `POST /jd/scan`
- **Body:** `{"raw_text": "..."}` OR multipart file upload
- **Response (200 OK):** Extracted title, company, requirements array, sector category, and mapped ANZSCO code.

---

## 3. Job Seeker Endpoints

### 3.1 Personalized Ranked Job Feed (REQ-S01, S02, S03, S04, S05, S06, S07, S15, S16)
- `GET /seeker/feed?q={query}&category={cat}&city={city}&within={days}&page={n}&limit={m}`
- **Auth:** Seeker session
- **Response (200 OK):**
```json
{
  "total_matching": 461,
  "page": 1,
  "limit": 20,
  "jobs": [
    {
      "id": "adzuna_5901612689",
      "title": "Registered Nurse",
      "company": "East Bridge Recruitment",
      "location": "Sydney, NSW",
      "city": "Sydney",
      "salary_display": "$100,000 - $110,000 AUD",
      "short_description": "Regional & Remote Aged Care opportunities across Australia. Competitive rates and flexible work arrangements available immediately.",
      "overall_score": 95.7,
      "anzsco_match_percent": 89.9,
      "anzsco_code": "254411",
      "anzsco_title": "Registered Nurse",
      "skill_gap_level": "Low Gap",
      "skill_gap_index": 13.5,
      "bridge_duration_months": 2.0,
      "posted_relative": "Posted 3 days ago",
      "posted_at": "2026-10-02T10:00:00Z",
      "is_saved": false,
      "is_applied": false
    }
  ]
}
```

### 3.2 Job Detail & Mathematical Projections (REQ-S08, S09, S10, S11)
- `GET /seeker/jobs/{id}`
- **Response (200 OK):**
```json
{
  "job": {
    "id": "adzuna_5901612689",
    "title": "Registered Nurse",
    "company": "East Bridge Recruitment",
    "location": "Sydney, NSW",
    "category": "Healthcare & Nursing",
    "employment_type": "Full-time",
    "salary_display": "$100,000 - $110,000 AUD",
    "full_description": "...",
    "requirements": ["AHPRA registration", "Clinical triage", "Medication administration"]
  },
  "scores": {
    "overall_score": 95.7,
    "anzsco_match_percent": 89.9,
    "job_readiness_score": 86.5,
    "gap_severity_index": 13.5,
    "bridge_duration_months": 2.0
  },
  "charts": {
    "anzsco_progression": [
      { "month": 0, "match_percent": 89.9, "milestone": "Current Base" },
      { "month": 1, "match_percent": 92.4, "milestone": "Orientation" },
      { "month": 2, "match_percent": 95.0, "milestone": "Full Alignment" }
    ],
    "gap_reduction": [
      { "month": 0, "gap_severity": 13.5 },
      { "month": 1, "gap_severity": 4.3 },
      { "month": 2, "gap_severity": 1.2 }
    ]
  },
  "explanation": {
    "score_drivers": [
      { "factor": "Capability Alignment", "points": 40.5, "max": 45.0, "rationale": "High direct overlap with ABS core competencies." },
      { "factor": "Wage Upside", "points": 18.2, "max": 20.0, "rationale": "Salary meets Australian industry benchmark." },
      { "factor": "Location Commute", "points": 20.0, "max": 20.0, "rationale": "Located in preferred metropolitan region (Sydney)." },
      { "factor": "Posting Freshness", "points": 14.2, "max": 15.0, "rationale": "Published within the last 72 hours." }
    ],
    "matched_skills": ["Clinical triage", "Patient assessment", "Care planning"],
    "missing_skills": ["Vital signs monitoring"],
    "actionable_steps": [
      "Obtain verification for PBS/Medicare billing module (+4.9 pts, 1.5 months)."
    ]
  }
}
```

### 3.3 Save & Ignore Actions (REQ-S12, S13, S16, S18)
- `PUT /seeker/saved/{jobId}` → Save to favourites.
- `DELETE /seeker/saved/{jobId}` → Remove from favourites.
- `PUT /seeker/ignored/{jobId}` → Ignore and demote similar jobs.
- `DELETE /seeker/ignored/{jobId}` → Restore ignored job to feed.
- `POST /jobs/{id}/reports` → Submit discrepancy report (REQ-S14).

### 3.4 Job Application Pipeline (REQ-S17, S24, S25, S26)
- `POST /applications`
  - **Request:** `{"job_id": "...", "message": "...", "share_gaps": true}`
  - **Response (201 Created):** Creates application record, snapshots scores, initializes timeline.
- `GET /seeker/applications`
  - **Response (200 OK):** List of applications with current status, timeline checkpoints, and employer updates.
- `POST /seeker/applications/{id}/withdraw`
- `POST /seeker/applications/{id}/accept-offer`
- `POST /seeker/applications/{id}/decline-offer`

### 3.5 Job vs Job Comparison (REQ-S27)
- `GET /seeker/compare`
- **Response (200 OK):**
```json
{
  "selected_jobs_count": 2,
  "radar_axes": [
    "ANZSCO Fit", "Capability Parity", "Salary Parity", 
    "Sector Affinity", "Location Proximity", "Overall Score"
  ],
  "radar_datasets": [
    {
      "job_id": "job_01",
      "job_title": "Registered Nurse",
      "company": "East Bridge",
      "values": [90, 85, 92, 100, 100, 95]
    },
    {
      "job_id": "job_02",
      "job_title": "Clinical Coordinator",
      "company": "Healthcare Australia",
      "values": [80, 70, 85, 100, 75, 78]
    }
  ],
  "proximity_matrix": {
    "pairwise_jpi": 61.0,
    "salary_delta_aud": -98350,
    "advice": "Adjacent career mobility path with shared clinical coordination methodologies."
  }
}
```

---

## 4. Recruiter / HR Endpoints

### 4.1 HR KPI Dashboard (REQ-H03)
- `GET /hr/dashboard`
- **Response (200 OK):**
```json
{
  "total_jobs": 12,
  "active_jobs": 8,
  "expired_jobs": 3,
  "hired_candidates": 2,
  "rejected_candidates": 5,
  "total_applications_received": 34,
  "recent_activity": []
}
```

### 4.2 Job Management & Metrics (REQ-H04, REQ-H05)
- `GET /hr/jobs`
- **Response (200 OK):**
```json
{
  "jobs": [
    {
      "id": "job_101",
      "title": "Senior Data Engineer",
      "company": "Novon",
      "status": "active",
      "posted_relative": "Posted 5 days ago",
      "expires_in_days": 25,
      "metrics": {
        "appearances": 1420,
        "views": 215,
        "applicants": 18
      }
    }
  ]
}
```

### 4.3 Applicant Shortlist & Details (REQ-H09, H10, H11)
- `GET /hr/candidates?job_id={jobId}&status={status}`
- **Response (200 OK):**
```json
{
  "candidates": [
    {
      "application_id": "app_9912",
      "alias": "Highland Data Engineer",
      "title": "Senior ETL Architect",
      "years_experience": 8.0,
      "anzsco_match_percent": 94.0,
      "skill_gap_level": "Low Gap",
      "skill_gap_index": 12.0,
      "overall_tss_score": 98.0,
      "status": "under_review",
      "applied_at": "2026-10-03T14:20:00Z"
    }
  ]
}
```

### 4.4 Applicant Lifecycle Transitions (REQ-H09)
- `POST /hr/applications/{id}/transition`
- **Request:**
```json
{
  "action": "schedule_interview",
  "note": "Technical interview scheduled via Zoom.",
  "interview_date": "2026-10-10T10:00:00Z",
  "interview_mode": "Video",
  "interview_link": "https://meet.novon.com.au/tech-interview-881"
}
```

### 4.5 Candidate Comparison Radar (REQ-H12)
- `GET /hr/compare?application_ids={id1},{id2}`
- **Response (200 OK):** Overlaid radar data across 7 dimensions (Skill Depth, Experience, Seniority, Evidence, Transferable, Regulatory, Overall Merit) + Formula 4 Head-to-Head delta ($\Delta$).
