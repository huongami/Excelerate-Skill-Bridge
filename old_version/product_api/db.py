"""
Skill Bridge 2.0 — SQLite Database Initialization & Connection Engine
Path: product_api/db.py
Follows specification in app/spec/04_DATA_AND_SCORING_SPEC.md
"""

import os
import sqlite3
from typing import Generator

DB_DIR = os.path.join(os.path.dirname(__file__), "var")
DB_PATH = os.path.join(DB_DIR, "app.db")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

-- 1. Users and Authentication
CREATE TABLE IF NOT EXISTS users (
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
CREATE TABLE IF NOT EXISTS seeker_profiles (
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
CREATE TABLE IF NOT EXISTS seeker_skills (
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
CREATE TABLE IF NOT EXISTS hr_profiles (
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
CREATE TABLE IF NOT EXISTS jobs (
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
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'interviewing', 'offer_pending', 'filled', 'expired', 'closed', 'under_review')),
    posted_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NULL,
    update_notice TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. User Engagement & Tracking (Feeds HR Metrics REQ-H05)
CREATE TABLE IF NOT EXISTS job_impressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    user_id TEXT,                              -- Optional (tracks unique seeker views)
    session_id TEXT NOT NULL,
    viewed_date DATE NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS job_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    seeker_id TEXT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

-- 7. Seeker Saved Jobs (Favourites REQ-S13, REQ-S23)
CREATE TABLE IF NOT EXISTS saved_jobs (
    seeker_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(seeker_id, job_id),
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 8. Seeker Ignored Jobs (Feed Exclusions REQ-S12, REQ-S18)
CREATE TABLE IF NOT EXISTS ignored_jobs (
    seeker_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    ignored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(seeker_id, job_id),
    FOREIGN KEY(seeker_id) REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 9. Job Discrepancy Reports (REQ-S14)
CREATE TABLE IF NOT EXISTS job_reports (
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
CREATE TABLE IF NOT EXISTS applications (
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

CREATE TABLE IF NOT EXISTS application_timeline_events (
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
CREATE TABLE IF NOT EXISTS compare_tray (
    user_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,                   -- job_id or candidate_id
    tray_type TEXT NOT NULL CHECK(tray_type IN ('jobs', 'candidates')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, entity_id)
);

-- Indexes for lightning fast feed queries and search
CREATE INDEX IF NOT EXISTS idx_jobs_status_posted ON jobs(status, posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_anzsco ON jobs(anzsco_code);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
CREATE INDEX IF NOT EXISTS idx_jobs_employer ON jobs(employer_id);

CREATE INDEX IF NOT EXISTS idx_applications_seeker ON applications(seeker_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id, status);

CREATE INDEX IF NOT EXISTS idx_timeline_app ON application_timeline_events(application_id, event_timestamp ASC);
CREATE INDEX IF NOT EXISTS idx_saved_seeker ON saved_jobs(seeker_id);
CREATE INDEX IF NOT EXISTS idx_ignored_seeker ON ignored_jobs(seeker_id);
CREATE INDEX IF NOT EXISTS idx_impressions_job ON job_impressions(job_id, viewed_date);
CREATE INDEX IF NOT EXISTS idx_clicks_job ON job_clicks(job_id);
"""


def init_db(db_path: str = DB_PATH):
    """Initializes the database directory and tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at: {db_path}")


def get_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Returns a configured SQLite connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


if __name__ == "__main__":
    init_db()
