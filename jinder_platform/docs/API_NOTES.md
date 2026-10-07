# API notes

The API follows the contract in `jinder_frontend/prompt.md` (section "API contract"). The frontend (`js/api/http.js`) calls it at `/api`.
This document lists only what the platform **adds** or **decides**. Version 2 changes are in the sections "Lists", "Compare", "Premium benefits" and "Job detail".

## Base address and errors

- Base: `/api` on the same address as the app. `GET /api/health` is public.
- Authentication: `Authorization: Bearer {token}`.
- Error body: `{ "error": { "code", "message", "fields"?, "suggestion"? } }`.

| Status | Code | Added by the platform |
|---|---|---|
| 413 | `TOO_LARGE` | The request is larger than 1 MB (JSON) or 25 MB (upload) |
| 429 | `RATE_LIMITED` | Five failed sign-ins for one address and email, twenty for one address, or thirty for one email (from all addresses), in 15 minutes. The same limit (five) applies to the password check in `POST /me/password` and `POST /me/delete` |
| 503 | `BUSY` | The database is busy. Try again |
| 500 | `INTERNAL` | An unexpected error. The body never has a stack trace |

**The key `missing` (compare only).** The two compare endpoints add a `missing` list next to `error`:
`{ "error": { "code", "message", "fields": { "ids": "..." } }, "missing": [ids] }`.
For an unknown id it is a 404 and `missing` has the unknown ids. For a wrong number of ids it is a 400 and `missing` has the ids above the limit (it is `[]` if there are too few).
A good answer has no `missing`. `error.code` and `error.message` are the same as for any other error. The frontend does not read `missing` yet: the compare page shows the message and a Remove button for each chosen item.

## Lists: page, page size and sort

Every list endpoint takes `page`, `pageSize` and `sort`. The answer has the old list key (`items`) and two new keys:

```json
{ "items": [], "page": { "page": 1, "pageSize": 10, "total": 114, "totalPages": 12 }, "sort": "best" }
```

| Endpoint | List key | `sort` values (the first is the default) |
|---|---|---|
| `GET /jobs/recommended` | `items` | `best`, `newest` |
| `GET /jobs` (`q`, `location`) | `items` (and `total`) | `best`, `newest` |
| `GET /bookmarks` | `items` | `saved` (the job saved last comes first), `best`, `newest` |
| `GET /applications` | `items` | `updated` (the old order), `best` (the skill coverage), `newest` (the date of the application) |
| `GET /recruiter/jobs` | `items` | `newest` |
| `GET /recruiter/jobs/:id/applications` | `items` (and `job`) | `newest` (the date of the application) |
| `GET /recruiter/candidates` | `items` (and `job`, `total`, `limitedTo`, `plan`, `skippedCount`) | `best` (the best fit for the chosen job), `updated` (the profile that changed last comes first) |

Rules:

- `page` starts at 1 (default 1). A bad or too small value gives page 1. A page above the last page gives the last page (`page.page` tells which page it is).
- `pageSize` is 1 to 50 (default 10). A bad value gives 10. The frontend offers 10, 20 and 50 and remembers the choice in the browser.
- A bad `sort` is a 400 error with `fields.sort` ("Use one of these: best, newest."). Nothing is tracked.
- `limit` is removed. The server ignores it. Use `pageSize`.
- The order is stable. Equal values are ordered by `id` (smallest first). `best` is the score, highest first. The date sorts have the newest first.
- An empty list has one empty page: `totalPages` is 1.
- **Basic employer** on `GET /recruiter/candidates`: 5 items, `limitedTo` 5, `page = {page: 1, pageSize: 5, total: <the real total>, totalPages: 1}`. `page` and `pageSize` are ignored. `total` (top level) is the real total too.
- `GET /jobs/recommended` returns every recommended job, page by page. The Home page of a talent asks for `?pageSize=5`.
- The events `job_appear` (talent) and `profile_appear` (employer) are written only for the items of the page that the server returns.
- The list of applications of a talent has no filter for Active and Past. The frontend reads all pages and filters in the browser. The list of applications of a job has no status filter either.

## Compare (2 to 5)

| Endpoint | Who | Rule |
|---|---|---|
| `GET /jobs/compare?ids=a,b,c,d,e` | Talent. Free | 2 to 5 different ids, else 400 with `fields.ids` = "Choose 2 to 5 jobs to compare.". An unknown id is a 404 |
| `GET /recruiter/compare?ids=a,b,c,d,e&jobId=` | Employer. **Premium** | 2 to 5 different ids and one own job (`jobId`). The old form `?a=&b=` is removed (400 for `ids`) |

The maximum is `config.COMPARE_MAX` = 5. `GET /entitlements` shows it as `compareMax`.

**Talent compare.** The answer has `jobs[]` (the job card, `axes` and `salaryMidpoint`), `axes[]`, `pairs[]` (all pairs of jobs: 1, 3, 6 or 10) and `skillMatrix`.
`skillMatrix` has one row for each skill that at least one job asks for, in the order of first appearance: `{ skill, yours, byJob: { <jobId>: { required, must } | null } }`.
`yours` is the level of the talent (1 to 5), or `null` if the talent does not have the skill (a related skill does not count). A job without skill levels gives `{ required: 3, must: true }`.

**Employer compare.** The order of the checks is: sign-in and role, Premium (403 `PREMIUM_REQUIRED`), `ids` (400), `jobId` (400 "Choose one of your jobs."), the job (404 if it is not yours), the profiles (404 "We can't find one of the profiles.").
The answer has:

| Key | Content |
|---|---|
| `job` | `{ id, title, skills }` |
| `candidates[]` | `id, alias, level, years, yearsExperience, roles, qualifications, certifications, awards, coverage, skills[], otherSkills[]` |
| `radar` | `{ axes: [{key, label, formula}], series: [{id, alias, values[]}] }`. Up to 9 axes: Skills for this job (coverage), Requirement fit, Seniority fit, Certification readiness (key `statutory`), Skill depth, Experience, Transferable skills, Level standing, Evidence. An axis stays only if all profiles have a value for it |
| `areas[]` | `{ area, ranks: [{id, position}] }` for up to 8 areas: Skill depth, Experience, Level standing, Evidence, Transferable skills, Certifications, Awards, Qualification level. Position 1 is the highest. Profiles within 3 points of the first profile of a group share its position (90, 89, 70 gives 1, 1, 3). Positions are never added up |
| `skillMatrix[]` | `{ skill, required, must, byCandidate: { <id>: { level, status } } }`. `status` is `meets`, `below`, `related` (`level` is `null`) or `missing` (`level` is `null`) |

There is **no total, no score and no overall ranking of people**. A test scans the answer for these words. The numbers come from Formulas 4 and 6 on the **shared** profile only.
A successful employer compare writes the event `compare_view`.

## Premium benefits (`GET /entitlements`, `PUT /entitlements`)

Version 2 adds three keys:

| Key | Meaning |
|---|---|
| `crown` | `true` when the plan is Premium (the frontend shows the crown and the gold ring) |
| `compareMax` | 5, for both roles |
| `benefits` | `[{ key, label, description, available, used, usedCount }]` |

`available` is true when the plan allows the benefit (Premium). `used` is true when the user did it at least once. `usedCount` is the number of times. The counts come from the table `events` where the user is the actor.
A user who goes back to Basic keeps `used` and `usedCount`. `available` becomes false. `canCompare` stays employer-only (a talent compares jobs for free).

| Role | Benefit key | Label | Event type |
|---|---|---|---|
| Employer | `all_talent` | See every talent profile, not only the top 5 | `talent_list_full` |
| Employer | `invite` | Invite talent to apply | `invite` |
| Employer | `compare` | Compare up to 5 talent profiles | `compare_view` |
| Employer | `advanced_charts` | Pipeline by stage and interest per job | `advanced_charts_view` |
| Talent | `skills_to_learn` | Skills to learn next | `insights_view` |
| Talent | `skill_demand` | Demand for your skills | `insights_view` |

A user sees only their own counts. No answer has the id or the alias of the other side next to these events.

## New optional fields (the real API sends them; the mock sends only some of them; the screens hide them when they are missing)

| Where | Field | Meaning |
|---|---|---|
| `GET /jobs/:id` | `bridge` | The talent's path to this job (Formulas 1, 2 and 5). Only for the signed-in talent with a profile. See `FORMULAS_IN_THE_PRODUCT.md` |
| `bridge` of `GET /jobs/:id` | `axes`, `score` | The 8 radar values of the job for this talent ("How this job fits you") and the Fit score |
| `bridge` of `GET /jobs/:id` | `path` | **New.** "Your path to this job": `axes[]` (`key, label, group, required, have, status`), `fit[]`, `gaps[]` and `summary` (`fitCount, gapCount, monthsToClose, readinessTier`). Plain JSON from Formula 2 |
| `bridge` of `GET /jobs/:id` | `projection` | **Removed.** There is no 12-month chart |
| `similar[]` in `GET /jobs/:id` | `similarity` | `{ index, tier, salaryChange }` from Formula 3 |
| `match` of a job | `score` | The Fit score with one decimal (0 to 100): `0.55 x fit + 0.45 x FRS*` |
| `match.skills[]` | `fitStatus`, `required`, `level`, `must` | `fitStatus` is `meets`, `below`, `related` or `missing`. `status` stays `match`, `partial` or `gap` (meets = match, below and related = partial, missing = gap). `required` and `level` are the levels (1 to 5) of the job and of the person. `level` is `null` if the person does not have the skill |
| every job | `level`, `specialisation`, `minYears`, `maxYears`, `workMode`, `skillRequirements`, `certifications`, `awards`, `educationMin`, `salaryUnit` | The job facts. A job without a value has `null`, `[]`, `{required: [], preferred: []}` or `{preferred: []}`. The API never invents a value |
| `GET /recruiter/candidates`, `/recruiter/candidates/:id` | `level`, `yearsExperience`, `certifications`, `awards`, `skillLevels`, `updatedAt` | The employer-safe profile has these keys. No score on a person |

## Job description and pay

- `description` is stored as sent, with its line breaks and the markup `## Heading` and `- bullet`. It is never cut. The limit is 10,000 characters. A longer text is a 400 (`fields.description`).
  `summary` is the first whole sentences that fit in 200 characters (it ends with "…" only if the first sentence alone is longer). The job card has `summary`. `GET /jobs/:id` and `GET /recruiter/jobs/:id` have the full `description`.
- `salaryUnit` is `year`, `day` or `hour`. `salaryMin` and `salaryMax` stay private. `salary` is the text, for example `$900 per day` or `$150,000 – $170,000 per year`.
  The platform never changes a day or hour rate to a yearly pay. The formula engine does it (`annual_salary`: day x 220, hour x 1950).
- An employer job gets its numbers and unit from the salary text: "per day", "a day", "daily" or "day rate" gives `day`; "per hour", "an hour" or "hourly" gives `hour`; else `year`. A text with no amount ("Market competitive") gives no numbers.
- `POST /recruiter/jobs` and `PATCH /recruiter/jobs/:id` accept the new job keys. The old short body still works (a new job without `level` gets `"Mid"`). The checks are in `jinder_frontend/prompt.md`.
  `skillRequirements` is `[{name, level 1 to 5, must}]` (1 to 12 skills). If it has items, the job skills come from it. `certifications` is `{required: [name], preferred: [name]}` (up to 10 in each list). `awards` is `{preferred: [kind]}` (kinds of the taxonomy).
- `POST /recruiter/jobs/suggest-skills` keeps `skills` (names) and adds `skillRequirements` (`[{name, level: 3, must: true}]`). It also reads `category` (a domain) from the body.
- A posted job gets its ANZSCO code and occupation from the taxonomy (the longest role of the role list found in the title, else the occupation of the specialisation). The codes are a demo mapping.

## The talent profile and the shared profile

- `PATCH /me` accepts the new profile keys: `level`, `yearsExperience` (0 to 40, one decimal; the band `years` is set from it), `certifications` (up to 20 of `{name, issuer, year}`), `awards` (up to 20 of `{name, kind, year}`),
  `specialisation`, `workModes`, and `translation[].level` (1 to 5) and `translation[].years`. The server cleans all of them. Text goes through `scrub_contact` (no email, no phone).
- `industry` and `targetIndustries` hold **domains**: Software Engineering, AI & Machine Learning, Data. Any other value is dropped when the profile is saved.
- `GET /me/shared-profile` and the employer views (`store.shared_profile`) add `level`, `yearsExperience` (rounded to 0.5), `skillLevels` (`[{name, level, years}]`), `certifications`, `awards`, `specialisation`, `workModes` and `updatedAt`.
  A skill with no level of its own gets the level of its evidence (Strong 4, Moderate 3, Limited 2). The shared profile still has no name, email, country, CV, evidence line or employer name.
  **Certification and award names and years are shared with an employer at once** (decision D5). The talent is warned in the app not to write a name or contact details there.

## The CV result (`GET /cv/parse/:id`, key `result`)

All old keys stay (`fields`, `detected`, `missing`, `evidence`, `sampleLabel`). New keys:

| Key | Meaning |
|---|---|
| `currentRole`, `targetRole`, `level` | Plain text. `""` when the CV does not show it |
| `yearsExperience` | A number 0 to 40, or `null` |
| `certifications`, `awards` | The same lists as in `fields` (`[]` when none) |
| `skills` | `[{name, level}]`. `level` is 1 to 5, or `null` when the CV gives no evidence. `fields.skills` stays a list of names |
| `found` | `{ currentRole, targetRole, level, yearsExperience, certifications, awards }`, booleans. The UI uses them for the "Not found" hints |
| `sources` | How each value was found (the name of the rule). For tests and hints |
| `domain` | The first domain of `fields.industry` (one of the 3), or `""` |

`fields` has the profile keys that the CV shows: the old keys plus `targetRole` (a list), `level`, `yearsExperience`, `certifications`, `awards`. `fields.industry` holds domains only (at most 2, the strongest first, and no key when nothing fits).
The new keys are never in `missing`: use `found`. A field that the CV does not show is empty (`""`, `[]`, `null`). The reader does not guess.

## Decisions that the contract leaves open

- **Upload.** `POST /cv` and `POST /recruiter/jobs/import` read the file type from the first bytes. A PDF with a `.docx` name is rejected with "Use a PDF or DOCX file.". The file is read in the background. The client polls `GET /cv/parse/:id` or `GET /recruiter/jobs/import/:id`.
- **A new CV** replaces the old one. The old file is deleted. `PATCH /me { "cv": null }` deletes the CV file.
- **A job description file** is deleted after it is read. Nothing is posted until `POST /recruiter/jobs`. The reader also gives `level`, `minYears`, `maxYears`, `workMode`, `skillRequirements`, `certifications`, `awards`, `educationMin`, `specialisation` and `domain` when the text shows them.
- **Posted jobs** get an ANZSCO code and an occupation from the taxonomy, so that the formulas can compare them.
- **Dates.** The slot times and the close date are stored in UTC. The notification for a confirmed interview time shows the time in UTC.
- **Plan switch.** `PUT /entitlements` works when `JINDER_ALLOW_PLAN_SWITCH` is `1`. If the variable is not set, it works only when the server listens on this computer (`127.0.0.1`). Otherwise it returns 403.
- **Email.** An event with `email: true` writes a row in `email_outbox`. Without SMTP settings the row gets the status `recorded` and nothing is sent.
- **Sample jobs** have no employer. A talent can apply, but no employer account moves the application. The 4 jobs of the demo employer use the full flow.
- **Premium insights of the talent** (`GET /stats`, `advanced`) are level-aware, from the skills of the 20 best jobs. `gapRanking[]` is `{ skill, count, needLevel, yourLevel, missing, below }` and `demandForYourSkills[]` is `{ skill, count, needLevel, yourLevel }`.
  `needLevel` is the mean level that the jobs ask for (one decimal). `yourLevel` is the level of the talent (`null` for a missing skill).

## Run the checks yourself

```
python run_tests.py                 # unit and API tests (729 tests, about 75 seconds)
python run_tests.py --formulas      # also the self-checks of the six formula files
python run_tests.py --browser       # also all browser tests (7 stages, about 12 minutes; Chrome or Edge)
python run_tests.py --browser-quick # also only the two journeys in a real browser (about 2 minutes)
```

The files `tests/browser/check_fe_core.py`, `check_fe_talent.py`, `check_fe_employer.py`, `check_fe_compare.py` and `check_mock_ict.py` are browser checks for each part of the frontend and for the mock. Each one starts its own platform (ports 8120, 8130, 8140, 8150 and 8170).
The scripts `qa_acceptance.py`, `qa_a11y.py`, `qa_perf.py` and `qa_xss.py` are the QA scripts (see `README.md`).

## Your data

| Endpoint | Purpose |
|---|---|
| `GET /me/export` | A JSON copy of the data of the signed-in user (account, profile, applications, alerts). No password hash. An employer's copy has the anonymous employer view of applications |
| `POST /me/delete` `{ "password" }` | Delete the account. The CV file, the profile, the sessions, the applications and the alerts go with it. For an employer: the posted jobs and their applications go too |

The Settings screen has the buttons "Download my data" and "Delete my account" (real backend only).
