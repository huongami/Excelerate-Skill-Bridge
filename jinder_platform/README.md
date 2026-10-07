# Jinder Platform

Jinder translates overseas and cross-industry experience into skills that Australian employers recognise.
This version of the demo covers **three domains only**: Software Engineering, AI & Machine Learning and Data.
This folder is the **running product**: it joins the Skill Bridge frontend, a REST API, a SQLite database and the six Jinder formulas.

```
Hackathon/
├── Skill Bridge/            The frontend (HTML, CSS and JavaScript), the design system and the product specifications
├── jinder_backend_engine/   The six formulas (intelligence_engine/), the taxonomy and the synthetic data (data/)
├── spec/                    Copies of the feature specifications
└── jinder_platform/         THIS FOLDER: the API, the database, the sample data loader and the tests
```

The platform does not copy the other folders. It reads the frontend from `Skill Bridge/app`, the formulas from
`jinder_backend_engine/intelligence_engine`, and the taxonomy and the sample data from `jinder_backend_engine/data`.
It needs only **Python 3.9 or later** (tested on 3.12). It has **no third-party package**.

> **All data in the demo is synthetic.** The 50 jobs, the 50 sample talent profiles and the 4 demo employer jobs were written for the demo
> (`jinder_backend_engine/data/synthetic`). The companies are invented. No job ad is a copy of a real ad. No file has a real person, a real URL, an email address or a phone number.
> The old Australian datasets in `jinder_backend_engine/data` (`australian_candidates.json`, `australian_jobs.json`, `australian_jobs_dataset.csv`, `international_candidates_dataset.csv`, `real_resumes_dataset.csv`)
> are **not used by the platform any more**. They are not deleted. Do not use them.

## Quick start

1. Open a terminal in this folder.
2. Run `python start.py`  (or double-click `start.bat`).
3. Open `http://localhost:8095/` in a browser.

The first start makes the database `var/jinder.db` and fills it with **50 synthetic jobs** and **50 sample talent profiles**.
A sample profile has an alias only. It cannot sign in.
If the folder `var` has an old database (schema version 1), the server keeps it as `jinder.db.v1.bak` and makes a new one. Nothing is deleted (see `docs/DATABASE.md`).

To try the product with ready-made accounts, run `python start.py --demo`.
The command makes an employer account (Bluebushworks, 4 jobs) and a talent account (alias Teal Heron) with a story: applications, an interview, alerts. It shows the random passwords **one time** in the terminal.

| Command | What it does |
|---|---|
| `python start.py` | Start the app and the API on port 8095 |
| `python start.py --demo` | Also make two demo accounts (random passwords) |
| `python start.py --reset-db` | Delete the database and make it again |
| `python start.py --port 9000` | Use a different port |
| `python run_tests.py` | Run all unit and API tests (**729 tests**, about 75 seconds). It must end with `OK` |
| `python run_tests.py --browser` | Also run all the tests in a real browser (needs Chrome or Edge): **7 stages, about 1,055 checks, about 12 minutes**. Each stage starts its own platform in a temporary folder on port 8197 and prints each step. At the end a table shows the result of each stage |
| `python run_tests.py --browser-quick` | Also run only the two journeys (`e2e_demo.py` and `e2e_journey.py`) in a real browser, about 2 minutes |
| `python run_tests.py --formulas` | Also run the self-checks of the six formula files |

## What the product does

| Area | What works |
|---|---|
| Accounts | Sign up and sign in for talent and employers, aliases ("Teal Heron"), password change, session expiry, rate limit on sign-in |
| User block and plan | The user block at the bottom of the left menu opens Settings. A Premium user has a crown and a gold ring. Settings lists the Premium benefits and shows which ones the user has used |
| CV | Upload a PDF or DOCX (up to 10 MB). The server reads it and fills the profile: current role, desired role, level, exact years, certifications, awards, skills with a level. It marks each field "AI-detected" or "Missing" and shows what it found |
| Translation | Overseas titles and skills become skills of the taxonomy, with a reason, an evidence level and a skill level (1 to 5). The talent accepts, edits or removes each one |
| Profile | Level (Intern to Principal), exact years, domain and specialisation, work modes, certifications and awards. Employers see certification and award names and years at once |
| Jobs | Recommendations, search, job detail with facts (level, experience, work mode, certifications, awards), the full job description in a scroll box, a per-skill match with levels, similar jobs, bookmarks, "Not for me", reports. Every list has a page size (10, 20 or 50) and a sort |
| Fit and path to a job | For each job: a **radar chart of 8 numbers** ("How this job fits you"), a decimal **Fit score**, and **Your path to this job**: a radar with two layers ("You have" and "Job requires") over the 7 skill groups (and experience, level and certifications), a list of what fits and a list of gaps with the months to close them |
| Compare | Talent compares 2 to 5 jobs (free). Employers compare 2 to 5 talent profiles (Premium). A "Compare" page, a basket of up to 5, a radar with one line for each item, and a table of skills side by side. No total, no ranking of people |
| Applications | Apply, edit until review, interview times, offers, feedback. The server enforces the state machine |
| Employers | Post a job (also from a PDF or DOCX), a job overview page with the full job description, applications for each job, anonymous talent list with a sort (best fit or recently updated), save, skip, report |
| Premium (demo switch) | Full talent list, invite a talent, compare up to 5 profiles, advanced charts. Talent: skills to learn next and demand for your skills |
| Alerts | In-app notifications, an email outbox with retry, tracking events and charts |

## How the six formulas are used

The six formulas were **rewritten for version 2**. They use levels (Intern to Principal), exact years, skill levels (1 to 5), certifications, awards and work mode.
`jinder/engine_bridge.py` loads them and builds the data that they read. All score math is in the formula files. The platform only builds dictionaries and calls the functions.

| Formula | Where it runs | What the user sees |
|---|---|---|
| F-01 SMF and fit (occupation and skill match) | Every job card, job detail | The **Fit score**, the per-skill match (meets, below, related, missing), and the axes Occupation fit, Skills and Work methods |
| F-02 GSI, JRS and path (gaps) | Job detail | The axis Readiness. **Your path to this job**: the gaps with their kind (missing, below level, experience, level, certification) and the months to close them |
| F-03 JPI (job proximity) | Similar jobs, and the **Compare** page of a talent | Similar jobs are in order of closeness, with a label such as "Adjacent Career Mobility · 77% alike". On the Compare page, a table of how close each pair of jobs is |
| F-04 RMS (merit model) | Compare page of an employer (Premium) | The **areas** (skill depth, experience, level standing, evidence and others) as positions, and some radar axes. **No total** |
| F-05 FRS and its feedback loop | Recommendations and search | Jobs are in order of fit. A saved job raises its employer and domain. Three skipped jobs of one employer lower that employer |
| F-06 TSS (talent search) | Employer talent list, compare page | Profiles are in order of fit. The score is **never sent** to the employer |

The product rules decide what is shown (PRD: "no single score on a person"). Read `docs/FORMULAS_IN_THE_PRODUCT.md` for the details.
The math is in `jinder_backend_engine/docs/02_FORMULAS_MATHEMATICAL_SPEC.md`.

## Privacy and security

- An employer sees a talent by **alias only**. The name and email appear for one application, and only after the talent agrees when they choose an interview time.
- The CV file and the evidence lines are private. Every employer response is built from an allowlist (`store.shared_profile`). A test scans all employer responses for personal data.
- The shared profile (what an employer sees) has: alias, roles with a code, skills with a level, level, exact years (rounded to 0.5), qualifications, fields of study, domains, target roles, locations, work types, certifications, awards and the time of the last change.
  **Certification and award names and years are shared with employers at once.** The app tells the talent not to write a name or contact details there. The server removes email addresses and phone numbers.
- An employer never gets a score on a person. Only a per-skill match, a coverage and an order.
- Formulas read no name, email, country, nationality, visa, age or gender. A test checks the data that goes into them. On the employer side the formulas never read the CV text.
- Passwords use scrypt. Session tokens are random, and only their SHA-256 hash is stored.
- Uploads: type checked by content (not by name), 10 MB limit, random file names, a private folder that is never served.
- The server sends a Content Security Policy and the other security headers. It serves only an allowlist of frontend file types.
- The log has paths and status codes only. It never has a query string, a body, an email or a token.
- Text in a CV is data. Nothing in it is run or followed as an instruction. No CV text leaves the server (there is no call to an AI service).

## Configuration

Set an environment variable, or write it in a `.env` file in this folder (see `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `JINDER_PORT` | `8095` | Port |
| `JINDER_HOST` | `127.0.0.1` | Address. Use `0.0.0.0` only behind HTTPS |
| `JINDER_DB_PATH` | `var/jinder.db` | The SQLite file |
| `JINDER_VAR_DIR` | `var` | The folder of the database and the uploads |
| `JINDER_UPLOAD_DIR` | `var/uploads` | The private folder of uploaded files |
| `JINDER_APP_DIR` | `../Skill Bridge/app` | The frontend folder |
| `JINDER_ENGINE_DIR` | `../jinder_backend_engine/intelligence_engine` | The formula folder |
| `JINDER_DATA_DIR` | `../jinder_backend_engine/data` | The data folder (it has `reference/` and `synthetic/`) |
| `JINDER_TAXONOMY_PATH` | `<data>/reference/ict_taxonomy.json` | The taxonomy file: the one list of names for skills, roles, certifications, domains and levels |
| `JINDER_SYNTHETIC_DIR` | `<data>/synthetic` | The synthetic jobs, talent and demo data |
| `JINDER_CORS_ORIGINS` | empty | Origins that may call the API from another address, for example `http://localhost:5173` |
| `JINDER_ALLOW_PLAN_SWITCH` | on for `127.0.0.1`, off for any other host | The Basic/Premium switch in Settings (a demo toggle). `1` turns it on, `0` turns it off |
| `JINDER_FREEZE_DATES` | empty | Set to `1` to stop the moving of sample job dates |
| `JINDER_SMTP_HOST`, `_PORT`, `_USER`, `_PASSWORD`, `_FROM` | empty | Send real email. Without them, messages are only recorded |
| `JINDER_FAST_TEST_HASH` | empty | **Tests only.** A weak password hash, so that the many test accounts are fast. `run_tests.py` sets it. The server writes a warning if it starts with it. `JINDER_REAL_HASH_IN_TESTS=1` runs the tests with the real hash (about 105 seconds) |

> **Warning:** Use HTTPS in front of the server for any use other than `localhost`.
> The platform serves plain HTTP. Put a reverse proxy with TLS in front of it.

## Use the frontend on its own address

The frontend can also run from `Skill Bridge/app/serve.ps1` (port 5173). Then:

1. Start the platform with `JINDER_CORS_ORIGINS=http://localhost:5173`.
2. In `Skill Bridge/app/js/config.js`, set `API_BASE_URL` to `http://localhost:8095/api`.
3. Start the frontend with `serve.ps1 -ApiOrigin http://localhost:8095`.

Add `?mock=1` to the address (`http://localhost:5173/?mock=1`) to use the browser-only mock API without a backend.
The mock has its own smaller data, and the data is **ICT only** like the real data: 24 jobs (a copy of 24 of the 50 synthetic jobs), 10 sample talent, 5 sample CVs and 4 sample job descriptions, with the same names of the taxonomy.
The mock has no formula engine and does not read a real file (a CV or a job file gives a sample by its name). The pager and the sort are made in the browser.
The features that need the real backend are not in the mock: the Compare page, the plan card with benefits, and "Your path to this job".
The new sections hide when the data is missing, and the Compare page tells the user that it needs the real backend.
The mock keeps its data in the browser under the key `jinder.mock.db.v2`. The old key `jinder.mock.db.v1` (the old data of other fields of work) is removed when the app starts.

## Folder map

```
jinder_platform/
├── start.py, start.bat, run_tests.py
├── jinder/
│   ├── app.py              start-up: database (and the backup of an old one), seed, email worker, server
│   ├── http_server.py      routing, JSON and multipart bodies, security headers, static frontend
│   ├── routes/             account, jobs, applications, recruiter (employer, compare), platform (alerts, plans, benefits, charts)
│   ├── store.py            users, profiles, the shared (employer-safe) profile, alerts, plans, benefits
│   ├── catalogue.py        jobs, ranking, similar jobs, the match, "path to a job"
│   ├── engine_bridge.py    the link to the six formulas
│   ├── taxonomy.py         reads ict_taxonomy.json once (the one list of names)
│   ├── reference.py        the pick-lists (domains, roles, cities, certifications, award kinds ...), built from the taxonomy
│   ├── translation.py      skill translation library
│   ├── skills.py           skill names, related skills, the per-skill match with levels
│   ├── cv_parser.py, cv_lexicon.py, jd_parser.py, textextract.py    read a CV or a job description (PDF, DOCX)
│   ├── seed.py             sample jobs, sample talent, demo accounts (seed version 2)
│   ├── security.py, aliases.py, mailer.py, parsing.py, guards.py, util.py, db.py, schema.sql
├── tests/                  unit and API tests; tests/browser has the browser scripts (e2e_*.py, check_fe_*.py, check_mock_ict.py, qa_*.py), e2e_common.py and cdp.py
├── docs/                   database, formulas in the product, API notes, V2 plan, CHANGELOG_V2.md, changes/
└── var/                    the database, the old-database backups and uploads (not committed)
```

## Tests

| Stage | What it checks | Checks | Time |
|---|---|---|---|
| Unit and API tests (`python run_tests.py`) | Accounts, profile, CV and job file readers, jobs and lists (page and sort), compare, benefits and events, privacy of every employer endpoint (`test_privacy_v2.py`), the pick-lists against the taxonomy (`test_reference_parity.py`), the formulas and the differentiation numbers, the seed, the migration of an old database, security, concurrency, the ICT-only mock files (`test_mock_ict.py`) | 729 tests | about 75 s |
| `e2e_demo.py` | The demo story in the real browser (Teal Heron, Alex Morgan at Bluebushworks): menu, pager and sort, the job description box, "Your path", compare, Settings and Premium, review | 74 | 55 s |
| `e2e_journey.py` | A new talent and a new employer: CV scan, onboarding, a new job, apply, review, interview, offer, delete the account | 45 | 52 s |
| `check_fe_core.py` | Shared components, menu, user block, Settings plan card, compare route, mock mode | 179 | 69 s |
| `check_fe_talent.py` | Talent lists, job card and detail, "Your path to this job", onboarding and the CV summary | 279 | 179 s |
| `check_fe_employer.py` | Employer lists, job form, job overview, talent cards and detail, compare entry points | 205 | 122 s |
| `check_fe_compare.py` | The Compare page for both roles | 192 | 104 s |
| `check_mock_ict.py` | The browser-only mock (`?mock=1`) has ICT data only and its screens work | 81 | 46 s |

The browser stages are run by `python run_tests.py --browser`. You can also run one script alone, for example `python tests/browser/check_fe_talent.py [--shots <folder>]` (ports 8120, 8130, 8140, 8150 and 8170).
Every browser script uses a temporary data folder. It never uses your `var/` folder or the port 8095.

**QA scripts** (not part of `run_tests.py`: they make many accounts and take longer). They are in `tests/browser/`:

| Script | What it does | Time |
|---|---|---|
| `qa_acceptance.py [--only R1,R5]` | The walk-through of the 12 feedback items with screenshots (142 steps) | about 5.5 min |
| `qa_a11y.py` | Keyboard order, accessible names, focus, the Compare picker and 390 px width (44 checks), and a measure of colour contrast | about 1.5 min |
| `qa_perf.py` | The response time of 17 endpoints (20 calls each) | about 40 s |
| `qa_xss.py` | Markup in text fields on 15 screens (18 checks) | about 30 s |

The screenshots of the QA walk-through are in `docs/changes/qa-shots/`. The results are in `docs/changes/QA.md` and `docs/CHANGELOG_V2.md`.

## Known limits

- The CV and job readers are rule-based. They work well on text PDFs and DOCX files. A scanned image (no text) fails with a clear message and the talent can type the details.
  The numbers of the CV reader come from made-up CVs. A real CV can fail where a test CV did not. The reader was also tested on the own CV of the user (a private file; its text is not copied into the project): the current role, the desired role, the level, the years and the domain are right, and its 2 certifications are found.
- Sample jobs have no employer account. An application to a sample job is stored, but no employer moves it. Jobs that an employer posts in Jinder (and the 4 jobs of the demo employer) use the full flow.
- Payments are out of scope. The Premium switch is a demo toggle (see `JINDER_ALLOW_PLAN_SWITCH`).
- Email needs SMTP settings. Password reset and email verification are not built (they are in the specification backlog).
- The sign-in rate limit and the parse queue live in the memory of one server process.
- The taxonomy, the ANZSCO-style codes, the pay benchmarks, the 220 working days of a day rate and the weights of the formulas are **demo values**. People made them by hand. They are not official data and not statistics.
- `jinder_backend_engine/intelligence_engine/formulas_presentation.html` still shows the formulas of version 1 (a note at the top says so).
- The screens were tested in Chrome only. Screen readers (NVDA, VoiceOver) were not tested.
- Colour contrast: 55 kinds of text on 10 screens are below 4.5:1 (the token `--muted` 3.3:1, accent text 4.1 to 4.3:1, white text on the accent colour 3.7:1, `chip-yellow` 3.1:1). This is old design debt in the design tokens, and the decision to change them is open (see `docs/CHANGELOG_V2.md`).
- `start.py` prints the address as `http://localhost:PORT/`. A script on Windows that uses this address can wait 2 seconds for each request (the server listens on 127.0.0.1 only). A browser is not affected. Use `http://127.0.0.1:PORT/` in a script.
- The old server on port 8095 (if it runs) keeps the old code in its memory. Stop it and start it again. At the first start, the old database `var/jinder.db` is **renamed** to `jinder.db.v1.bak` (and `var/uploads` to `uploads.v1.bak`). The old accounts are in the backup, not in the new database: create a new account, or use `--demo`.

See `docs/CHANGELOG_V2.md` for what changed in version 2 and the full list of known limits.
