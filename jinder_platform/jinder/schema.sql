-- Jinder platform database (SQLite). Every statement is safe to run again.
-- Dates are ISO 8601 text in UTC. Lists inside a profile are JSON text.
-- Schema version 2 (V2_PLAN.md, section 4.5). The version is the row 'schema_version' in schema_info.
-- A database with an older version is renamed to a backup file at start-up (see db.py). It is never changed in place.

CREATE TABLE IF NOT EXISTS schema_info (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- ---------- Accounts ----------
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  role          TEXT NOT NULL CHECK (role IN ('candidate', 'recruiter')),
  name          TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,                 -- lower case
  company       TEXT,                                 -- employers only
  alias         TEXT COLLATE NOCASE,                  -- talent only. Unique, case-insensitive
  password_hash TEXT NOT NULL,                        -- scrypt hash. "!" = this account cannot sign in
  onboarding    TEXT CHECK (onboarding IN ('done', 'dismissed')),
  is_sample     INTEGER NOT NULL DEFAULT 0,           -- 1 = sample talent profile (cannot sign in)
  created_at    TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_alias ON users (alias) WHERE alias IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,                        -- SHA-256 of the token. The token itself is never stored
  user_id    TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions (user_id);

CREATE TABLE IF NOT EXISTS plans (
  user_id TEXT PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  plan    TEXT NOT NULL CHECK (plan IN ('basic', 'premium'))
);

-- ---------- Talent profile (private) ----------
CREATE TABLE IF NOT EXISTS profiles (
  user_id           TEXT PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  qualification     TEXT NOT NULL DEFAULT '[]',
  field_of_study    TEXT NOT NULL DEFAULT '[]',
  study_country     TEXT NOT NULL DEFAULT '[]',       -- used only for the AQF note. Never shared, never used to rank
  current_role      TEXT NOT NULL DEFAULT '[]',
  industry          TEXT NOT NULL DEFAULT '[]',
  years             TEXT NOT NULL DEFAULT '',         -- the band. It is set from years_exact when that is set
  skills            TEXT NOT NULL DEFAULT '[]',
  target_role       TEXT NOT NULL DEFAULT '[]',
  target_industries TEXT NOT NULL DEFAULT '[]',
  locations         TEXT NOT NULL DEFAULT '[]',
  work_types        TEXT NOT NULL DEFAULT '[]',
  evidence          TEXT NOT NULL DEFAULT '[]',       -- CV evidence lines. PRIVATE: never in an employer response
  updated_at        TEXT NOT NULL,
  -- version 2
  level             TEXT NOT NULL DEFAULT '' CHECK (level IN ('', 'Intern', 'Junior', 'Mid', 'Senior', 'Lead', 'Principal')),
  years_exact       REAL CHECK (years_exact IS NULL OR (years_exact >= 0 AND years_exact <= 40)),   -- exact years of experience
  certifications    TEXT NOT NULL DEFAULT '[]',       -- JSON [{name, issuer, year}]
  awards            TEXT NOT NULL DEFAULT '[]',       -- JSON [{name, kind, year}]
  specialisation    TEXT NOT NULL DEFAULT '',         -- a specialisation of the domain (taxonomy), or ''
  work_modes        TEXT NOT NULL DEFAULT '[]'        -- JSON list: Onsite, Hybrid, Remote
);

-- The translated skills and the talent's decision for each one. Only accepted and edited skills are shared.
CREATE TABLE IF NOT EXISTS translated_skills (
  user_id       TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  skill_id      TEXT NOT NULL,
  position      INTEGER NOT NULL,
  source        TEXT NOT NULL CHECK (source IN ('role', 'skill', 'qualification')),
  original      TEXT NOT NULL,
  mapped        TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('cross-border', 'cross-industry', 'direct')),
  anzsco        TEXT NOT NULL DEFAULT '',
  occupation    TEXT NOT NULL DEFAULT '',
  reason        TEXT NOT NULL DEFAULT '',
  evidence      TEXT NOT NULL CHECK (evidence IN ('Strong', 'Moderate', 'Limited')),
  evidence_text TEXT NOT NULL DEFAULT '',
  status        TEXT NOT NULL CHECK (status IN ('suggested', 'accepted', 'edited', 'removed')),
  level         INTEGER CHECK (level IS NULL OR level BETWEEN 1 AND 5),   -- version 2: the skill level (skills only). NULL = not set
  years         REAL CHECK (years IS NULL OR (years >= 0 AND years <= 40)),   -- version 2: the years that the talent used the skill (skills only). NULL = not known
  PRIMARY KEY (user_id, skill_id)
);
CREATE INDEX IF NOT EXISTS ix_translated_shared ON translated_skills (user_id) WHERE status IN ('accepted', 'edited');

-- ---------- Files and file reading ----------
CREATE TABLE IF NOT EXISTS cv_files (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  size        INTEGER NOT NULL,
  stored_name TEXT NOT NULL,                          -- the name inside the private upload folder
  added_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_cv_user ON cv_files (user_id, added_at);

-- One row for each file that the server reads in the background (a CV, or a job description)
CREATE TABLE IF NOT EXISTS parses (
  id          TEXT PRIMARY KEY,
  kind        TEXT NOT NULL CHECK (kind IN ('cv', 'jd')),
  user_id     TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  file_name   TEXT NOT NULL,
  stored_name TEXT NOT NULL,
  status      TEXT NOT NULL CHECK (status IN ('parsing', 'done', 'failed')),
  result      TEXT,
  error       TEXT,
  created_at  TEXT NOT NULL,
  finished_at TEXT
);

-- ---------- Jobs ----------
CREATE TABLE IF NOT EXISTS jobs (
  id                TEXT PRIMARY KEY,
  owner_id          TEXT REFERENCES users (id) ON DELETE SET NULL,   -- NULL = catalogue job
  title             TEXT NOT NULL,
  company           TEXT NOT NULL,
  category          TEXT NOT NULL,
  location          TEXT NOT NULL,                    -- a city or "Remote"
  area              TEXT NOT NULL,                    -- the full location text
  type              TEXT NOT NULL,
  anzsco            TEXT NOT NULL DEFAULT '',
  occupation        TEXT NOT NULL DEFAULT '',
  salary            TEXT NOT NULL DEFAULT 'Market competitive',
  salary_min        REAL,
  salary_max        REAL,
  salary_unit       TEXT NOT NULL DEFAULT 'year' CHECK (salary_unit IN ('year', 'day', 'hour')),   -- the unit of salary_min and salary_max, as given. The formulas change it to a yearly pay
  summary           TEXT NOT NULL DEFAULT '',
  description       TEXT NOT NULL DEFAULT '',
  target_applicants INTEGER,
  posted_at         TEXT NOT NULL,
  closes_at         TEXT NOT NULL,
  edited_at         TEXT,
  created_at        TEXT NOT NULL,
  -- version 2. NULL (or an empty list) means "not set". The API sends null for it, never an invented value.
  level             TEXT CHECK (level IS NULL OR level IN ('Intern', 'Junior', 'Mid', 'Senior', 'Lead', 'Principal')),
  specialisation    TEXT,
  min_years         REAL CHECK (min_years IS NULL OR (min_years >= 0 AND min_years <= 40)),
  max_years         REAL CHECK (max_years IS NULL OR (max_years >= 0 AND max_years <= 40)),
  work_mode         TEXT CHECK (work_mode IS NULL OR work_mode IN ('Onsite', 'Hybrid', 'Remote')),
  education_min     TEXT,
  certs_required    TEXT NOT NULL DEFAULT '[]',       -- JSON [name]
  certs_preferred   TEXT NOT NULL DEFAULT '[]',       -- JSON [name]
  awards_preferred  TEXT NOT NULL DEFAULT '[]'        -- JSON [award kind]
);
CREATE INDEX IF NOT EXISTS ix_jobs_owner ON jobs (owner_id);
CREATE INDEX IF NOT EXISTS ix_jobs_closes ON jobs (closes_at);
CREATE INDEX IF NOT EXISTS ix_jobs_anzsco ON jobs (anzsco);

CREATE TABLE IF NOT EXISTS job_skills (
  job_id   TEXT NOT NULL REFERENCES jobs (id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  skill    TEXT NOT NULL,
  level    INTEGER CHECK (level IS NULL OR level BETWEEN 1 AND 5),   -- version 2: the level that the job asks for. NULL = not set
  must     INTEGER NOT NULL DEFAULT 1,                               -- version 2: 1 = required, 0 = nice to have
  PRIMARY KEY (job_id, position)
);
CREATE INDEX IF NOT EXISTS ix_job_skills_skill ON job_skills (skill);

-- ---------- What a talent or an employer does with jobs and profiles ----------
CREATE TABLE IF NOT EXISTS bookmarks (
  user_id    TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  job_id     TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (user_id, job_id)
);

CREATE TABLE IF NOT EXISTS skips (
  user_id    TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  job_id     TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (user_id, job_id)
);

CREATE TABLE IF NOT EXISTS saved_candidates (
  recruiter_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  candidate_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  created_at   TEXT NOT NULL,
  PRIMARY KEY (recruiter_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS skipped_candidates (
  recruiter_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  candidate_id TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  created_at   TEXT NOT NULL,
  PRIMARY KEY (recruiter_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS reports (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  target_type TEXT NOT NULL CHECK (target_type IN ('job', 'candidate')),
  target_id   TEXT NOT NULL,
  reason      TEXT NOT NULL,
  details     TEXT NOT NULL DEFAULT '',
  at          TEXT NOT NULL,
  UNIQUE (user_id, target_type, target_id)
);

-- ---------- Applications and the hiring flow ----------
CREATE TABLE IF NOT EXISTS applications (
  id              TEXT PRIMARY KEY,
  job_id          TEXT NOT NULL,
  candidate_id    TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  recruiter_id    TEXT REFERENCES users (id) ON DELETE SET NULL,
  origin          TEXT NOT NULL CHECK (origin IN ('applied', 'contacted')),
  status          TEXT NOT NULL CHECK (status IN ('applied', 'contacted', 'review', 'interview', 'accepted', 'offer',
                                                  'confirmed', 'rejected', 'declined')),
  note            TEXT NOT NULL DEFAULT '',
  message         TEXT NOT NULL DEFAULT '',           -- the employer's message of an invitation
  snapshot        TEXT NOT NULL,                      -- JSON. A frozen copy of the shared profile. Never the CV
  match_json      TEXT NOT NULL,                      -- JSON. { coverage, skills[] } against the snapshot
  chosen_slot_id  TEXT,
  slot_confirmed  INTEGER NOT NULL DEFAULT 0,
  identity_shared INTEGER NOT NULL DEFAULT 0,         -- 1 = the talent agreed to share name and email
  offer_text      TEXT,
  offer_sent_at   TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  UNIQUE (job_id, candidate_id)
);
CREATE INDEX IF NOT EXISTS ix_app_candidate ON applications (candidate_id, updated_at);
CREATE INDEX IF NOT EXISTS ix_app_recruiter ON applications (recruiter_id, updated_at);
CREATE INDEX IF NOT EXISTS ix_app_job ON applications (job_id);

-- Every status change is logged with who made it and when
CREATE TABLE IF NOT EXISTS application_history (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id TEXT NOT NULL REFERENCES applications (id) ON DELETE CASCADE,
  status         TEXT NOT NULL,
  at             TEXT NOT NULL,
  actor          TEXT NOT NULL CHECK (actor IN ('candidate', 'recruiter', 'system')),
  note           TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_history_app ON application_history (application_id, id);

CREATE TABLE IF NOT EXISTS application_slots (
  id             TEXT NOT NULL,
  application_id TEXT NOT NULL REFERENCES applications (id) ON DELETE CASCADE,
  start          TEXT NOT NULL,
  position       INTEGER NOT NULL,
  PRIMARY KEY (application_id, id)
);

CREATE TABLE IF NOT EXISTS application_feedback (
  application_id TEXT NOT NULL REFERENCES applications (id) ON DELETE CASCADE,
  side           TEXT NOT NULL CHECK (side IN ('candidate', 'recruiter')),
  to_other       TEXT NOT NULL DEFAULT '',
  to_team        TEXT NOT NULL DEFAULT '',
  at             TEXT NOT NULL,
  PRIMARY KEY (application_id, side)
);

-- ---------- Alerts, events and email ----------
CREATE TABLE IF NOT EXISTS notifications (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  type       TEXT NOT NULL,
  title      TEXT NOT NULL,
  body       TEXT NOT NULL DEFAULT '',
  link       TEXT NOT NULL DEFAULT '',
  email      INTEGER NOT NULL DEFAULT 0,
  read       INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_notif_user ON notifications (user_id, created_at);

-- Tracking events (Feature 7). Counts only: the API never shows who did an event to an employer.
CREATE TABLE IF NOT EXISTS events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  type        TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id   TEXT NOT NULL,
  actor_id    TEXT,
  at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_target ON events (target_type, target_id, type);
-- Version 2: the Premium benefits in Settings count the events of the signed-in user ("used" and "usedCount")
CREATE INDEX IF NOT EXISTS ix_events_actor ON events (actor_id, type);

-- The outbox: an email that fails is tried again later. A failed email never blocks the action.
CREATE TABLE IF NOT EXISTS email_outbox (
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  notification_id TEXT,
  subject         TEXT NOT NULL,
  body            TEXT NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'recorded')),
  attempts        INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_outbox_status ON email_outbox (status, next_attempt_at);
