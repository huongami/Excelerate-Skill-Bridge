# Jinder V2 plan (feedback round 2)

This file is the **single source of truth** for the 12 feedback items. Every agent reads it first, works only in the files that it owns (section 8),
and does not change a contract (sections 4 to 7) without telling the lead. If something here is unclear or two parts disagree, **stop and report it. Do not guess.**

## 0. Rules for every agent

1. Read `jinder_frontend/AI_Rule.md` (privacy and security rules) and this file before you write code.
2. Only edit the files that you own (section 8). If you need a change in a file of another agent, write it in your final report ("Needs from X: ..."). Do not edit it.
3. Use the Write and Edit tools for files. Do not write code with shell heredocs or `echo` (this caused NUL and backspace bugs before). Keep LF line endings. Python 3.9 compatible, standard library only.
4. Privacy does not change: an employer never gets a name, an email, a country, a visa, an age, a gender, the CV text, the evidence lines, or a single score on a person.
   An employer sees: per-skill match, coverage, levels, certifications, awards (names and years only), and an order. Never a total.
5. No inline style and no inline script (CSP). Charts are SVG with CSS classes. Every chart has a table with the same numbers.
6. All sample data is **synthetic and clearly fake**: no real company, no real person, no real job ad. Company names are invented (check that they are not well-known brands).
7. Do not stop or restart the server on port 8095 (it is the user's). Use only your own ports: BE 8110, FE-Core 8120, FE-Talent 8130, FE-Employer 8140, FE-Compare 8150. Browser-test port 8197 is used by QA only. Chrome remote-debugging ports: use 9300 + the last digit of your port block.
8. Every change gets a test (unit test in `jinder_platform/tests`, or a browser check). Run `python run_tests.py` in `jinder_platform` before you report. Say the real result. If a test fails, say so.
9. Simple English in all text that users read and in all docs (short sentences, one idea each), like the existing docs.
10. In the final report list: what you did, files changed, tests run with result, what is NOT done, and "Needs from X".
11. Do not write docs into `prompt.md`, `DESIGN.md`, `AI_Rule.md` or `README.md` yourself. Write your doc changes as a short file `jinder_platform/docs/changes/<your-agent-name>.md` (what changed, new fields, new screens, new states). The Docs agent merges them at the end.

## 1. Decisions from the user (final)

| # | Decision |
|---|---|
| D1 | Data: write **new structured synthetic data**. Real-looking names are fine, real ads are not. **50 jobs + 50 talents.** |
| D2 | Remove all domains except Software Engineering, AI, Data from the demo product: data, pick-lists, post-job form, translation library. |
| D3 | Edit the **original formula files** in `jinder_backend_engine/intelligence_engine` directly. Keep the math docs consistent. |
| D4 | Level scale for jobs and talents: **Intern, Junior, Mid, Senior, Lead, Principal** (rank 0 to 5). |
| D5 | Certifications and awards: a Job lists **required/preferred certifications** and **preferred awards**. A Talent has both. Employers see them **at once** on the anonymous profile (names and years only, no person name). |
| D6 | Sort "time" for the employer talent list = **profile updated most recently**. For jobs = posted date. |
| D7 | "Your path to this job": a **radar with 2 layers** ("You have" vs "Job requires") over the requirement groups, plus a Fit list and a Gap list. **The 12-month line chart is removed.** The 8-axis "How this job fits you" panel stays. |
| D8 | The user icon **stays at the bottom of the left menu** and is clickable: it opens the account Settings. The "Settings" item leaves the menu. Premium users get a crown icon and a gold ring. "Highlight Premium" = (a) crown + gold ring, (b) account area lists the Premium benefits (used / not used yet), (c) a lock / gold badge on Premium features for Basic users. |
| D9 | Compare: a **"Compare" item in the left menu + a compare basket** (max 5, kept while the user browses). The Compare page is a full page. Employer: **talent vs talent (Premium)**. Talent: **job vs job (free)**. Up to 5 each. |

## 2. Defaults that I applied (the user can change any of them)

| # | Default | Why |
|---|---|---|
| F1 | Page sizes **10, 20, 50**; default **10**; the choice is remembered in the browser. Applies to every list of jobs or talent. Basic employer sees 5 talent and no pager (Feature 5 AC7). | "The user can choose the number" |
| F2 | Sort only (no new filters). Job lists: **Best match** / **Newest posted** (Bookmarks also: **Recently saved**, its default). Employer talent list: **Best fit for this job** / **Recently updated**. | R6 says "filter sort by fit and by posting time" |
| F3 | A new **employer job overview page** shows the full JD. The edit form keeps working, with the JD headings as a template. | R4 asks for the JD on the Employer page |
| F4 | JD text uses a small markup: `## Heading` lines and `- ` bullet lines. Standard headings: About the role, What you will do, What you bring, Nice to have, Tech stack, Certifications and awards, What we offer, About the company, How we hire. The page shows the JD in a box with a maximum height and a scroll bar. | R4 |
| F5 | The compare basket is stored in the browser (`localStorage`, one for each user and kind). The employer's talent compare needs a chosen job (the match is "for this job"). | simple, no new table |
| F6 | The UI word "Industry" becomes **"Domain"**; the values are the 3 domains. The profile key `industry` and `targetIndustries` do not change. | only 3 values are left |
| F7 | Years of experience: the band drop-down stays. An optional **exact years** number is added (the CV scan fills it). The formulas use the exact number when it exists, else the band middle. | the bands are too coarse to tell two talents apart |
| F8 | Skill level 1 to 5 (Beginner, Working, Proficient, Advanced, Expert) per skill. The talent can change it in the skill review step. A skill with no level gets 3 from "Moderate" evidence (Strong 4, Limited 2). | needed for different fit scores |
| F9 | New features work with the real backend only (as the radar and job compare did). The mock adapter keeps working for the old screens; new sections hide when the data is missing. | the mock is a prototype |
| F10 | On the first start, an old database (schema version 1) is **renamed to a backup file** and a fresh database is made. Nothing is deleted. | the old catalogue is not ICT |
| F11 | A desired role that the CV does not state is **left empty** (not guessed); the UI shows a hint. | no invented data in a profile |
| F12 | Sample talent profiles have `updated_at` spread over the last 60 days (so "Recently updated" is meaningful). | R6 |

## 3. Traceability: the 12 items

| R | The user said (short) | Becomes | Acceptance (what must be true) | Owner |
|---|---|---|---|---|
| R1 | The CV scan does not read the current job title, the desired job, the current level | CV parser reads **current role, desired role, level, exact years, certifications, awards**; onboarding shows them; each is editable | 12+ fixture CVs in different layouts (PDF and DOCX): current role found in ≥ 10, level found in ≥ 10, desired role found when the CV states one (objective, summary, "seeking") in 100% of those fixtures. A failed field is empty, not wrong. **The user's own failing CV is still needed** (open item O1) | CV, FE-Talent, BE |
| R2 | A job shows no experience, level, awards, certifications | Job card and job detail (talent) and the job overview (employer) show **Level, Experience (min–max years), Certifications (required/preferred), Awards (preferred)**. The talent profile and the anonymous employer view show **Level, Years, Certifications, Awards** | Every one of the 50 jobs has all four. The employer sees them on talent cards/detail. No person name next to an award | Data, BE, FE-Talent, FE-Employer |
| R3 | Reduce scope; fewer records; normalised data for the demo; SWE/AI/Data only; the overall fit of jobs is the same; give detail per job and per talent; rewrite the formulas if needed | 50 jobs + 50 talents, structured and detailed; non-ICT domains removed everywhere; formulas rewritten for ICT with levels, years, certs, awards, work mode | See section 9 "Differentiation tests": for every talent, the visible job list has distinct fit scores (≥ 18 of 20 distinct at 1 decimal in the top 20), a spread of ≥ 30 points between best and worst, and no radar axis is the same for all jobs | Taxonomy, Data, Formulas, BE |
| R4 | "About the role" is cut. Full text, headers as in the JD, scroll if the box is full, on Talent and Employer pages | Full JD (1,200–3,500 characters, ≥ 6 headed sections) stored uncut; shown with headings in a scroll box on both pages | No "…" cut in any of the 50 JDs. The scroll box is reachable by keyboard. Employer overview page exists | Data, FE-Core (component), FE-Talent, FE-Employer |
| R5 | Show a limited number of jobs/talent per page, then go to the next page; the user picks the number | Server-side pagination (`page`, `pageSize`) and a pager component on all lists | `pageSize` 10/20/50; page 2 holds different items; totals are right; the choice is remembered | BE, FE-Core (component), FE-Talent, FE-Employer |
| R6 | Add sort by fit and by posting time | `sort` parameter and a sort select on the lists (F2) | `sort=newest` is in date order; `sort=best` is in fit order; ties are broken by id (stable) | BE, FE |
| R7 | Settings moves into the user icon; Premium user has an own icon with a crown; highlight Premium features | D8 | The menu has no Settings item. The user block opens Settings. A Premium user sees the crown. Settings lists the Premium benefits with used / not used. Basic users see lock/gold badges. | FE-Core, BE (benefits data) |
| R8 | Compare is not limited to 2; up to 5 | Max 5 for both compare kinds | The 6th item is refused in the UI and the API (400) | FE-Compare, BE |
| R9 | Compare as its own page, not attached; talent vs talent, and add job vs job | D9: Compare menu item, basket, full page | `#/compare` page for both roles; items can be added and removed on the page | FE-Compare, FE-Core |
| R10 | "Your path to this job" rewritten: say what fits and what is a gap; chart as a spider | D7 | The panel has: radar (2 layers), Fit list, Gap list (each with have vs need and months). No line chart | BE (data), FE-Talent (panel), FE-Core (radar) |
| R11 | Analyse, plan, split the work, do not assume, ask when unclear | This plan + the questions that were asked | Open items are listed in section 10 | Lead |
| R12 | (the formulas) rewrite the calculation behind if needed | D3 + section 6 | Math docs and code agree; tests pass | Formulas |

## 4. Domain contract (data model)

### 4.1 Levels, skill levels

* `LEVELS = ["Intern","Junior","Mid","Senior","Lead","Principal"]`, rank 0 to 5.
* Typical years (guide for the formulas, not a hard rule): Intern 0, Junior 0–2, Mid 2–5, Senior 5–9, Lead 7–12, Principal 10+.
* Skill level 1 to 5: 1 Beginner, 2 Working, 3 Proficient, 4 Advanced, 5 Expert.

### 4.2 The taxonomy file (made first, by the Taxonomy agent)

`jinder_backend_engine/data/reference/ict_taxonomy.json` is the one list of names for the whole product. Data, formulas, parsers, pick-lists and the translation library all use these names (no other spelling).
It holds: `levels`, `skillLevels`, `domains` (3, with `specialisations`), `occupations` (ANZSCO-style code, title, domain, core skills with level, methods), `skills`
(name, group, aliases, related, `monthsToLearn` from zero to level 3, `rarity` 1.0 to 3.0), `skillGroups`, `certifications` (name, issuer, domain, tier, `prepMonths`, evidences skills), `awardKinds`
(kind, label, examples), `roles` (pick-list titles), `fieldsOfStudy`, `cities`, `workModes`, `workTypes`.

Domains (the only 3): **Software Engineering**, **AI & Machine Learning**, **Data**.
Skill groups (radar axes of "Your path"): `languages` Languages, `frameworks` Frameworks & libraries, `cloud` Cloud & DevOps, `data` Data & storage, `ml` ML & AI, `practices` Engineering practices, `collab` Collaboration.

### 4.3 Talent profile (new and changed keys)

| Key | Type | Notes |
|---|---|---|
| `level` | one of LEVELS or "" | current level |
| `yearsExperience` | number 0–40 or null | exact years. `years` (band) stays and is set from it |
| `certifications` | `[{name, issuer, year}]` | name from the taxonomy or free text (scrubbed) |
| `awards` | `[{name, kind, year}]` | `kind` from `awardKinds` |
| `translation[].level` | 1–5 or null | for skills (not for role and qualification rows) |
| `industry`, `targetIndustries` | domains | values = the 3 domains |
| `currentRole`, `targetRole` | as now | The CV scan fills them (R1) |

The shared (employer-safe) profile adds: `level`, `yearsExperience` (rounded to 0.5), `skillLevels: [{name, level}]` (`skills` stays a list of names), `certifications`, `awards`, `updatedAt`.
It still has no name, email, country, CV or evidence.

### 4.4 Job (new and changed keys)

| Key | Type | Notes |
|---|---|---|
| `level` | one of LEVELS | required level |
| `specialisation` | text from the taxonomy | e.g. Backend, Data engineering |
| `minYears`, `maxYears` | number, number or null | experience asked |
| `workMode` | Onsite, Hybrid, Remote | `location` stays a city or "Remote" |
| `skillRequirements` | `[{name, level 1–5, must: bool}]` | `skills` (names) stays as a list for the old code |
| `certifications` | `{required: [name], preferred: [name]}` | |
| `awards` | `{preferred: [awardKind]}` | |
| `educationMin` | text | e.g. "Bachelor's degree" |
| `description` | JD text with the markup of F4, **not cut** | `summary` = short text, ≤ 200 characters |
| `category` | one of the 3 domains | |

### 4.5 Database

`schema.sql` version 2 (`schema_info.schema_version = "2"`). New columns: `profiles.level`, `profiles.years_exact`, `profiles.certifications` (JSON), `profiles.awards` (JSON);
`translated_skills.level`; `jobs.level`, `jobs.specialisation`, `jobs.min_years`, `jobs.max_years`, `jobs.work_mode`, `jobs.education_min`, `jobs.certs_required`, `jobs.certs_preferred`, `jobs.awards_preferred` (JSON);
`job_skills.level`, `job_skills.must`. F10 for old databases. `docs/DATABASE.md` is updated by the Docs agent from `docs/changes/BE.md`.

## 5. API contract

All errors keep the existing shape (`{error:{code,message,fields?}}`).

### 5.1 Pagination and sort (R5, R6)

Every list endpoint takes `page` (default 1), `pageSize` (default 10, clamp 1–50) and `sort`. A bad `sort` is a 400 with `fields.sort`.
The response keeps the old list key and adds `page: { page, pageSize, total, totalPages }` and `sort`.

| Endpoint | `sort` values (default first) |
|---|---|
| `GET /jobs/recommended`, `GET /jobs` | `best`, `newest` |
| `GET /bookmarks` | `saved`, `best`, `newest` |
| `GET /applications` (talent) | `updated`, `best`, `newest` (old order stays the default) |
| `GET /recruiter/jobs` | `newest` (only) |
| `GET /recruiter/jobs/:id/applications` | `newest` (only) |
| `GET /recruiter/candidates` | `best`, `updated` |

`limit` is removed from these endpoints (`pageSize` replaces it). A Basic employer on `/recruiter/candidates` gets 5 items, `page.total` = the real total, `limitedTo` = 5 and `page.totalPages` = 1.
Stable order: ties are broken by id.

### 5.2 Compare (R8, R9)

`GET /jobs/compare?ids=a,b,c,d,e` (talent, 2 to 5 ids; else 400 `fields.ids` "Choose 2 to 5 jobs to compare.")

```json
{ "jobs": [ { "...JobCard": 0, "axes": [{"key","label","formula","value"}], "salaryMidpoint": 150000 } ],
  "axes": [{"key","label","formula"}],
  "pairs": [ { "a","b","index","tier","advice","salaryChange","parts":[{"key","label","value"}] } ],
  "skillMatrix": [ { "skill": "Python", "yours": 4, "byJob": { "<jobId>": { "required": 3, "must": true } | null } } ] }
```

`GET /recruiter/compare?ids=a,b,c,d,e&jobId=` (employer, **Premium**, 2 to 5 ids; `jobId` required, own job)

```json
{ "job": {"id","title","skills"},
  "candidates": [ { "id","alias","level","years","yearsExperience","roles","qualifications","certifications","awards",
                    "coverage","skills":[SkillResult],"otherSkills":[] } ],
  "radar": { "axes":[{"key","label","formula"}], "series":[{"id","alias","values":[0-100]}] },
  "areas": [ { "area","ranks":[{"id","position"}] } ],
  "skillMatrix": [ { "skill","required","must","byCandidate": { "<id>": { "level": 4, "status": "meets|below|missing|related" } } } ] }
```

No total and no ranking of people. `areas` replaces the "a is ahead" text with positions inside one area (F-04), never summed.
The old `?a=&b=` form is removed. A basic employer gets 403 `PREMIUM_REQUIRED`.

### 5.3 Job detail (talent) — `GET /jobs/:id`

`job` carries the new job keys of 4.4 and the full `description`. `bridge` becomes:

```json
{ "occupation": {...}, "readiness": {...}, "score": 71.4,
  "axes": [ ...the 8 radar values... ],
  "path": {
    "axes":  [ { "key": "languages", "label": "Languages", "group": "languages", "required": 80, "have": 60, "status": "gap|fit|above" } ],
    "fit":   [ { "kind": "skill|experience|level|certification|award", "label": "Python", "have": "Advanced", "need": "Proficient", "note": "" } ],
    "gaps":  [ { "kind": "missing|below_level|experience|level|certification", "label": "Kubernetes", "have": "none", "need": "Proficient", "months": 3.5, "must": true, "note": "" } ],
    "summary": { "fitCount": 7, "gapCount": 3, "monthsToClose": 5.5, "readinessTier": "..." } },
  "gaps": [ ...kept for compatibility... ] }
```

`bridge.projection` is **removed** (and the 12-month chart with it). Employer job (own) uses `GET /recruiter/jobs/:id` with the same job keys (no `bridge`).
Radar values `required` and `have` are 0–100. For a skill group: the average over the job's skills in that group of (level / 5 × 100) for `required`, and of min(have, 5)/5 × 100 for `have`, weighted by `must` (the weight rule is in `01_SKILL_MATCHING_MODEL.md`). Extra axes: `experience`, `level`, and `certifications` (only when the job lists certifications).

### 5.4 Profile, jobs, entitlements

* `PATCH /me` accepts the new profile keys of 4.3 (cleaned, scrubbed). `GET /me` returns them.
* `POST /recruiter/jobs`, `PATCH /recruiter/jobs/:id`, JD import: accept and return the new job keys of 4.4. The old minimal body still works (new keys optional; `level` defaults to "Mid").
* `GET /recruiter/candidates` and `/recruiter/candidates/:id`: cards and detail add `level`, `yearsExperience`, `certifications`, `awards`, `skillLevels`, `updatedAt`.
* CV parse result (`GET /cv/parse/:id` → `result`) adds `currentRole`, `targetRole`, `level`, `yearsExperience`, `certifications`, `awards`, `skills[].level` and `found: {currentRole, targetRole, level, yearsExperience, certifications, awards}` (booleans, so the UI can show "not found" hints).
* `GET /entitlements` adds `crown: bool` (= premium) and `benefits: [{ key, label, description, available, used, usedCount }]`. Employer keys: `all_talent`, `invite`, `compare`, `advanced_charts`. Talent keys: `skills_to_learn`, `skill_demand`.
  `used` is true when an event of that kind exists for the user (`talent_list_full`, `invite`, `compare_view`, `insights_view`).
* `canCompare` stays employer-only. Job compare for a talent is free. `entitlements.compareMax = 5`.

## 6. Formula contract (Formulas agent)

Edit `jinder_backend_engine/intelligence_engine/01…06*.py` and their `.md`, `MASTER_PLAN.md`, `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, `docs/04_DATA_AND_SCORING_SPEC.md`, `run_verification.py`, the engine `README.md`.
The legacy prototype in `jinder_backend_engine/backend/` is out of scope; the formulas must still **accept the old dictionary shape** without an error (new keys are optional, with safe defaults).
**All score math lives in the engine files.** The platform only builds dictionaries and calls the functions.

Engine input (the bridge builds these):

```
candidate: id, alias, current_title, level, level_rank (0-5), years_experience (float), domain, specialisation,
           target_anzsco_code, target_roles[], highest_education, field_of_study[],
           skills[{skill_name, name, skill_type Direct|Transferable, level 1-5, years, last_used_year}],
           certifications[{name, issuer, year}], awards[{name, kind, year}],
           preferred_location, locations[], work_modes[], work_types[], cv_raw_text (talent screens only)
job:       id, title, company, category (domain), specialisation, level, level_rank, min_years, max_years,
           city, location, work_mode, type, anzsco_code, anzsco_title, salary_min, salary_max (AUD per year),
           required_skills[{name, level 1-5, must}], requirements[names], certifications_required[], certifications_preferred[],
           awards_preferred[kinds], education_min, days_old, description
```

Requirements for the new math (each is a test):

1. **Continuous.** No fixed-step tier decides a score alone. Use smooth functions of levels, years, rarity, salary and age, so that two different jobs or talents seldom tie.
2. **F1** gives, per job skill, a credit in [0,1] from `have level / need level` (partial credit below, a small bonus above, related-skill credit through `related`), weighted by `must` (2×) and `rarity`. It returns `skill_breakdown`.
   It also scores the occupation distance (finer than the old 5 steps; specialisation adds closeness), the method skills, the experience multiplier from years against the job's `min_years`/level, and a level-fit part. It returns the sub-metrics used by the "How this job fits you" axes.
3. **F2** returns gap items `{skill|item, kind: missing|below_level|certification|experience|level, have_level, need_level, months, must}` and **strength items** (met requirements). Months come from `monthsToLearn`, the level difference, `prepMonths` for certifications and the parallel-learning rule. Missing a **required certification** is a gap with `months = prepMonths`; it is not a statutory blocker.
4. **F3** compares two jobs with the new facts too (level, work mode, skill overlap weighted by level). It keeps `compare_two_jobs`, `get_job_salary_midpoint`, `compare_multiple_jobs`.
5. **F4** (benchmark) uses level and years and the skill depth (average level of the skills the job asks for), certifications and awards. It returns the parts. The platform never shows the total.
6. **F5** (feed): capability uses the F1 outputs, wage upside uses a benchmark for each domain and level, location uses city and work mode (Remote always fits), recency stays. The diversity penalty stays. Keep `rank_job_feed_for_candidate`.
7. **F6** (talent search, employer): requirement fit, seniority fit (from `level_rank` and years, not from title words), evidence rigor (from skill levels, certifications and awards, **not from CV text length**), and readiness for required certifications. It works on the **shared** profile only. The statutory block for AHPRA/CPA is removed.
8. Awards: a preferred award kind that the talent has gives a small, capped bonus in F1/F6. Certifications: a held preferred certification gives a small, capped bonus; a held required one removes the gap.
9. The platform match: `score = 0.55 × fit + 0.45 × FRS*` stays, but `fit` is **defined in the engine** (a documented function in `01_skill_matching_model.py`, "candidate–job fit") from: skill credit, level fit, experience fit, target-role closeness, domain, location and work mode, work type, certifications and awards. Weights are in the math doc.
10. Differentiation (section 9) is a tuning target. Report the numbers.

## 7. UI contract

Routes: add `#/compare` (both roles) and the employer job overview `#/…/jobs/:id` (name it like the existing employer routes). Left menu: remove "Settings", add "Compare" (both roles). The user block at the bottom opens `#/settings`.

Shared components (built by **FE-Core** first; the others call them):

| File | API |
|---|---|
| `components/pagination.js` | `pagerHtml({ page, pageSize, total })`; `bindPager(root, { onPage(page), onPageSize(size) })`; `loadPageSize(key)` / `savePageSize(key, size)` (key = list name + user id). Shows "Rows per page" (10/20/50), "Showing a–b of n", Previous/Next and numbered buttons (`aria-current="page"`). Hidden when `total` ≤ the smallest size and there is one page |
| `components/sort-select.js` | `sortSelectHtml({ id, value, options:[{value,label}] })`; `bindSort(root, id, onChange)` |
| `components/jd-view.js` | `jdViewHtml(description, { label })` renders the markup of F4 (escape all text; headings `h3`; bullets `ul`) in `section.jd-view[tabindex=0][role=region]` with a maximum height and `overflow-y:auto` |
| `components/premium.js` | `crownIconHtml()`, `premiumChipHtml(text?)`, `lockedBadgeHtml(featureLabel)`; a click on a locked feature opens the "Premium feature" dialog (existing text) |
| `core/compare-store.js` | `compareStore.items(kind)`, `.has(kind,id)`, `.add(kind,item)` (returns false at 5), `.remove`, `.clear`; `kind` = `"job"` or `"talent"`; event `jinder:compare-change`; storage key `jinder.compare.{userId}.{kind}` |
| `components/compare-tray.js` | the basket bar at the bottom of list pages: "Compare (n/5)", "Open compare", "Clear" |
| `components/radar.js` | up to **5** series with 5 line styles (solid, dashed, dotted, dash-dot, long-dash) and 5 colours, defined in CSS classes; a **two-layer mode** (`layers: true`: series 1 "You have" filled, series 2 "Job requires" outline) |
| `icons.svg` | add `i-crown`, `i-lock` |

CSS files (each agent edits only its own; `index.html` links all of them after `styles.css`; FE-Core creates the empty files): `styles-core.css` (FE-Core), `styles-talent.css` (FE-Talent), `styles-employer.css` (FE-Employer), `styles-compare.css` (FE-Compare). Only design-token variables from `styles.css` may be used for colours and spacing.

Locked/gold badge: gold chip "Premium" with the lock icon on Basic; for a Premium user the feature shows normally and a small crown only in the account area.

## 8. Work packages and file ownership

Waves: **1** Taxonomy, BE (infra), FE-Core, CV → **2** Data, Formulas (when Taxonomy is done) → **3** FE-Talent, FE-Employer, FE-Compare (when FE-Core and BE infra are done) → **4** BE integration (when Data, Formulas and CV are done) → **5** QA + Docs.

| Agent | Work | Owns (only these) | Needs |
|---|---|---|---|
| **Taxonomy** | `ict_taxonomy.json` + checker + `README_taxonomy.md` | `jinder_backend_engine/data/reference/ict_taxonomy.json`, `…/validate_taxonomy.py`, `…/README_taxonomy.md` | — |
| **Data** | 50 jobs, 50 talents, validator, README | `jinder_backend_engine/data/synthetic/*` | Taxonomy |
| **Formulas** | section 6 | `jinder_backend_engine/intelligence_engine/*`, `jinder_backend_engine/docs/02*`, `04*`, `run_verification.py`, `jinder_backend_engine/README.md`, `jinder_platform/tests/test_formulas.py`, `jinder_platform/tests/test_differentiation.py` | Taxonomy; Data (for the tuning pass) |
| **CV** | R1: CV and JD parsers, fixtures | `jinder_platform/jinder/cv_parser.py`, `jd_parser.py`, `textextract.py`, `tests/test_cv_*.py`, `tests/test_jd_*.py`, `tests/test_textextract.py`, `tests/fixtures/cv/*` | Taxonomy (names) |
| **BE** | Wave 1: schema v2 + migration F10, store/profile fields, pagination + sort on all lists, compare endpoints (5.2), entitlements benefits and events, job CRUD fields, shared profile fields, tests. Wave 4: reference lists, skills.py, translation.py, seed (loads the new JSON), engine bridge and catalogue on the new formulas, `bridge.path`, demo story, remove the old domains, differentiation checks | all of `jinder_platform/jinder/` **except** the CV agent's files; all of `jinder_platform/tests/` **except** the Formulas and CV files; `run_tests.py`, `config` | Wave 4: Data, Formulas, CV |
| **FE-Core** | shared components, `radar.js`, `icons.svg`, `index.html`, `main.js` routes, `api/index.js` (all new client methods and `api/mock` fallbacks), `config.js`, `shell.js` (menu, user block, crown), `settings.js` (plan area with benefits; sign out), new `data/levels.js` (exports `LEVELS`, `SKILL_LEVELS`, `WORK_MODES`, `PAGE_SIZES`, `COMPARE_MAX`), `charts.js`, `styles-core.css`, a stub `views/compare.js` (FE-Compare replaces it) | those files | — |
| **FE-Talent** | lists (home, search, recommended, bookmarks, applications) with pager + sort; job card and job detail (JD box, level/experience/certs/awards); "Your path" panel (`bridge.js`); onboarding and CV scan fields (R1 UI), skill levels, profile editing | `views/home.js`, `views/jobs.js`, `views/applications.js`, `views/notifications.js`, `components/job-card.js`, `components/bridge.js`, `components/onboarding.js`, `components/profile-card.js`, `components/search-bar.js`, `components/combobox.js`, `data/reference.js` (the pick-lists: domains, roles, fields of study, cities, certifications, award kinds, from the taxonomy), `styles-talent.css` | FE-Core components; BE infra; Taxonomy |
| **FE-Employer** | employer lists with pager + sort; job form (new fields, JD template); **job overview page**; talent cards and detail (level, years, certs, awards, skill levels); compare buttons (basket) and Premium locks | `views/recruiter.js`, `styles-employer.css` | FE-Core components; BE infra |
| **FE-Compare** | `#/compare` page for both roles (talent: jobs; employer: talent), the picker, the radar with 5 series, the tables, the pair matrix | `views/compare.js`, `styles-compare.css` | FE-Core; BE compare endpoints |
| **QA** | run everything, update the browser E2E, check R1–R12 one by one with screenshots, fix small things in test files only, report defects to the owners | `jinder_platform/tests/browser/*`, `run_tests.py` (with BE) | all |
| **Docs** | merge `docs/changes/*.md` into `prompt.md`, `DESIGN.md`, `README.md`, `docs/*`, `START_HERE.md`, `AI_Rule.md` where needed | docs only | all |

## 9. Tests and acceptance

Differentiation tests (`tests/test_differentiation.py`, run on the 50 jobs and 50 talents):
for each talent, over all open jobs the list sorted by `match.score`: the number of distinct 1-decimal scores in the top 20 is ≥ 18 (relaxed from 19 on 2026-10-06: a smooth score with a 40-point range cannot promise 19 for every talent; the formulas reach a mean of 19.5); best minus worst ≥ 30 points;
no radar axis has the same value for all jobs; over the 50 talents, for each job the employer order has no more than 2 exact ties in the top 10.

Other tests (BE and FE owners write them): migration F10; every list with page and sort (page 2, last page, bad sort, `pageSize` clamp); compare 2–5 and 6 (400); Premium gate; the benefits `used` flag; profile new keys (clean, scrub, limits);
shared profile has no private key; no employer response has a score on a person; JD not cut; path object shape; CV fixtures; browser E2E: menu without Settings, crown for Premium, pager, sort, compare basket to page, JD scroll, path radar.

## 10. Open items for the user

* **O1.** The CV file that the scan could not read (to fix the parser against the real layout). The parser is tested on 12+ fixture layouts meanwhile.
* **O2.** The defaults F1 to F12 in section 2: please confirm or change.
