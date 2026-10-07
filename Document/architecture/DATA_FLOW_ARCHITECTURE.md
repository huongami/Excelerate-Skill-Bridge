# Data Flow Architecture — Jinder Platform

> **Scope:** how data moves through the platform, from the source files to the screen.
> **Applies to:** `jinder_frontend/app`, `jinder_platform`, `jinder_backend_engine`.
> **Related:** [Data modeling](DATA_MODELING_ARCHITECTURE_DETAIL.md) (tables), [Backend](BACKEND_ARCHITECTURE_DETAIL.md), [Formulas](FORMULA_ARCHITECTURE_DETAIL.md), [Gap analysis](../GAP_ANALYSIS.md).

---

## 1. Overview diagram

![Jinder data flow](diagrams/06_data_flow.png)

The bottom of the diagram shows three examples, step by step, with the tables and formulas that each step uses:
- **A talent applies for a job:** upload CV → accept skills → open a job → apply → interview.
- **An employer finds talent:** post a job (also from a PDF) → open the talent list (F-06, Basic = top 5) → open and save a profile (F-01) → invite (Premium) or review an applicant → interview (name and email only with the talent's consent).
- **After the interview (both sides):** confirm the time → accepted or not selected (email) → send an offer (email) → the talent answers the offer → both sides give feedback. See 3.10.

The last strip shows the other flows: email outbox, charts, compare, skip, save and report, and the privacy rights (export and delete).

Source of the diagram: [`diagrams/06_data_flow.html`](diagrams/06_data_flow.html). Open it in a browser, or make the PNG again with headless Chrome (window 1600 × 1626).

---

## 2. The five layers

| Layer | Where | Keeps data? | Job |
|---|---|---|---|
| **Users** | Talent and employer in a browser | — | Send actions, read results |
| **Web client** | `jinder_frontend/app` (one-page app) | Only the session token | Show screens. Every call goes through `js/api/index.js` |
| **API** | `jinder_platform/jinder` (Python, port 8095) | No (stateless per request) | Check the session, the role and the rules. Read and write the store. Call the formulas |
| **Persistence** | `jinder_platform/var/jinder.db` (SQLite, WAL) and `var/uploads/` | **Yes — the only place** | Store facts: who, what, when |
| **Intelligence engine** | `jinder_backend_engine/intelligence_engine` (6 formulas) | No | Compute scores from the facts, on each request |

Two more inputs feed the layers:
- **Reference data** — `jinder_backend_engine/data/reference/ict_taxonomy.json`: the one list of names (skills, roles, certifications, award kinds, levels, cities). The API, the CV reader and the formulas use the same names.
- **Seed data** — `jinder_backend_engine/data/synthetic/` (`jobs.json`, `talents.json`): the job catalogue and the initial talent profiles. The root folder `Data/` has the same files for reference; the server does not read it (`jinder_platform/jinder/config.py`, `DATA_DIR`).

**Main rule:** the database stores facts only. Scores are computed again on every request and are **never stored**.

---

## 3. Core flows

### 3.1 Start-up and seeding
1. `start.py` runs `schema.sql` (safe to run again) and checks the schema version.
2. An older database is renamed to a backup file (`*.v1.bak`). It is never changed in place.
3. The seed loads the taxonomy, the job catalogue and the initial talent profiles into the database. It is idempotent.
4. Two background workers start: the file reader pool (2 threads) and the email outbox worker.

### 3.2 Read request (for example, the job feed)
```
Browser ──GET /api/jobs/recommended──► API: session → role guard
                                          │
                                          ├─ store: read profile, jobs, skips, applications
                                          ├─ engine_bridge: build dictionaries → formulas F-01, F-05
                                          ├─ events: write job_appear (counts only)
                                          ▼
Browser ◄──────── JSON (cards + per-skill match + reasons) ─────────
```
The response has the result of the formulas. The database gets only the event row.

### 3.3 Write request (a command that changes state)
Every state change follows the same pattern, in one database transaction:

| Step | Table | Example (employer invites to interview) |
|---|---|---|
| 1. Check the rule | — | The state machine allows `review → interview` |
| 2. Change the fact | the main table | `applications.status = interview`, `application_slots` |
| 3. Log the change | `application_history` | status, time, actor role, note |
| 4. Tell the other side | `notifications` (+ `email_outbox` for email events) | "Interview times for …" |
| 5. Count it | `events` | `job_respond` |

The system never changes an application status by itself. A person makes every change.

### 3.4 File in, structured data out (CV and job description)
```
upload ─► type + size check ─► var/uploads/ (private file) + parses (status = parsing)
                                   │  background thread (ThreadPoolExecutor, 2 workers)
                                   ▼
                       text extraction ─► rule-based reader (taxonomy names)
                                   ▼
                       parses.result (status = done | failed)
browser polls GET …/parse/:id ─► fills the form (fields marked "AI-detected" / "Missing")
```
- The user checks the result before anything is saved. A CV result becomes `profiles` and `translated_skills` only after the talent saves. A job description result becomes a job only after the employer posts it.
- The file is never sent to an employer endpoint. A failed read falls back to manual entry.
- The reader is rule-based today. An LLM can replace it behind the same module (see the gap analysis, Phase 6).

### 3.5 Scores on read
- `engine_bridge.py` reads the facts and builds the inputs of the six formulas. All the math is in the formula files.
- F-01 fit and per-skill match, F-02 gaps and the path to a job, F-03 similar jobs, F-04 compare (no total), F-05 job feed order, F-06 talent search order.
- The score of a talent is never sent to an employer. Employers get per-skill results and an order only.

### 3.6 Privacy projection (what an employer can see)
```
profiles + translated_skills (private)
        │  store.shared_profile()  ← allowlist, the only way out
        ▼
shared profile: alias, level, years (rounded), accepted skills, certifications, awards
        │  frozen copy when the talent applies
        ▼
applications.snapshot  ──► employer screens
```
- Never in an employer response: name, email, country of study, CV file, CV evidence lines.
- Only `accepted` and `edited` translated skills are shared.
- Name and email are shown only after the talent ticks the consent box when they pick an interview time (`applications.identity_shared = 1`).
- Free text that the other side reads (note, invitation, offer, feedback) is cleaned of emails and phone numbers.

### 3.7 Notifications and email
1. An action writes a row in `notifications` (in-app) in the same transaction.
2. For email events, it also writes a row in `email_outbox` with status `pending`.
3. The outbox worker (a background thread, every 20 s) sends pending emails and retries failures with backoff. A failed email never blocks the action.
4. Without SMTP settings, the email is kept as `recorded`.

### 3.8 Tracking events and charts
- Actions write rows in `events`: `job_appear`, `job_watch`, `job_save`, `job_skip`, `job_apply`, `job_respond`, `profile_appear`, `profile_watch`, `profile_saved`, `profile_skip`, and the premium-use events.
- `GET /api/stats` turns the events into counts for the charts.
- Counts only: the API never shows the other side who did an event. Skip counts are not shown to users; they only change the order of results.

### 3.9 Mock mode (no server)
With `?mock=1` and the static server (`jinder_frontend/app/serve.ps1`), the web client uses `js/api/mock/` instead of the API. The mock keeps its data in the browser `localStorage`. It follows the same API contract (`jinder_frontend/prompt.md`). Use it to run the web client without the backend.


### 3.10 After the interview
Each step uses the write pattern in 3.3: one transaction writes the fact, a row in `application_history` and a notification to the other side.

| # | Who | Call | Fact that changes | Tell the other side |
|---|---|---|---|---|
| 6 | Employer | `POST /api/recruiter/applications/:id/confirm-slot` | `applications.slot_confirmed = 1` (only after the talent picks a time) | notification `slot_confirmed` |
| 7 | Employer | `POST …/status` with `to = accepted` or `to = rejected` | `applications.status`. `accepted` needs a confirmed time | notification + `email_outbox` |
| 8 | Employer | `POST …/status` with `to = offer` | `offer_text` (at least 10 characters, contact details removed), `offer_sent_at` | notification + `email_outbox` |
| 9 | Talent | `POST /api/applications/:id/offer-reply` | `status = confirmed` or `rejected` | notification `offer_reply`, event `job_respond` |
| 10 | Both | `POST /api/applications/:id/feedback`, `POST /api/recruiter/applications/:id/feedback` | `application_feedback`: `to_other` (the other side reads it) and `to_team` (only the own team reads it) | notification `feedback` |

- The employer can set `rejected` ("not selected") at each open step.
- A talent can decline a Premium invitation: `POST /api/applications/:id/decline` changes `contacted` to `declined` and tells the employer (`contact_declined`).
- Feedback is possible only in a final state: `confirmed`, `rejected` or `declined`. At least one box must have text.

### 3.11 Compare, skip, save and report
- **Compare:** a talent compares 2 to 5 jobs (`GET /api/jobs/compare`, F-03). A Premium employer compares 2 to 5 profiles per skill (`GET /api/recruiter/compare`, F-04). There is no total score and no ranking of people. `COMPARE_MAX = 5` is in `config.py`.
- **Skip and save:** a talent writes `bookmarks` and `skips`. An employer writes `saved_candidates` and `skipped_candidates`. Saves and skips change the order of the results (F-05, F-06). Skip counts are not shown to users.
- **Report:** a user can report a job or a profile. The row goes to `reports`.

### 3.12 Your data: export and delete
- `GET /api/me/export` returns the data of the signed-in user only: account, shared profile, applications, notifications, reports, and also the bookmarks and skipped jobs (talent) or the posted jobs (employer).
- Delete account needs the password. One transaction removes the CV and job description files from `var/uploads/`, the jobs of an employer (with their applications, bookmarks and skips), the events and reports about the user, and then the user row. The other rows go by `ON DELETE CASCADE`.

---

## 4. Data classes

| Class | Examples | Who can read it | Where |
|---|---|---|---|
| **Private** | Name, email, password hash, CV file, CV evidence lines, country of study, all translated skills | The owner (and system processes) | `users`, `profiles`, `cv_files`, `parses`, `var/uploads/` |
| **Shared** | Alias, level, rounded years, accepted skills, certifications, awards | Employers, through the allowlist only | `store.shared_profile()`, `applications.snapshot` |
| **Process** | Application status, history, slots, offers, feedback to the other side | The two parties of one application | `applications`, `application_*` |
| **Aggregate** | Event counts, chart data | The owner of the job or profile, as counts | `events` → `/api/stats` |
| **Team only** | Feedback to the Jinder team, reports | The Jinder team | `application_feedback.to_team`, `reports` |
| **Reference** | Taxonomy, job catalogue, initial talent profiles | Everyone (public names) | `jinder_backend_engine/data/` |

---

## 5. Rules that the data flow must keep

1. **One way out for talent data:** employer routes read a profile only through `store.shared_profile()`.
2. **Facts in, scores out:** do not store a score in the database. Compute it from the facts.
3. **Frozen at apply:** an application keeps the snapshot and the match of the time of applying.
4. **One application for each talent and job:** `UNIQUE (job_id, candidate_id)`.
5. **Every status change is logged** in `application_history` and tells the other side.
6. **One list of names:** a value that is not in the taxonomy is cleaned when it is saved.
7. **Nothing is deleted at upgrade:** an old database is kept as a backup file.
8. **No CV text or personal data in the logs.**

---

## 6. Where to change what

| To change … | Edit … |
|---|---|
| A score or a ranking | The formula file in `jinder_backend_engine/intelligence_engine/` (the API does not change) |
| What an employer can see | `store.shared_profile()` and the privacy tests |
| A new skill, role or certification name | `ict_taxonomy.json`, then make `js/data/reference.js` again |
| How a CV or job description is read | `cv_parser.py`, `jd_parser.py` (`jinder_platform/jinder/`) |
| A new table or column | `schema.sql` (statements must be safe to run again) and `docs/DATABASE.md` |
| An API endpoint | `jinder_platform/jinder/routes/` and the API contract in `jinder_frontend/prompt.md` |

---

## 7. Known gaps in the data flow

See [`../GAP_ANALYSIS.md`](../GAP_ANALYSIS.md) for the full list and the plan. The gaps that touch the data flow most:

- **The `/admin/*` routes have no access control.** They can read every table, including private data. Fix this before the app runs on a shared computer or a network (gap analysis, section 1).
- Caching of the recommendations and the parse results is missing; each request runs the formulas again.
- Events are written synchronously inside the request.
- Data is not encrypted at rest, and the server uses plain HTTP.
