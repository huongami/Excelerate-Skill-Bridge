# MockICT: the browser-only mock backend is ICT only

Owner: the MOCK-ICT agent. This file is for the Docs agent (merge into `prompt.md`, `AI_Rule.md`, `README.md`) and for the QA agent.
The plan is `docs/V2_PLAN.md` (decision D2). The mock is the backend that runs in the browser with `?mock=1`. All paths are in `jinder_frontend/app/js/`.
Text is written in simple English.

## 1. What changed

The mock had the old catalogue (a CSV file with 8 old categories), old demo data (Harbour Logistics, a nurse, an accountant ...) and an old translation library.
All of this is now ICT only: **Software Engineering, AI & Machine Learning and Data**. The names come from `jinder_backend_engine/data/reference/ict_taxonomy.json`.

| File | Change |
|---|---|
| `api/mock/seed-jobs.js` | New content. 24 jobs, copied from `jinder_backend_engine/data/synthetic/jobs.json` (see section 2). |
| `api/mock/jobs.js` | Rewritten. No CSV and no `fetch`. Embedded catalogue, a skill table of the taxonomy, new role closeness and level rules (section 3). |
| `api/mock/translation.js` | Rewritten. 33 role pairs and 37 skill pairs, all ICT (section 4). |
| `api/mock/seed-demo.js` | Rewritten. The story of the real seed, in a smaller form (section 5). |
| `api/mock/cv-samples.js` | Rewritten. 5 ICT CV samples. New function `parseResultOf` (section 6). |
| `api/mock/jd-samples.js` | Rewritten. 4 ICT job description samples (section 7). |
| `api/mock/routes-account.js` | The CV parse answer comes from `parseResultOf`. `translateKeeping` keeps the skill level and the years that the talent set. `GET /me/shared-profile` adds the V2 facts (section 8). |
| `api/mock/core.js` | `sharedProfileOf`: the shared `skills` list has the skill cards only (a role card is a role, not a skill). |
| `api/mock/db.js` | The storage key is now `jinder.mock.db.v2`. The old key `jinder.mock.db.v1` is removed at start, so a browser with the old non-ICT demo data starts clean. |
| `config.js` | One label: "Employer demo (Bluebushworks)". |
| `tests/browser/check_mock_ict.py` | New browser check (section 9). |
| `tests/test_mock_ict.py` | New unit test that scans the mock files (section 9). |

Not changed: `adapter.js`, `aliases.js`, `routes-jobs.js`, `routes-applications.js`, `routes-recruiter.js`, `routes-platform.js`. They had no old words.
The API client (`api/index.js`) is not changed. Pages, sort and the compare errors still work through its fallback.

## 2. The catalogue (`seed-jobs.js`, `jobs.js`)

* 24 jobs: Data 9, Software Engineering 9, AI & Machine Learning 6. Levels: Intern 2, Junior 4, Mid 11, Senior 3, Lead 3, Principal 1.
  Cities: Sydney 8, Remote 6, Melbourne 4, Brisbane 2, Perth 2, Canberra 1, Adelaide 1. Types: Full-time 18, Contract 4 (day rate), Graduate / Internship 2.
  21 jobs list certifications and 9 list preferred awards.
* Each job has the full description with the JD markup (`## Heading`, `- bullet`). It is never cut and never flattened. `summary` is the first whole sentences, 200 characters at most.
* The job ids are `job-<key>`, as in the real backend (for example `job-data-eng-senior-02`). The demo jobs are `job-demo-data-engineer-mid` and so on.
* `postedDaysAgo` and `closesInDays` count from the day when the app starts, so every catalogue job is open.
* The text is the same as in the synthetic file. Two small edits were made, so that no word of an old field of work stays in the files:
  the word "warehouse" got the word "data" before it ("cloud data warehouse"), and in the talent and demo texts "retail", "finance" and "marketing" became "shop", "billing" and "campaign".
  The alias "chef infra" of the skill Ansible is left out of the skill table for the same reason.
* Job fields for the old screens stay: `id, title, company, category, location, area, type, anzsco, occupation, salary, postedAt, closesAt, summary, description, skills`.
  `category` is one of the 3 domains. New optional fields (as in the real backend): `specialisation, level, minYears, maxYears, workMode, educationMin, salaryUnit, skillRequirements [{name, level, must}], certifications {required, preferred}, awards {preferred}`.
* `jobs.js` exports the same functions as before (`loadJobs, catalogue, isOpen, findJob, jobSource, suggestSkills, namesFromProfile, namesFromList, skillMatch, recommend, searchJobs, jobDetail`).
  It adds `skillsIn`, `canonicalSkillName` and `salaryText`. `loadJobs()` only returns a resolved promise.

## 3. Skills and matching (`jobs.js`)

* `SKILL_TABLE` has the 172 skills of the taxonomy: name, aliases and related skills. The patterns are built from it when the file loads.
* Word-safe rules (as in the real backend): `C#`, `C++`, `.NET`, `Node.js`, `CI/CD` are found as whole words. `R`, `C` and `Go` count only inside a list ("Python, R, SQL"). `Swift`, `Rust`, `Ruby` and `Spark` count only with a capital letter.
  A word inside another word never counts ("java" is not in "javascript", "js" is not in "node.js"). A short alias ("js", "ml", "k8s") counts only when it is the whole text of a skill.
* `RELATED` is a map of the related skills of the taxonomy (both ways). A related skill gives "partial", as before.
* `CATEGORY_MAP` has the 3 domains only.
* The rank (never shown as a number) is: skill coverage x 0.4, plus the target role (up to 30) or the past role (up to 18), plus domain 15, location 10 (a Remote job always fits), work type 5, and level (same level 8, one step 4).
  A job is recommended when the rank is 45 or more and the level is not 2 or more steps away. The role closeness uses the role phrase of the title ("Senior Data Engineer, Lakehouse" is "data engineer") and the ANZSCO occupation of the job.
* The demo talent gets 7 recommended jobs. Each of the 5 CV samples gets 3 to 8.

## 4. Translation (`translation.js`)

* A simpler copy of `jinder_platform/jinder/translation.py`. It does not copy the whole file.
* A role card: `mapped` is a title of the role list (53 titles of the taxonomy). `anzsco` and `occupation` come from the taxonomy tables in the file. `kind` is `cross-border`, `cross-industry` or `direct`.
  A title is read without level words, company and place in brackets. Two titles that give the same role make one card ("BI Specialist; MIS Executive").
  A title that is not an ICT title (Registered Nurse, Accountant, Chef, Marketing Manager, Teacher, Mechanical Engineer) gives **no** role card.
* A skill card: the name or alias of the taxonomy first ("spreadsheets" gives "Microsoft Excel"), then a pair ("Informatica", "Qlik", "ER diagrams"), then the name as it is. New keys `level` (1 to 5) and `years`.
  A level that the talent gave stays. Without a level, the evidence gives it (Strong 4, Moderate 3, Limited 2: rule F8).
* Qualifications keep the AQF rules. A role card no longer adds a skill.

## 5. Demo data (`seed-demo.js`)

* **10 sample talents** with ICT profiles, aliases from `talents.json`: Jade Koala, Plum Heron, Amber Finch, Cyan Puffin, Lime Kestrel, Coral Fox, Mint Fox, Cyan Falcon, Sage Lynx, Slate Seal.
  Each has level, exact years, domain, skills with level and years, certifications, awards, locations, work modes and private evidence lines.
* **Talent demo** Teal Heron (Linh Nguyen, `candidate@demo.jinder.app`): a Mid data analyst who studied in Vietnam and wants to be a Data Engineer. 8 skills with levels (SQL 4, Python 3, Power BI 4, spreadsheets 4, Data analysis 4, dashboards 3, Informatica 2, ER diagrams 3), one certification (Microsoft Certified: Power BI Data Analyst Associate, 2024), one award (Smart City Hackathon Runner-up, 2023).
  Her two titles are one cross-border Data Analyst card (ANZSCO 224114). She is in interview for the Data Engineer job and has the alert with 3 interview times.
* **Employer demo** Alex Morgan, Bluebushworks (`recruiter@demo.jinder.app`), with the 4 jobs of `demo.json`: Data Engineer, Solar Analytics (open); Senior Backend Engineer, Installer Platform (open); Machine Learning Engineer, Solar Forecasting (closes in 4 days); Contract Data Engineer, Billing Migration (closed 2 days ago, day rate).
  The applications: Data Engineer (Jade Koala in review, Teal Heron in interview, Plum Heron applied with a note), Backend (Amber Finch applied, Cyan Puffin in review), Machine Learning (Lime Kestrel applied), closed contract (Coral Fox confirmed, offer sent, name shared).
  The employer has 3 alerts. The jobs have activity events (the same numbers at each start) for the charts of Premium.
* The demo jobs keep the new fields (level, years, work mode, skill levels, certifications, awards) for the job pages of talent only. The employer screens of the mock keep the old fields (plan F9).
* The password of both demo accounts is `demo1234`. The sample talents cannot sign in.

## 6. CV samples (`cv-samples.js`)

* 5 samples: data analyst (BI Specialist, Vietnam; this is the default and the CV of the demo talent), software developer (Java, India), machine learning researcher (Germany), business analyst (Philippines), systems administrator (Brazil).
* The file name chooses the sample: "fail" or "corrupt" fails the read; "ml", "machine", "research", "scientist" or "ai" gives the machine learning CV; "software", "developer", "backend", "java" or "swe" gives the software CV;
  "devops", "admin", "infra", "cloud" or "platform" gives the systems administrator CV; "data" gives the data analyst CV; "analyst" or "business" gives the business analyst CV; any other name gives the data analyst CV.
* Each sample has a current role, a level, exact years, certifications, awards, a desired role, skills with levels and evidence lines. Some fields are left out on purpose:
  the machine learning CV has no desired role and no certification (plan F11), the business analyst CV has no years, no certification and no award.
* `parseResultOf(sample)` makes the answer of `GET /cv/parse/:id`: `fields`, `detected`, `missing`, `evidence`, `sampleLabel`, and the V2 keys `domain`, `skills [{name, level}]` and `found {currentRole, targetRole, level, yearsExperience, certifications, awards}`.
  The onboarding already reads these keys, so it shows "What we found in your CV" and the "not found" hints in the mock too.

## 7. JD samples (`jd-samples.js`)

4 samples with the JD markup: Backend Engineer (Sydney), Data Analyst (contract, no location), Machine Learning Engineer (no salary), DevOps Engineer (Remote).
The file name chooses one ("fail" fails; "ml", "machine" or "ai": machine learning; "devops", "cloud", "platform", "infra" or "sre": DevOps; "data", "analyst" or "bi": data; any other name: backend).
The domain, the city and the work type are values of the pick-lists, so the form shows no "Missing" mark for a domain.

## 8. Other edits in the mock

* `GET /cv/parse/:id` gives the answer of section 6.
* `POST /profile/translate` keeps the `level` and `years` that the talent set (as the real backend does).
* `GET /me/shared-profile` (the talent's own "What employers see") adds `level`, `yearsExperience` (rounded to 0.5), `specialisation`, `skillLevels`, `certifications` and `awards`.
  The applications and the talent cards that an employer reads in the mock do **not** have these keys (the old shape stays).
* The browser storage key is `jinder.mock.db.v2` (see section 1).

## 9. Tests

* `tests/browser/check_mock_ict.py`: **81 checks, all passed.** Run `python tests/browser/check_mock_ict.py [--shots <folder>] [--app-dir <folder>]`.
  It starts the platform on port 8170 with a temporary data folder, and Chrome on port 9370. It imports the real mock files in the page and tests the data (24 jobs, taxonomy names, descriptions, word-safe skills, translation, samples), then drives the screens:
  a new talent signs up and goes through the onboarding with a mock CV, sees 5 recommended jobs, the job list (27 open jobs), a job detail with the JD box, a bookmark, an application;
  the demo talent; the demo employer (4 jobs, the overview, a job from a file sample, a failing file, a new job, the talent list, Premium, privacy of the answers). Every screen is also checked for words of an old field of work.
  It checks that there is no console error, no CSP error and no request for a CSV file.
* `tests/test_mock_ict.py`: 17 tests. The mock files have no old word; the embedded jobs, the skill table, the translation tables, the demo data and the samples use the names of the taxonomy; no control character; the other files of the app do not get more old words (the numbers are fixed in the test).
* `python run_tests.py`: **717 tests, OK** (about 88 seconds).

## 10. What the mock still does not do

* No compare (talent jobs or employer talent), no skill-gap path (`bridge.path`), no Premium `benefits` list. The client fails with `NEEDS_REAL_BACKEND` (plan F9).
* The employer screens keep the old fields. The employer form has no level, years, work mode, certifications or awards, and the talent cards and the review page of an employer have no level, years, certifications, awards or skill levels.
* The mock has no formula engine. The "fit" is the simple rank of section 3, and no number is shown. Pages and sort are done by the client (`api/index.js`), not by the mock.
* The mock reads no real file. A CV or a job file gives one of the samples by its name.
* The talent search matches words in the title, company, occupation, domain, specialisation, level, skills and area. It has no ranking of the words.
* Data is stored in the browser (`localStorage`), with a weak demo hash. It is for demos only (AI_Rule Rule 6).

## 11. For QA, the Docs agent and the lead

**Browser checks of other agents that now fail by design (3 assertions).** The new mock has the new job fields and ICT samples. Update these assertions (the files are not mine):

| File and check | Why it fails | New expectation |
|---|---|---|
| `check_fe_talent.py`, "mock: the Home widget shows 5 cards ... and no chip row" | The mock cards have the chips Level, Experience and Work mode | `facts == 5` (one chip row on each card) |
| `check_fe_talent.py`, "mock: the job detail has the description box ... the facts of the old data" | The detail facts are now `Level, Experience, Work mode, Place, Type, Salary, Education` | the new list of facts |
| `check_fe_employer.py`, "mock import: the sample fills the form ..." | The file name `nurse-aged-care.pdf` now gives the default sample (Backend Engineer, domain Software Engineering). No sample has a domain that is not in the list | use a file name such as `backend-engineer.pdf`; the title is "Backend Engineer, Payments API" and the domain marker is "From your file" |

The other mock checks pass: `check_fe_core.py` mock part 16 of 16 (run alone), `check_fe_talent.py` mock part 10 of 12 (the two above), `check_fe_employer.py` 204 of 205 (the one above).
`check_fe_core.py` as a whole stops before its mock part, in the real-backend talent part (`check_tray`, "compare-tray-title" is null). This is not caused by the mock files.

**Docs agent.** Sync `prompt.md` from these files: `seed-jobs.js`, `jobs.js`, `translation.js`, `seed-demo.js`, `cv-samples.js`, `jd-samples.js`, `db.js`, `core.js`, `routes-account.js`. Change the text about the mock:
the 24 embedded jobs (no CSV, no `MOCK_JOBS_CSV_URL`), the storage key `jinder.mock.db.v2`, the demo data of section 5. `AI_Rule.md` Rule 2 (last bullet) says that the mock keeps non-ICT sample data. That is no longer true.

**Not mine, found by the scan** (a test fixes the numbers, so that they do not grow):

* `views/landing.js` lines 38, 44 and 49: the picture of the landing page shows a "Marketing Executive" role and "Trade marketing exec".
* `components/onboarding.js` line 623: the placeholder "Search or type, e.g. Marketing" for the field of study.
* `config.js` lines 14 and 15: the comment and the key `MOCK_JOBS_CSV_URL` (`data/australian_jobs_dataset.csv`) are not used any more. `app/serve.ps1` still serves that file.
* `prompt.md` and its embedded copies: the old mock text.

**Real backend, not mine.** `jinder/translation.py`: the last pair (`software (engineer|developer)|developer|engineer`) gives the card "Software Engineer" to any title that ends with "Engineer", for example "Civil Engineer" and "Mechanical Engineer".
The plan says that a title that is not an ICT title gives no role card. The mock does not do this. Suggested fix: use the same stricter test as `translation.js` (a bare "Engineer" or "Developer", or a title that starts with "Software").

**Run list.** Add `check_mock_ict.py` to `FRONT_END_CHECKS` in `run_tests.py` (BE and QA own that file). It takes about 50 seconds.
