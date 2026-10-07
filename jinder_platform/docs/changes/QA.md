# QA: result of wave 5 (Jinder V2)

Owner: QA agent. Date of the run: 2026-10-07. The plan is `docs/V2_PLAN.md`. This file uses simple English.
All runs used a temporary data folder and the ports 8160 (manual runs), 8161 (the unzipped release) and 8197 (`run_tests.py --browser`).
The port 8095 and the folder `var/` of the user were not used by any QA run: every script sets `JINDER_VAR_DIR` to a temporary folder. The file `var/jinder.db` is the same before and after (SHA-256 `ba8dd1a0...5905d`). The time of the folder `var/` changed during the session; the likely cause is the user's own server on port 8095 (SQLite creates and removes the files `-wal` and `-shm`).
Screenshots of the walk-through are in `docs/changes/qa-shots/` (51 files, 8.6 MB). They are not in the release zip.

## 1. Summary

| What | Result |
|---|---|
| Unit and API tests (`python run_tests.py`) | **720 tests, OK** (72 s). 666 before QA. QA and the MOCK-ICT agent added 54 |
| Formula self-checks (`--formulas`) | 32 checks, all pass |
| Browser, `python run_tests.py --browser` | **7 stages, all pass, 1,055 checks, 628 s**: `e2e_demo` 74, `e2e_journey` 45, `check_fe_core` 179, `check_fe_talent` 279, `check_fe_employer` 205, `check_fe_compare` 192, `check_mock_ict` 81. The whole command with `--formulas` ran 14 min while other QA runs used the computer; it is about 12 min alone |
| Acceptance walk-through R1 to R12 (`tests/browser/qa_acceptance.py`) | 142 steps, all pass (329 s). Run twice with the same result |
| Keyboard, names, focus, 390 px (`tests/browser/qa_a11y.py`) | 44 checks, all pass. One finding on colour contrast (section 8) |
| Response times (`tests/browser/qa_perf.py`) | 17 endpoints x 20 calls: the slowest call is 363 ms. All under 1 second |
| Markup in text fields (`tests/browser/qa_xss.py`) | 18 checks on 15 screens, all pass |
| Release zip | 2.9 MB, 375 entries, all required files, no `var`, no `.bak`, no `__pycache__`. The unzipped copy starts, `/api/health` is ok, `e2e_demo` passes against it (73 of 73), and `python run_tests.py` in it: 720 tests OK |
| Defects | 12 fixed by QA (4 of them are test problems), 6 open (section 12) |

## 2. How to run

| Command | What it does | Time |
|---|---|---|
| `python run_tests.py` | Unit and API tests | about 1.5 min |
| `python run_tests.py --formulas` | And the self-checks of the six formula files | +10 s |
| `python run_tests.py --browser` | And all browser tests: `e2e_demo.py`, `e2e_journey.py`, `check_fe_core.py`, `check_fe_talent.py`, `check_fe_employer.py`, `check_fe_compare.py`, `check_mock_ict.py`. Each stage prints each step. At the end a table shows each stage | about 12 min |
| `python run_tests.py --browser-quick` | And only `e2e_demo.py` and `e2e_journey.py` | about 2 min |
| `python tests/browser/qa_acceptance.py [--only R1,R5]` | The walk-through of R1 to R11 with screenshots | 5.5 min |
| `python tests/browser/qa_a11y.py`, `qa_perf.py`, `qa_xss.py` | Keyboard and 390 px, response times, markup in text | 1.5 min, 40 s, 30 s |

**Decision on the check scripts.** The seven browser stages need about 10 minutes together. The whole `--browser` run is under the limit of 15 minutes. Thus `--browser` runs all of them, and the flag `--browser-full` is not needed.
The flag `--browser-quick` is new (a fast answer). The QA scripts (`qa_*.py`) are not part of `run_tests.py`: they make many accounts and take longer.

## 3. Acceptance R1 to R12 (V2_PLAN section 3)

All lines come from `qa_acceptance.py` (142 steps) and from the other runs of this file. The screenshots are in `docs/changes/qa-shots/`.

| R | Result | Evidence |
|---|---|---|
| **R1** CV scan reads current role, desired role, level, years, certifications, awards | **Pass** | 6 CVs through the real onboarding (4 PDF: cv02, cv07, cv13, cv18; 2 DOCX: cv09, cv11). Every field on "What we found in your CV" equals `tests/fixtures/cv/expected.json`. A missing field has the check mark off and the hint "Not found. You can add it in the next steps." Screens `r1-1-cv02-found.png` to `r1-6-cv18-found.png`; the credentials step (`r1-5-cv13-credentials.png`: 1 certification row, 3 award rows) and the goals step (`r1-5-cv13-goals.png`, `r1-6-cv18-goals.png`: the hint "We could not find your desired role in your CV. You can add it." and an empty field). The level, the exact years and the current role are in editable fields. Parser numbers (unit tests, 23 fixtures): current role found 22/23, level 22/23, years 22/23, desired role 10 of the 10 CVs that state one; every value that was found is right (23/23). 124 CVs of other writers (first run): current role 85%, level 87%, desired role 94%, years 79%, certifications 57%, awards 58%, no invented value. **The own CV of the user (open item O1) was found and tested: see defect D-1** |
| **R2** level, experience, certifications, awards | **Pass** (one note) | API: all 53 open jobs have a level, a minimum of years, a work mode and an education. 45 list a certification, 19 list an award kind. **4 jobs list neither**, and 34 list no award kind (the page says "This job does not ask for ..."): see note N-1. Talent: every job card has the 3 chips (`r2-1-talent-job-cards.png`), the detail has the facts, "Certifications" and "Awards" (`r2-2-...png`). Employer: the overview has Level, Experience, Work mode and the certifications and awards (`r2-3-employer-overview.png`); the anonymous cards show level, years and the names and years of certifications and awards (`r2-4-employer-talent-cards.png`), the detail too (`r2-5-employer-detail.png`). No person name next to an award |
| **R3** different fit scores | **Pass** | The 20 best recommended jobs of the demo talent: 77.7, 74.3, 72.3, 71.9, 71.0, 69.4, 68.9, 68.3, 62.8, 62.5, 58.9, 58.5, 57.9, 55.8, 55.0, 50.0, 49.0, 48.6, 47.3, 47.1 (20 different values). All 53 jobs: best 77.7, worst 29.2, difference 48.5, 52 different values. The 8 axes over 53 jobs have 25 (occupation), 45 (skills), 26 (methods), 49 (readiness), 47 (capability), 51 (pay), 8 (location), 32 (freshness) different values: no axis is constant. 5 jobs opened in the browser (4 spread over the ranking and the one with the lowest Location number): no row of the panel has the same number for all 5, and the numbers on the screen equal the API (`r3-1-fit-panel-job1.png`, `r3-2-fit-panel-job5.png`). Over the 50 talents (engine, `tests/test_differentiation.py --report`): top 20 has at least 19 different scores for every talent (mean 19.50), best minus worst at least 45.4 (mean 55.5), at most 1 exact tie in the top 10 of the employer order, 0 of 400 constant radar axes |
| **R4** About the role, full text | **Pass** | API: all 53 open jobs: no "…" or "...", the 7 standard headings and an "About <company>" heading, equal to the source text of `jobs.json`; 2,311 to 3,153 characters. Browser, 5 talent jobs and 5 employer overviews (4 demo jobs and one with a JD of 3,220 characters): the box is reached with Tab (4 to 6 presses), has a visible focus ring (outline of 2 px or more), scrolls with the arrow keys and Page Down, and End shows the last heading "How we hire" (`r4-1-talent-jd-end.png`, `r4-2-employer-overview-long.png`). `jd_parser` keeps a JD with a blank line after each heading (all 50 JDs come back byte for byte) |
| **R5** pager, 10/20/50 | **Pass** | Seven lists, each with 10, 20 and 50 rows per page, page 2 with other items, last page with the right count, the size is remembered after a reload: Jobs 68 (7/4/2 pages), Bookmarks 25 (3/2/1), Applications 15 (2/1/1), My jobs 19 (2/1/1), Applicants of one job 14 (2/1/1), Talent list 62 (7/4/2), Saved talent 25 (3/2/1). A Basic employer sees 5 cards and no pager. API: `pageSize=500` gives 50; a page past the end gives the last page. Screens `r5-1-jobs.png` to `r5-7-saved-talent.png`. A list with 10 items or fewer shows no pager (the design of FE-Core) |
| **R6** sort | **Pass** | For every list the order on the screen equals the order of the API, and the API order equals the values: Jobs `best` (scores descending, ties by id) and `newest` (postedAt descending); Bookmarks `saved` (the job saved last first), `best`, `newest`; Applications `updated`, `best`, `newest`; Talent list `best` and `updated` ("Recently updated": updatedAt descending over all 62 profiles, ties by id); My jobs and Applicants (one sort, newest first). A bad sort is a 400 with `fields.sort`. Screens `r6-1-jobs-sort.png` to `r6-4-talent-sort.png` |
| **R7** menu, user block, crown, benefits, locks | **Pass** | No "Settings" item in the menu of the talent or the employer; the user block is one link to Settings (also with the keyboard). A new Premium user: the crown, the gold ring (box shadow of 2 px) and the Premium chip show at once after "Try Premium", without a reload. Employer benefits: 4 x "Not used yet" -> after one list with more than 5 profiles only "See every talent profile" says "Used 1 time" -> after a compare, an invite and the Home charts all 4 say "Used 1 time" (`r7-2-employer-premium-not-used.png`, `r7-3-employer-premium-used.png`). Talent benefits: both "Not used yet" -> after the Home insights both "Used 1 time" (`r7-4-talent-premium-used.png`). Basic: gold "Premium" chips and locks in Settings (`r7-1-employer-basic-settings.png`), the lock on Compare in the menu, locks on Compare and Invite on the talent list. Back to Basic: the crown goes at once |
| **R8** 2 to 5, the 6th refused | **Pass** | API (talent): 2, 3, 4 and 5 jobs give 1, 3, 6 and 10 pairs and a skill matrix; 6 jobs and 1 job are a 400 with `fields.ids` "Choose 2 to 5 jobs to compare.". API (employer): 2 to 5 profiles give a radar with that many series, `areas` and `skillMatrix`; 6, 1 and no `jobId` are a 400. UI: the 6th job (and the 6th profile) is refused: the check box clears and the text "You can compare up to 5 jobs." (profiles) shows, and the basket stays at 5 (`r8-1-basket-5.png`) |
| **R9** Compare page | **Pass** | "Compare" item in the menu of both roles. The basket keeps 5 jobs across Jobs page 1, Jobs page 2, a job detail and Bookmarks. The page shows 5 cards and 5 radar lines, the 5 ids are in the address, a remove changes the address and the basket, a reload of the address shows the same jobs, "Add to compare" opens the picker (`r8-2-compare-5-jobs.png`, `r9-1-picker.png`). A Basic employer gets the locked page with an example picture and no data request (`r9-2-employer-basic-locked.png`); the API gives 403 PREMIUM_REQUIRED. A Premium employer compares 5 profiles for a chosen job; changing the job reloads the comparison; the page has no total, no score and no ranking of a person, and it says that it does not add the areas up (`r9-3-employer-compare-5.png`) |
| **R10** "Your path" panel | **Pass** | 5 jobs, including a job with no gap: a radar with 2 layers ("You have" filled, "Job requires" outline), the Fit list and the Gap list have the sizes of `summary.fitCount` and `gapCount`, the table of the radar equals the API axes, `monthsToClose` equals the longest gap plus 0.18 times the others (0.0, 6.1, 0.0, 8.2 and 11.6 months for the 5 jobs, all equal to the recomputed value; the two jobs with 0 months have no gap), no 12-month chart and no "projection" text, no item is both a fit and a gap (`r10-1-path-job1.png`, `r10-2-path-job4.png`) |
| **R11** process | Not a test | The plan lists the open items O1 and O2. QA found the file for O1 (defect D-1) |
| **R12** math docs and code | **Pass** | 4 worked examples were recomputed with the code, and the arithmetic of the doc was recomputed by hand. **F1** (`01_..._MODEL.md` section 8): fit 77.6 and SMF 67.4 as in the doc; skill credits 1.000, 0.688, 0.45, 0.45, 1.068; parts 65.3, 52.7, 97.6, 57.7, 74.2; bonus -2.71 and +2.66. **F2** (`02_..._ANALYSIS.md` section 6): months 6.0, 8.4, 1.6, 1.5, 1.3; severities 16.31, 15.50, 10.44, 9.07, 8.88; JRS 42.2, GSI 57.8, learner factor 0.914, months to close 10.2; path axes 80/70, 60/0, 50/30, 60/40, 100/0. **F3**: JPI 68.1 with parts 100.0, 43.9, 66.0, 98.1, 70.0, 63.8; the same for B and A. **F5**: S_cap 60.6, S_wage 63.3, S_loc 100.0, S_rec 76.8, FRS 71.2. Two rounding notes (not errors): the doc writes 10.2 months, and the sum with the rounded months gives 10.27; the doc sums 77.66 for the fit parts and the rounded parts give 77.64 |

## 4. Plan points that are unclear (not guessed)

* **N-1 (R2).** "Every one of the 50 jobs has all four" can mean that the four fields exist (true), or that each list is not empty (false for 4 jobs without a certification or award, and for 34 jobs without an award kind). The data agent's validator allows an empty list. The page says "This job does not ask for a certification (or an award)." QA treats the first meaning as the plan. The lead must say if the second meaning is wanted.
* **N-2 (R5).** The pager is hidden when a list has one page and 10 items or fewer. This is the design of FE-Core (pager hidden when `total` is at most the smallest size). The plan says "a pager on all lists". QA treats a short list without a pager as correct.

## 5. The test results in detail

### 5.1 Before and after

| Run | Result |
|---|---|
| First run of `python run_tests.py --formulas` | 666 tests OK (75.7 s), 32 checks OK |
| First runs of the check scripts (stand-alone) | core 175 of 179 (4 stale checks of the stub page, see F-9), talent 279 of 279, employer 205 of 205, compare 191 of 191 |
| Old `e2e_demo.py`, `e2e_journey.py` | They expected the old product (old compare, old texts, old demo data). Rewritten (section 6) |
| Final runs | see section 1. Run 3 of `--browser` failed once in `check_fe_core` (a race in the test, F-10). Run 4 passed all 7 stages |

### 5.2 New and changed test files

| File | What |
|---|---|
| `tests/browser/e2e_common.py` (new) | Shared helpers: the report that prints each step, the API client (127.0.0.1), sign in, keyboard keys, a platform starter |
| `tests/browser/e2e_demo.py` (rewritten) | 74 steps. The new demo story: Teal Heron / Linh Nguyen, Alex Morgan at Bluebushworks and the 4 demo jobs; the menu without Settings; the user block; the pager, the page size and its memory; the sort (order checked against the API); the JD box with the keyboard; the path panel; the compare basket and page; Settings and the Premium switch; the employer's Basic and Premium talent list; compare; applicants and review |
| `tests/browser/e2e_journey.py` (rewritten) | 45 steps. A new talent uploads a DOCX CV (the desired role is missing: the hint), edits the level, adds credentials, accepts the skills; a new employer posts a job with the V2 fields; apply; review; interview; offer; feedback; delete the account |
| `tests/test_privacy_v2.py` (new) | 15 tests. The privacy scan of every employer endpoint (section 7) |
| `tests/test_reference_parity.py` (new) | 15 tests. `reference.js` against the taxonomy (section 9) |
| `tests/test_qa_fixes.py` (new) | 7 tests for the fixes F-3, F-4 and F-8 |
| `tests/browser/qa_acceptance.py`, `qa_a11y.py`, `qa_perf.py`, `qa_xss.py` (new) | The QA scripts of this file |
| `run_tests.py` | New stages and the docstring; the clean environment of the browser stages (see F-9) |
| `tests/browser/check_fe_core.py`, `check_fe_compare.py`, `check_fe_talent.py`, `check_fe_employer.py` | Updated assertions (F-9) and one new check (F-5) |

## 6. Leftovers of the removed domains and of the old wording (task 3)

Words searched in the whole project: nurse, nursing, AHPRA, accountant, accounting, CPA, hospitality, warehouse, civil engineer, chef, marketing manager, supply chain, logistics, "Industry" as a label, "job seeker", "candidate" in text for users, "Licence readiness", "12-month", "projection".

### Fixed

| Where | What | Fix |
|---|---|---|
| `jinder_platform/jinder/translation.py` last role pair | Any title that ends with "Engineer" gave the card "Software Engineer" (Civil, Mechanical, Electrical, Chemical Engineer, Engineering Manager ...) | Stricter test (F-8) |
| `jinder/routes/recruiter.py:101` | The error "Choose a category." for a missing domain | "Choose a domain." (F-4) |
| `app/styles.css` | 12 rules `.lc-*` of the removed 12-month chart | Removed (nothing used them) |
| `app/js/views/landing.js` lines 38, 44, 45, 49, 53 to 55 | The picture of the landing page: "Marketing Executive", "Trade marketing exec", "Office coordinator", a campaign gap | ICT examples (Data Analyst, BI Specialist, Informatica, Power BI, Apache Airflow) |
| `app/js/components/onboarding.js` line 623 | The placeholder "e.g. Marketing" | "e.g. Computer science" |
| `app/js/config.js` | `MOCK_JOBS_CSV_URL` and its comment (not used) | Removed |
| `app/serve.ps1` | The route that served the old CSV file | Removed |
| `AI_Rule.md` Rule 2 last bullet | It said that the mock has non-ICT data | Rewritten |
| `jinder_backend_engine/docs/01_BACKEND_DEVELOPMENT_GUIDE.md`, `03_API_SPEC.md` | Documents of the earlier prototype: nurse examples, AHPRA, `/api/seeker/projection` | A note at the top: earlier prototype, version 1, the product API is in `jinder_platform/docs/API_NOTES.md` |
| `jinder_frontend/prompt.md` Appendix | 7 embedded copies were different from the files (`landing.js`, `onboarding.js`, 5 mock files) | Copied from the files. All 19 embedded copies are now equal (checked) |

### Kept, with the reason

| Where | Reason |
|---|---|
| `jinder/cv_lexicon.py:65-66, 554`, `jinder/cv_parser.py:206, 222-223, 243, 861-862, 1023` (nurse, accountant, chef, "Logistics" in an employer name, "retail", "finance" as words of a CV) | The CV reader must know the titles and employers of other fields so that it reads a title and gives no domain for such a CV. A test checks it (`test_cv_rules.py:993`: a nurse CV gives no domain) |
| `jinder/routes/recruiter.py:582` (comment "Licence readiness") | It explains why the key `statutory` has the label "Certification readiness" |
| `jinder_backend_engine/data/synthetic/*.json` (14 + 6 + 2 hits), `ict_taxonomy.json:698, 1130` | The words are "data warehouse", "cloud warehouse", the tool Chef (an alias of a configuration tool) and "Marrowgate Labs makes freight and warehouse software": a client of a job, not a field of work of the job |
| `jinder_backend_engine/data/australian_*.json/csv`, `international_candidates_dataset.csv`, `real_resumes_dataset.csv`, `data/reference/role-mappings.reference.json:30` | Data of the earlier prototype. The platform does not read them (BE.md section 10). They stay in the zip (about 3 MB packed) |
| `docs/V2_PLAN.md`, `docs/changes/*.md`, `docs/CHANGELOG_V2.md`, `docs/FORMULAS_IN_THE_PRODUCT.md`, `docs/API_NOTES.md`, `Docs/DESIGN.md` (723, 733, 939, 979), `AI_Rule.md:91`, `prompt.md` (456, 870-873, 1676, 1697), the engine `.md` files (02, 04, 06, MASTER_PLAN) | They say that the old thing is gone (no AHPRA rule, no 12-month projection, "Certification readiness" and not "Licence readiness") |
| `Docs/Skill_Bridge_*.md`, `spec/**` ("sushi chef", "projection" of data) | Read-only source documents (AI_Rule Rule 9) |
| Tests and fixtures (nurse CVs, "Chef" in `test_formulas.py`, old words in `test_taxonomy.py` ...) | They test that the old things are refused or ignored |
| The chip "Cross-industry" on translation cards (`onboarding.js:287`) and "cross-industry experience" in the landing text and `index.html` | A concept of the PRD: a translation from another industry (for example a quantitative analyst to a Data Scientist). It is not the label "Industry" of a field. The lead can change the words |
| "candidate" in the app | Only in code, comments, URLs (`#/candidates`), the API role value and the demo e-mail `candidate@demo.jinder.app`. No visible text. The same for "recruiter". "job seeker" is only in file names and keys (`05_job_seeker_ranking_feed.py`) |

### Mock (`js/api/mock/*`): being converted by the MOCK-ICT agent

The first scan found these hits (before the conversion): `cv-samples.js` 9, 10, 14, 38; `jd-samples.js` 5-9, 17-24, 45, 47; `jobs.js` 15, 16, 18, 19, 77, 79, 232; `seed-jobs.js` 19-23, 32-36, 48, 61-62, 71-79, 87-88, 100-101, 149-179 (also real company names and real ad text); `translation.js` 27-31, 41-42, 59, 61; `seed-demo.js` 17-49, 84, 105; `routes-recruiter.js` 41 ("Choose a category."); `config.js` 21 (Harbour Logistics). The MOCK-ICT agent converted all of them (`docs/changes/MockICT.md`). After that QA found only the hits of section "Fixed" (`landing.js`, `onboarding.js`, `config.js`, `serve.ps1`, `AI_Rule.md`).

## 7. Privacy audit (task 4)

The permanent test is `tests/test_privacy_v2.py` (15 tests, 3 seconds). It makes three talents with private values ("Zelda Quixote" and others, a study country, original titles, evidence lines), a Premium and a Basic employer, and calls **every employer endpoint**: candidates (sort `best` and `updated`, pages 1 and 2, saved), candidate detail (own test talent and sample talent), compare of 3 and 5 profiles and the errors (1 id, 6 ids, Basic 403), jobs, job, applicants, review, stats, entitlements, notifications, an invite, and the Basic employer's list and detail.

| Check | Result |
|---|---|
| No key named score, fit, rank, overall, total (on a person), tss, merit, email, phone, name (of a person), studyCountry, country, nationality, visa, age, gender, evidence, cv, password, token, hash in any of 30 answers. Allowed: `name` of a skill, certification or award; `total` of a list or the number of skills of the job ("8 of 10"); `email: false` of a notification | Pass |
| The scanner can fail: it finds 10 kinds of made-up leak (a test of the scanner) | Pass |
| A person has only the keys of the shared profile: a card has 20 keys, a detail 26, a compare profile 12, a snapshot 18, an applicant 11; a certification has `name`, `issuer`, `year`; an award has `name`, `kind`, `year` | Pass |
| No private value in any answer: names, e-mails and e-mail names of all talent accounts (except people who agreed to share), study countries, evidence lines and original titles of all 50 sample talents and the 3 test talents | Pass |
| The alias does not contain a word of the real name | Pass |
| Before consent: `identity` is `null` for every application and no name or e-mail is in the review or the applicant list. After a talent chooses a time and ticks the consent box: `identity` is `{name, email}` in that application only; the lists and the other application stay without it | Pass |
| **D5**: the names and years of the certifications and awards of a talent are visible in the card, the detail, the compare and the application snapshot (also for a Basic employer in the detail), and no person name is next to them | Pass |
| A talent gets 403 on the employer endpoints; no token gives 401 | Pass |

Findings: the shared profile keeps `issuer` of a certification and `kind` of an award (the lead decided so; BE.md section 8). The screens do not show the issuer. No leak was found. Text that a person writes (the note of an application, an award name) is free text: the server removes e-mail addresses and phone numbers, but not a name that the talent writes on purpose.
`tests/browser/qa_xss.py` puts markup (`<img onerror>`, `<script>`) into award, certification, job title, job description and application note, and looks at 15 screens of both roles: the markup shows as text, nothing runs, no tag is injected, no CSP report (18 checks pass).

## 8. Keyboard, names, focus, 390 px (task 6)

`tests/browser/qa_a11y.py` (44 checks, all pass), screenshots `a11y-*.png`.

| Check | Result |
|---|---|
| Tab order on the Jobs list | After a page change the router puts the focus on the heading, so the first Tab goes into the page (search box, location, Search, sort select, the cards, the pager). Shift+Tab from the heading goes backwards through Sign out, the user block (**one** link "Account settings, Linh Nguyen"), 6 menu links, the menu button and the logo. The sort select comes before the first card. The pager comes after the cards (rows per page, Previous, numbers, Next), then the basket bar (`a11y-1-tab-jobs-list.png`). There is a "Skip to content" link |
| Name and focus ring | 77 stops of the Tab key: every stop has an accessible name and a visible focus indicator. Every visible control on 14 screens (7 talent, 7 employer) has a name |
| Sort and pager | The sort select keeps the focus after a change and a live region says "Sorted by ..." |
| JD box | A labelled region, focusable, ArrowDown and PageDown scroll it, Home goes to the top |
| Compare basket and picker | Enter on "Add to compare" opens the dialog and the focus goes into it. In 60 Tab and Shift+Tab presses the focus is 54 times in the dialog and 6 times on the browser bar (the behaviour of a native modal dialog), never on the page behind it. All controls have names. Esc closes it and the focus returns to the button (`a11y-2-picker.png`). Each Remove button says "Remove <title> from compare" |
| Path table | A caption, column headers with `scope`, a row header for each skill group, and the status is a word (Fit, Gap, Above). The radar charts have `role="img"` and a label with all the numbers |
| 390 px, no sideways scroll of the page | Home, Jobs list, Job detail, Compare (3 jobs), Settings, Employer talent list, Job form, Job overview: the document is 390 px wide on all 8. The wide tables of Compare scroll inside a focusable, labelled region. Pager, sort and buttons are at least 44 px high (`a11y-390-*.png`) |
| Colour contrast (WCAG AA) | **Finding A11Y-1 (open).** 55 kinds of text on 10 screens are below 4.5:1. The root causes: the token `--muted` (#868e96, 3.3:1 on white, 2.8 to 2.9:1 on tinted rows), accent text and links (4.1 to 4.3:1), white text on the accent colour (badges and the avatar, 3.7 to 3.8:1), `chip-yellow` (3.1:1). This is the design debt that `Docs/DESIGN.md` already notes. QA did not change design tokens |

## 9. The open points of task 5

| Point | Result |
|---|---|
| (a) JD with a blank line after each heading | `jd_parser.parse_jd` returns the 50 JDs byte for byte and keeps a custom text with the blank lines. `jd-view` shows the headings (`h3`), the paragraph and the lists: 9 headings on every demo job (e2e_demo, qa_acceptance) |
| (b) The pick-lists match the taxonomy | `tests/test_reference_parity.py`, 15 tests: DOMAINS, SPECIALISATIONS, ROLES (53), CERTIFICATIONS (38: name, issuer, domains, tier), AWARD_KINDS (12), FIELDS_OF_STUDY, CITIES, WORK_TYPES, SKILL_NAMES (172), SKILL_SUGGESTIONS, LEVELS, WORK_MODES, SKILL_LEVELS, and the lists of `jinder/reference.py`. The test parses the JS file in Python. No word of another field |
| (c) Migration of the current database of the user | A copy of `var/jinder.db` and `var/uploads` (the file was only read; its SHA-256 did not change). The first start printed the warning and "Old data: kept as `jinder.db.v1.bak`. Nothing was deleted". Result: `jinder.db.v1.bak` equal to the old file byte for byte, `uploads.v1.bak` with the 2 CV files, a new `jinder.db` (schema version 2, 50 jobs, 50 sample talents), an empty new `uploads`. The old file had schema version 1, 139 talent rows, 1 employer, 387 jobs, 7 applications. A second start with `--demo` made the demo accounts (and the demo talent had 23 recommended jobs). **The old accounts are not in the new database** (decision F10: the user must create a new account, or use `--demo`) |
| (d) First start from an empty folder, no `--demo` | No demo account (login gives 401), 50 jobs, 50 sample talents, 0 applications, no `.bak` |
| (e) `--demo` twice | Same counts after the second start (54 jobs, 52 users, 7 applications, 217 events, 0 duplicate e-mail or alias). The passwords are new at each start; the old ones stop working. A start without `--demo` keeps the data |
| (f) Premium switch | The crown, ring and chip show at once for a talent (e2e_demo) and for an employer (qa_acceptance R7); the lock of the Compare menu item goes |
| (g) `?mock=1` | `check_mock_ict.py`: 81 of 81. The mock parts of the other check scripts pass after the update of 3 assertions (F-9) |

## 10. Performance and robustness (task 7)

`qa_perf.py`: 53 open jobs, 51 profiles for the employer, 20 calls each, sequential, on this computer (milliseconds, minimum / mean / maximum):

| Endpoint | min / mean / max |
|---|---|
| Talent recommended, page of 10 | 86 / 118 / 173 |
| Talent recommended, page of 50 | 118 / 146 / 187 |
| Talent jobs list, page of 50, newest | 203 / 245 / 363 (the slowest) |
| Talent job detail (path, 8 axes, similar jobs) | 65 / 84 / 113 |
| Talent compare with 5 jobs | 50 / 62 / 78 |
| Employer candidates, Basic (5) | 67 / 86 / 126 |
| Employer candidates, page of 50, best | 187 / 207 / 266 |
| Employer candidates, page of 50, updated | 192 / 233 / 332 |
| Employer candidate detail | 27 / 32 / 44 |
| Employer compare with 5 profiles | 30 / 47 / 79 |
| Bookmarks, applications, stats, my jobs, applicants (8 more) | 7 to 53, all small |

All are under 1 second. The server log of each run has no ERROR line and no traceback (since fix F-3). With **4 clients at the same time** a round of two calls (job detail and talent list) has a mean of 976 ms and a maximum of 1.9 s, with no error (finding P-1).
Note for scripts on Windows: a request to `localhost` can take 2 seconds for each call (the computer tries the IPv6 address first; the server listens on IPv4). Browsers are not affected. Use 127.0.0.1 in scripts (finding P-2).

## 11. The release zip (task 8)

`make_release.py` (copy in the scratchpad of the session) builds `Jinder.zip`: 375 entries, 2.9 MB. It has `jinder_backend_engine/data/synthetic/`, `data/reference/ict_taxonomy.json`, `intelligence_engine/engine_common.py`, `jinder_platform/tests/fixtures/cv/` (24 files), the docs and the new tests. It has no `var/` content (only `var/.keep`), no `.bak`, no `.db`, no `__pycache__`, and no 54 MB resume file.
**Changes of the script:** `.bak` is a skipped suffix; the folder `jinder_platform/docs/changes/qa-shots/` is skipped (8.6 MB of screenshots).
Check: the zip was extracted into a new empty folder; `python start.py --demo --port 8161` (no `JINDER_VAR_DIR`) started, `/api/health` is ok, the data is in the unzipped `var/`; `e2e_demo.py` passed 73 of 73 against it. `python run_tests.py` in a second unzipped copy: 720 tests OK (the first try of that copy had one failing test, a flaky test: F-12; it was fixed and the zip was built again).

## 12. Defects

### Fixed by QA

| # | Where | Defect | Fix and test | Severity |
|---|---|---|---|---|
| F-1 | `views/settings.js` ("What employers see") | The panel of the talent in Settings showed the version 1 rows. It did not show level, exact years, certifications, awards or skill levels, that employers see (R2, R7). The Home panel showed them | It uses `sharedFactsHtml` and `skillChipsHtml` as Home does. Checked in `e2e_demo.py` | minor |
| F-2 | `components/status.js` | In "Skill by skill" a skill that the talent has below the asked level was named "Related" (the same word as a related skill). The path panel says "Below level" for the same skill | Label "Below level" and "You: Proficient, Needs: Advanced" (`fitStatus` of the API). Checked by eye and by `e2e_demo` (the card text) | minor |
| F-3 | `jinder/http_server.py` | When a browser closes a connection, the server printed a long traceback to the log for each connection (5 in one run). A clean log is a QA criterion | `JinderServer.handle_error` drops connection resets and logs only the type of another error. `tests/test_qa_fixes.py` (3 tests) | minor |
| F-4 | `jinder/routes/recruiter.py` | The error text for a wrong domain said "Choose a category." (the visible word must be "domain") | "Choose a domain."; `test_employer_flow.py` and `test_qa_fixes.py` | minor |
| F-5 | `api/errors.js`, `api/http.js`, `views/compare.js` | The Compare page did not read `missing` (the ids that the API names in a 404 or 400). It showed a Remove button for each item | `ApiError.missing`; the named items are first, marked "Not found" (or "Over the limit") and named in the message. `check_fe_compare.py` has a new check | minor |
| F-6 | `app/styles.css` | 12 unused rules `.lc-*` (the 12-month chart) | Removed | cosmetic |
| F-7 | `landing.js`, `onboarding.js`, `config.js`, `serve.ps1`, `AI_Rule.md`, the 2 legacy docs, `prompt.md` embedded copies | Leftover words and files (section 6) | Fixed (section 6) | minor |
| F-8 | `jinder/translation.py` | The last role pair gave "Software Engineer" to any title that ends with "Engineer" (Civil, Mechanical, Electrical Engineer, Engineering Manager ...). The plan says that a title that is not an ICT title gives no role card | A stricter test (a bare "Engineer" or "Developer", a title that starts with "Software", or an ICT word before "Engineer" or "Developer"). `tests/test_qa_fixes.py`: 18 non-ICT titles give no card; 20 ICT titles give one (PHP Developer, Unity Developer, Embedded Software Engineer ... still do). "Quality Engineer" still gives "QA Engineer" (it can be an ICT title) | major (wrong card for a non-ICT person) |
| F-9 | `check_fe_core.py`, `check_fe_talent.py`, `check_fe_employer.py`, `run_tests.py` | 4 checks of `check_fe_core.py` expected the stub of the Compare page ("Coming next."). 3 mock checks expected the old mock data. My new `run_tests.py --browser` first passed the database of the unit tests to the browser stages (the unit tests set `JINDER_DB_PATH` in the process) and the stages could not start | Assertions updated to the real page and the ICT mock. `run_tests.py` gives each stage a clean environment and runs `check_mock_ict.py` too | test problem |
| F-10 | `check_fe_core.py` (`check_tray`, reported by the MOCK-ICT agent) | `.compare-tray-title` was null: "the basket survives a reload" | **A test problem (a race), not a product defect.** The check started the reload and then waited for the tray in the page that was still the OLD page; sometimes it read the new page before the tray was drawn. It passed in 2 of 3 full runs and in the stand-alone runs. Fixed: the check puts a marker in the old page and waits until the marker is gone. The product code was not changed | test problem |
| F-11 | my first versions of `e2e_demo.py` and `qa_acceptance.py` | The "reload" of a page was a `goto` of the same address, which only changes the fragment and does not reload. The 12-month words matched "12 months to close" | New helper `reload()` (a real reload, a marker in the old page). The words are "12-month", "next 12 months", "projection" | test problem |
| F-12 | `tests/test_employer_flow.py` (`test_post_list_badge_edit`) and `tests/test_talent_flow.py` (`test_bookmarks`) | The two tests make 2 items one after the other and expect "newest first". The clock of Windows ticks every few milliseconds (43 different values in 200 ms on this computer), so two quick requests can have the same time, and the list then orders them by id. The first test failed once in the unzipped copy (1 of 6 runs) | A pause of 50 ms between the two items. The product is right (a tie is broken by the id, as the plan says) | test problem |

### Open, by severity

| # | Severity | Where | Steps | Expected | Actual |
|---|---|---|---|---|---|
| **D-1** | **major** | CV text reader (`jinder/textextract.py`, `_find_gutter`, `_blocks`) | Upload the own CV of the user (`C:\Hackathon\CV_Tran_Quoc_Bao_Data_Analyst.pdf`, the same file as `var/uploads/1627a39f-....pdf`, open item O1) | The 2 certifications ("Microsoft Certified: Power BI Data Analyst Associate (PL-300), 2023" and "Google Data Analytics Professional Certificate, 2021") are found | The current role (Senior Data Analyst), the desired role (Data Analyst), the level (Senior), the years (7.8) and the domain (Data) are right. **Certifications are not found.** The last block of page 1 and the first block of page 2 have two columns (CERTIFICATIONS and LANGUAGES, then WORK RIGHTS AND AVAILABILITY), the rest of the page has one column. `_find_gutter` needs a free strip in all but 8% of the lines, so it finds no gutter and the lines of both columns are mixed ("Microsoft Certified: Power BI Data Analyst Vietnamese - native"). Suggested fix for the CV agent: find a "band" of 3 or more consecutive lines with a free strip, split only that band, and join the left columns of two pages. The result is empty, not wrong (plan R1). Text of the CV is not copied into the repository |
| **D-2** | **minor to major** (accessibility) | `styles.css` tokens | Run `qa_a11y.py`: contrast of the text on 10 screens | 4.5:1 for normal text | 55 kinds of text are below (3.3:1 for muted text). See section 8 (A11Y-1). Fix: darken `--muted` (for example `#6c757d`, 4.7:1 on white), a darker accent for text and links, dark text on yellow chips. It changes `Docs/DESIGN.md` and the design |
| **D-3** | minor | Server (`catalogue.TalentContext`, `routes/recruiter.py`) | 4 clients ask at the same time (job detail and the employer talent list) | Each answer under 1 second | A round of two calls has a mean of 976 ms and a maximum of 1.9 s. There is no cache: each request runs the formulas for all jobs or all profiles in one process (about 200 ms for 51 profiles) |
| **D-4** | minor | Words for one state of a skill on 3 screens | Open a job where the talent has a related skill | One word | Job detail: "Related, via Python". The Compare page: "Missing" (the related skill does not count). The path panel: gap "Missing" with the note "You have a related skill: Python." The notes explain it, but the three words differ |
| **D-5** | minor | `start.py` message and `README.md` | Call the platform from a script on Windows with the address in the message | Fast | The message shows `http://localhost:PORT/`. A script that uses it waits 2 seconds for each request (the server listens on 127.0.0.1 only). A browser is fine. Use 127.0.0.1 in the message or listen on both addresses |
| D-6 | cosmetic | Employer talent list at 390 px | Open it on a narrow screen | Full width cards | The card is inside a second box with a large left padding (see `a11y-390-employer-talent-list.png`). No sideways scroll |

### For the lead and the Docs agent

* QA updated these places for its own fixes: `prompt.md` (the `skillMatchHtml` line, the Settings panel, the compare error state, `errors.js`) and `Docs/DESIGN.md` (`skill-match`, the known gaps). Still to do for the Docs agent: the text of `prompt.md` about the mock (not the embedded files, which are equal to the app): `MOCK_JOBS_CSV_URL` and the CSV (lines 14, 86, 146, 1047, 1262), `serve.ps1` with `$dataFiles` (1650, 1702), the old mock demo story (Operations Coordinator and others, from line 1741), and the new scripts and flags in `README.md` (`--browser`, `--browser-quick`, `qa_*.py`).
* `docs/changes/qa-shots/` is for the team only. The release script skips it.
* **Information for the user.** The user's own database (`var/jinder.db`, schema version 1) will be renamed to `jinder.db.v1.bak` at the first start of this version. The old accounts are in that backup, not in the new database. A server that runs now on port 8095 uses the old code in its memory and serves the new files: restart it.

## 13. What was not tested

* Screen readers (NVDA, JAWS, VoiceOver). Names, roles and live texts were checked in the DOM only.
* Edge, Firefox and Safari (only Chrome). Real touch devices (390 px is a narrow window of Chrome).
* A scanned CV (an image), a password-protected PDF, a very long CV (more than 30 pages), other CV layouts than the 23 fixtures and the 124 text CVs of the CV agent, and the CV of the user in the browser (only the parser was run on it: the screens are tested with the fixtures).
* More than 4 clients at the same time, a long run (many hours), a database with thousands of users.
* The real e-mail sending (SMTP). The outbox only records messages.
* The server on port 8095 (it is the user's, not touched).
* The number of the unit tests of the release zip was run once; the browser tests were not run inside the unzipped copy (only `e2e_demo.py` against it).
