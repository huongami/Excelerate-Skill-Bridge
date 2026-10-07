# Database

The platform uses **SQLite** (file `var/jinder.db`) in WAL mode with foreign keys on.
The schema is in `jinder/schema.sql`. The server runs it at each start (every statement is safe to run again).
The schema version is **2**. It is the row `schema_version` = `2` in the table `schema_info`. (Version 1 used the row `version`.)
Dates are ISO 8601 text in UTC, for example `2026-10-06T03:45:04.120Z`. Lists inside a profile are JSON text.

## Tables

| Group | Table | Purpose |
|---|---|---|
| Accounts | `users` | One row for each talent (`candidate`) or employer (`recruiter`). Email is unique. Alias is unique and not case-sensitive. `password_hash` is a scrypt hash. The value `!` means "cannot sign in" (sample profiles) |
| | `sessions` | A session. The key is the SHA-256 hash of the token. The token is never stored |
| | `plans` | `basic` or `premium` for a user |
| Talent profile | `profiles` | The private profile: qualifications, roles, domains, skills, goals, level, years, certifications, awards and the CV evidence lines |
| | `translated_skills` | One row for each translated skill, with its reason, evidence level, skill level, years and the talent's decision (`suggested`, `accepted`, `edited`, `removed`). Only `accepted` and `edited` are shared |
| | `cv_files`, `parses` | The stored CV (name, size and private file name) and the result of reading a file (CV or job description) |
| Jobs | `jobs` | Sample jobs (`owner_id` is empty) and jobs that an employer posted |
| | `job_skills` | The skills of a job, in order, with the level that the job asks for and a must-have flag |
| Talent and employer actions | `bookmarks`, `skips`, `reports` | What a talent saves, hides and reports |
| | `saved_candidates`, `skipped_candidates` | What an employer saves and hides |
| Hiring | `applications` | One row for each talent and job (unique). It has the frozen `snapshot` of the shared profile and the `match_json` |
| | `application_history` | Every status change: who (`actor`) and when |
| | `application_slots`, `application_feedback` | Interview times (1 to 3) and the feedback of each side |
| Alerts | `notifications`, `events`, `email_outbox` | In-app alerts, tracking events (counts only) and the email queue with retries |

There are 22 tables (the 21 above and `schema_info`).

## What version 2 added

All the new columns have a safe default. A column with a CHECK rule refuses a bad value (for example a level that is not in the list).

| Table | Column | Type | Meaning |
|---|---|---|---|
| `profiles` | `level` | text: `''` or Intern, Junior, Mid, Senior, Lead, Principal | The current level of the talent |
| `profiles` | `years_exact` | real 0 to 40, or NULL | Exact years of experience. The column `years` (the band) is set from it |
| `profiles` | `certifications` | JSON text | `[{name, issuer, year}]` |
| `profiles` | `awards` | JSON text | `[{name, kind, year}]` |
| `profiles` | `specialisation` | text | A specialisation of the domain (taxonomy), or `''` |
| `profiles` | `work_modes` | JSON text | A list of Onsite, Hybrid, Remote |
| `translated_skills` | `level` | integer 1 to 5, or NULL | The level of one skill. Only rows of `source = 'skill'` have it |
| `translated_skills` | `years` | real 0 to 40, or NULL | The years that the talent used the skill. Only for a skill row |
| `jobs` | `level` | text or NULL | The level that the job asks for (same list as above) |
| `jobs` | `specialisation` | text or NULL | For example Backend, Data engineering |
| `jobs` | `min_years`, `max_years` | real 0 to 40, or NULL | The experience that the job asks for. No maximum means "or more" |
| `jobs` | `work_mode` | text or NULL | Onsite, Hybrid or Remote |
| `jobs` | `education_min` | text or NULL | For example "Bachelor's degree" |
| `jobs` | `certs_required`, `certs_preferred` | JSON text, default `[]` | Lists of certification names |
| `jobs` | `awards_preferred` | JSON text, default `[]` | A list of award kinds |
| `jobs` | `salary_unit` | text: `year`, `day` or `hour` (default `year`) | The unit of `salary_min` and `salary_max`. The numbers are stored **as given**: a day rate stays a day rate. Only the formula engine changes them to a yearly pay (day x 220, hour x 1950) |
| `job_skills` | `level` | integer 1 to 5, or NULL | The level of the skill that the job asks for |
| `job_skills` | `must` | integer, default 1 | 1 = required. 0 = nice to have |

A new index `ix_events_actor` (`actor_id`, `type`) serves the Premium benefits in Settings.

The job description (`jobs.description`) is stored as sent, with its line breaks. It is never cut. The limit is 10,000 characters: a longer text is refused with a message.
The short text `summary` has at most 200 characters.

## The old database (version 1): rule F10

Nothing is deleted. At each start the server does this:

1. It reads the schema version of `var/jinder.db`. A missing, empty or table-less file is a new database.
2. If the version is lower than 2 (version 1, or a file with tables but no version row), the server does NOT change the file.
3. It writes the pending changes of the WAL file into the main file. Then it renames the file to `jinder.db.v1.bak`. If that name exists, it uses `jinder.db.v1.2.bak`, then `jinder.db.v1.3.bak`, and so on.
4. The folder of uploaded CV files (`var/uploads`) goes with it, if it has files. It gets the same suffix (`uploads.v1.bak`). Without this step, the clean-up of unused uploads would delete the old CV files.
5. A new database is made and filled with the sample data. The server writes a warning in the log and a line in the start-up text ("Old data ... Nothing was deleted").
6. If the rename fails (for example, another program has the file open), the start stops with a message. Nothing is lost.
7. A database with version 2 or higher is not moved.

To go back: stop the server, delete the new `jinder.db` (and `-wal`, `-shm`), then rename the backup (and the uploads folder) to the old names.

A database that was made in the middle of the version 2 work gets four columns at the start (`jobs.salary_unit`, `profiles.specialisation`, `profiles.work_modes`, `translated_skills.years`). The schema version stays 2.

## The sample data (seed version 2)

The seed reads the files in `jinder_backend_engine/data/synthetic` (folder `config.SYNTHETIC_DIR`). All the data is synthetic.
The old Australian files in `jinder_backend_engine/data` are **not read** any more (they are not deleted).

| What | Rows | Source |
|---|---|---|
| Sample jobs (`owner_id` empty) | 50. Id `job-<key>` | `synthetic/jobs.json` |
| Sample talent (`is_sample = 1`, no password, alias only) | 50. `updated_at` is spread over the last 60 days | `synthetic/talents.json` |
| Demo employer jobs (with `--demo`) | 4 | `synthetic/demo.json` |

`SEED_VERSION = "2"` in `jinder/seed.py`. A database that was seeded with version 1 (the old data) gets the new data at the next start:
the old sample jobs (and their bookmarks and skips) and the old sample talent are removed and the new ones are made. Real accounts stay.
The demo story is made again with `--demo` (the demo accounts stay; their old jobs, applications and alerts go).

The names of skills, certifications, award kinds, specialisations, cities and levels come from `jinder_backend_engine/data/reference/ict_taxonomy.json`.

## Events

The table `events` holds tracking events. They are counts only. The API never shows who did an event to the other side.

| Event type | When | Used for |
|---|---|---|
| `job_appear`, `job_watch`, `job_save`, `job_skip`, `job_apply`, `job_respond` | A talent sees, opens, saves, hides or applies for a job | Counts of a job (employer charts) |
| `profile_appear`, `profile_watch`, `profile_saved`, `profile_skip` | An employer sees, opens, saves or hides a talent profile | Counts of a profile (talent charts) |
| `talent_list_full` | A Premium employer gets a page of the talent list with more than 5 items | Premium benefit "See every talent profile" |
| `invite` | An invitation was sent (`POST /recruiter/candidates/:id/contact`) | Premium benefit "Invite talent to apply" |
| `compare_view` | A talent comparison was made (`GET /recruiter/compare` worked) | Premium benefit "Compare up to 5 talent profiles" |
| `advanced_charts_view` | `GET /stats` of an employer returned the advanced part | Premium benefit "Pipeline by stage and interest per job" |
| `insights_view` | `GET /stats` of a talent returned the advanced part | Both talent benefits (they change together) |

A user sees only their own counts for the benefits (`used`, `usedCount` in `GET /entitlements`). A user who goes back to Basic keeps these counts.

## Relationships

```
users 1──1 profiles 1──* translated_skills
users 1──* cv_files, parses, sessions, bookmarks, skips, reports, notifications, email_outbox
users (employer) 1──* jobs 1──* job_skills
jobs 1──* applications *──1 users (talent)
applications 1──* application_history, application_slots, application_feedback
```

## Rules in the data

- **Privacy.** A talent profile is read by the employer routes only through `store.shared_profile()` (an allowlist of fields). `profiles.evidence`, `profiles.study_country`, the CV and the user's name and email are never in an employer response.
  The allowlist has the level, the exact years (rounded to 0.5), the skill levels, the certifications, the awards (names, issuer, kind and year) and the time of the last change. It has no name, email, country, CV or evidence line.
- **State machine.** `applications.status` has a CHECK on the allowed values. The server checks the moves (`routes/applications.py`: `TRANSITIONS`). Every change writes a row in `application_history`.
- **One application.** `UNIQUE (job_id, candidate_id)` stops a second application to the same job.
- **One alias.** A unique index on `lower(alias)` (the column uses `COLLATE NOCASE`).
- **Frozen snapshot.** An application keeps a copy of the shared profile as sent. A later change of the profile does not change it. A snapshot of an old application has no level, certifications or awards.
- **Taxonomy.** A value that is not in the taxonomy is cleaned when it is saved, not kept: a domain (`industry`, `targetIndustries`), a specialisation, a work mode, an award kind.
- **Delete.** Deleting a user deletes their profile, sessions, applications and alerts (`ON DELETE CASCADE`). (Account deletion in the app is in the specification backlog.)

## Back up and reset

- Back up: stop the server, then copy `var/jinder.db` (and `var/uploads/`).
- Reset: run `python start.py --reset-db`. The database file is deleted and made again with the sample jobs and the sample talent. The backup files of an old database (`*.v1.bak`) stay.
- The sample job dates move forward at each start, so that the demo jobs stay open (set `JINDER_FREEZE_DATES=1` to stop this).
