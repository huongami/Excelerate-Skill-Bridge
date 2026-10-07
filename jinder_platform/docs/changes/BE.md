# Changes of the BE agent, wave 1 (infrastructure)

This file lists every new or changed field, endpoint, event and column. The Docs agent merges it into `DATABASE.md`, `API_NOTES.md` and `README.md`.
The plan is `docs/V2_PLAN.md`. This file uses simple English.

What is NOT in wave 1: the new seed data, `skills.py`, `translation.py`, the pick-lists from the taxonomy, the new formulas, `bridge.path`.
The old catalogue stays. Its new fields are empty.

## 1. Database (version 2)

The version is the row `schema_version` = `2` in the table `schema_info`. (Version 1 used the row `version`.)

### New columns

| Table | Column | Type | Meaning |
|---|---|---|---|
| `profiles` | `level` | text, `''` or one of Intern, Junior, Mid, Senior, Lead, Principal | The current level of the talent |
| `profiles` | `years_exact` | real 0 to 40, or NULL | Exact years of experience. The column `years` (the band) is set from it |
| `profiles` | `certifications` | JSON text | `[{name, issuer, year}]` |
| `profiles` | `awards` | JSON text | `[{name, kind, year}]` |
| `translated_skills` | `level` | integer 1 to 5, or NULL | The level of one skill. Only rows of `source = 'skill'` have it |
| `jobs` | `level` | text or NULL | The level that the job asks for (same list as above) |
| `jobs` | `specialisation` | text or NULL | |
| `jobs` | `min_years`, `max_years` | real 0 to 40, or NULL | The experience that the job asks for |
| `jobs` | `work_mode` | text or NULL | Onsite, Hybrid or Remote |
| `jobs` | `education_min` | text or NULL | For example "Bachelor's degree" |
| `jobs` | `certs_required`, `certs_preferred` | JSON text, default `[]` | Lists of names |
| `jobs` | `awards_preferred` | JSON text, default `[]` | A list of award kinds |
| `job_skills` | `level` | integer 1 to 5, or NULL | The level of the skill that the job asks for |
| `job_skills` | `must` | integer, default 1 | 1 = required. 0 = nice to have |

The database has CHECK rules for `level`, `work_mode`, the skill levels and the years. A new index `ix_events_actor` (`actor_id`, `type`) serves the Premium benefits.

### What happens at start-up (F10)

1. The server reads the schema version of the file `var/jinder.db`. A missing, empty or table-less file is a new database.
2. If the version is lower than 2 (version 1, or a file with tables but no version row), the server does NOT change the file.
3. The server renames the file to `jinder.db.v1.bak`. If that name exists, it uses `jinder.db.v1.2.bak`, then `jinder.db.v1.3.bak`, and so on.
4. The folder of uploaded CV files (`var/uploads`) goes with it, if it has files. It gets the same suffix (`uploads.v1.bak`). Without this step, the clean-up of unused uploads would delete the old CV files at the first start.
5. The server writes the pending changes of the WAL file into the main file before the rename, so that the backup is complete.
6. A new database is made and filled with the sample data. The server writes a warning in the log and a line in the start-up text ("Old data ... Nothing was deleted").
7. If the rename fails (for example, another program has the file open), the start stops with a message. Nothing is lost.
8. A database with version 2 or higher is not moved.

To go back: stop the server, delete the new `jinder.db` (and `-wal`, `-shm`), rename the backup (and the uploads folder) to the old names.

Code: `db.init_db(path, upload_dir)` returns the path of the backup or `None`. `db.stored_version(path)` reads the version. `app.prepare()` returns it as `info["migrated"]`.

## 2. Talent profile

`PATCH /me` and `GET /me` (key `profile`) have these new keys. The server cleans all of them. The text goes through `scrub_contact` (no email, no phone).

| Key | Rule |
|---|---|
| `level` | One of Intern, Junior, Mid, Senior, Lead, Principal. Any other value becomes `""` |
| `yearsExperience` | A number from 0 to 40, one decimal (6.57 becomes 6.6). Any other value (text, a boolean, 41, -1) becomes `null`. The value `years` (the band) is then set from the number: under 1 "Less than 1 year", under 3 "1–2 years", under 6 "3–5 years", up to 10 "6–10 years", above 10 "More than 10 years". If `yearsExperience` is `null`, the band that the client sent stays |
| `certifications` | A list of `{name, issuer, year}`. At most 20. `name` is required (up to 120 characters). `issuer` is up to 120 characters or `""`. `year` is a whole number from 1990 to next year, or `null`. A bare text counts as a name. A copy is dropped |
| `awards` | A list of `{name, kind, year}`. At most 20. `kind` is free text of up to 40 characters for now (wave 4 checks it against the taxonomy list). The other rules are the same |
| `translation[].level` | A whole number 1 to 5, or `null`. Text ("4"), 2.5, 0, 6 and booleans become `null`. A row of a role or a qualification always has `null` |

`POST /profile/translate` keeps the `level` of a skill when the engine runs again. A new card has `level: null`.

### The shared profile (what an employer sees)

`store.shared_profile(alias, profile, updated_at)` adds these keys. It still has no name, email, country, CV, evidence line or employer name.

| Key | Meaning |
|---|---|
| `level` | The level, or `null` |
| `yearsExperience` | The exact years rounded to 0.5 (6.6 gives 6.5), or `null` |
| `skillLevels` | `[{name, level}]` for each name in `skills`, in the same order. A skill with no level of its own gets the level of its evidence (Strong 4, Moderate 3, Limited 2). This is rule F8 |
| `certifications` | `[{name, issuer, year}]` |
| `awards` | `[{name, kind, year}]` |
| `updatedAt` | The time of the last save of the profile |

`store.candidate_pool()` items also carry `updated_at`. An application snapshot has the new keys for new applications only.

## 3. Jobs

### Keys that every job has (card, detail, employer list, employer detail, compare)

`level`, `specialisation`, `minYears`, `maxYears`, `workMode`, `skillRequirements`, `certifications`, `awards`, `educationMin`.

For a job without a value the API sends: `null` for `level`, `specialisation`, `minYears`, `maxYears`, `workMode`, `educationMin`; `[]` for `skillRequirements`; `{required: [], preferred: []}` for `certifications`; `{preferred: []}` for `awards`. This is the case for every job of the old catalogue. The API never invents a value.
`skills` (the names) stays. `summary` stays.

Use `catalogue.requirements_of(job)` when you need levels: it gives `skillRequirements` when the job has them, else the skills with level 3 and `must = true`.

### Employer: `POST /recruiter/jobs`, `PATCH /recruiter/jobs/:id`

The old short body still works. The new keys are optional.

| Key | Rule (error field when it is wrong) |
|---|---|
| `level` | One of the six levels (`level`). A new job without it gets `"Mid"`. On `PATCH`, a missing or `null` level is "no change" |
| `specialisation`, `educationMin` | Text up to 80 characters, scrubbed. `null` or `""` clears it |
| `minYears`, `maxYears` | A number 0 to 40 with one decimal, or `null` (`minYears`, `maxYears`). `minYears` must not be more than `maxYears` (error on `maxYears`). On `PATCH`, the stored value is used when you send only one of them |
| `workMode` | Onsite, Hybrid or Remote, or `null` (`workMode`) |
| `skillRequirements` | `[{name, level, must}]`. `level` is a whole number 1 to 5 (missing = 3). `must` is a boolean (missing = true). 1 to 12 skills. A copy of a name is dropped. If it has items, the job skills (`skills`) come from it and a `skills` key in the body is ignored. Without it, the job has the names from `skills` and no levels |
| `certifications` | `{required: [name], preferred: [name]}`. Up to 10 names in each list, up to 120 characters each, scrubbed. A bigger list is an error (`certifications`). Send both lists: the value replaces the old one |
| `awards` | `{preferred: [award kind]}`. Up to 10 kinds, up to 40 characters each, scrubbed (`awards`) |

On `PATCH`:
- `skillRequirements` with items replaces the skills with their levels.
- `skills` alone replaces the skills and clears the levels.
- `skillRequirements: []` keeps the skills and clears the levels.

The responses of `POST`, `PATCH`, `GET /recruiter/jobs` and `GET /recruiter/jobs/:id` all have the new keys. `GET /recruiter/jobs/:id` and `PATCH` also have `description`, `summary` and `company`.

### The description is never cut

- `description` is stored as sent. Only control characters and the space at both ends are removed. `\r\n` becomes `\n`, so that the `## Heading` and `- ` markup works.
- The limit is 10000 characters (`catalogue.MAX_DESCRIPTION`). A longer text is refused with a message (400, field `description`). It is never cut. The old limit of 6000 characters, which cut the text without a message, is gone.
- `summary` is a short text of at most 200 characters (the "…" mark counts). Headings and bullet marks are left out of it.
- The job card does not carry the description (as before). `GET /jobs/:id` and `GET /recruiter/jobs/:id` carry all of it.

### Job description file (`POST /recruiter/jobs/import`)

`parse_jd` is called as before. The new keys in its `fields` go through the same checks as the form. A value that is not valid is left out. `detected` lists the new keys that stay. If `skillRequirements` is there and `skills` is not, `skills` is made from it.

## 4. Lists: page and sort

All these lists take `page` (from 1, default 1), `pageSize` (1 to 50, default 10) and `sort`. They answer with the old list key plus `page` and `sort`:

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
| `GET /recruiter/candidates` | `items` (and `job`, `total`, `limitedTo`, `plan`, `skippedCount`) | `best`, `updated` (the profile that changed last comes first) |

Rules:
- `limit` is removed. The server ignores it. Use `pageSize`.
- A bad `sort` is a 400 error with `fields.sort` ("Use one of these: best, newest."). Nothing is tracked.
- A bad or too small `page` gives page 1. A page above the last page gives the last page (`page.page` tells which page it is).
- `pageSize` is set to the range 1 to 50. A bad value gives 10.
- The order is stable. Equal values are ordered by `id` (smallest first). `best` is the score, highest first. The date sorts have the newest first.
- An empty list has one empty page: `totalPages` is 1.
- **Basic employer** on `GET /recruiter/candidates`: 5 items, `limitedTo` 5, `page = {page: 1, pageSize: 5, total: <the real total>, totalPages: 1}`. `page` and `pageSize` are ignored. `total` (top level) is the real total too.
- Events: `job_appear` (talent) and `profile_appear` (employer) are written only for the items of the page that the server returns.
- `GET /recruiter/jobs/:id/applications` was in the order "last change first". It is now "newest application first" (`createdAt`).
- `GET /jobs/recommended` used to return the 5 best jobs. It now returns every recommended job, page by page. The home page of a talent asks for `?pageSize=5`.

## 5. Compare (2 to 5)

### Talent: `GET /jobs/compare?ids=a,b,c,d,e` (free)

- 2 to 5 different ids. Otherwise 400 with `fields.ids` = "Choose 2 to 5 jobs to compare.". An unknown id is a 404.
- `jobs[]` (job card + `axes` + `salaryMidpoint`), `axes[]`, `pairs[]` (all pairs: 1, 3, 6 or 10) and the new `skillMatrix`.
- `skillMatrix` has one row for each skill that at least one job asks for, in the order of first appearance: `{skill, yours, byJob: {<jobId>: {required, must} | null}}`.
  - `yours` is the level of the talent (1 to 5), or `null` if the talent does not have the skill. A related skill does not count.
  - The talent's own level is used. If the skill has no level, the level of the evidence is used. A skill that the talent only typed (no card) is level 3.
  - A job without skill levels gives `{required: 3, must: true}` for each of its skills.

### Employer: `GET /recruiter/compare?ids=a,b,c,d,e&jobId=` (Premium)

- Order of the checks: sign-in and role, then Premium (403 `PREMIUM_REQUIRED`), then `ids` (400 `fields.ids` = "Choose 2 to 5 profiles to compare."), then `jobId` (400 `fields.jobId` = "Choose one of your jobs."), then the job (404 if it is not yours), then the profiles (404 "We can't find one of the profiles.").
- The old `?a=&b=` form is removed. It now gives 400 for `ids`.
- Answer: `job`, `candidates[]`, `radar`, `areas`, `skillMatrix` (as in plan 5.2).
  - `candidates[]`: `id, alias, level, years, yearsExperience, roles, qualifications, certifications, awards, coverage, skills[], otherSkills[]`.
  - `radar.series[]`: `{id, alias, values[]}` on the same axes as before (coverage, F6 parts, F4 parts). An axis stays only if all profiles have a value for it.
  - `areas[]`: `{area, ranks: [{id, position}]}` for the areas Skill depth, Experience, Transferable skills and Qualification level (Formula 4). Position 1 is the highest. Profiles whose values are within 3 points of the first profile of a group (the "equivalent competency band" of Formula 4) share its position. The next group gets the position that follows the group before it (90, 89, 70 gives 1, 1, 3). Positions are never added up.
  - `skillMatrix[]`: `{skill, required, must, byCandidate: {<id>: {level, status}}}`. `status` is `meets` (level at or above the required level), `below`, `related` (the profile has a related skill: `level` is `null`) or `missing` (`level` is `null`). The levels are the shared levels (see section 2).
- No total, no score, no overall ranking of people. A test scans the answer for these words.
- The function `_areas(cand_a, cand_b, index)` of `routes/recruiter.py` is no longer used by an endpoint. It stays because `tests/test_formulas.py` imports it.

## 6. Entitlements and events

`GET /entitlements` and `PUT /entitlements` add:

| Key | Meaning |
|---|---|
| `crown` | `true` when the plan is Premium |
| `compareMax` | 5 (`config.COMPARE_MAX`). For both roles |
| `benefits` | `[{key, label, description, available, used, usedCount}]` |

`available` is true when the plan allows the benefit (Premium). `used` is true when the user did it at least once. `usedCount` is the number of times. The count comes from the rows of the table `events` where the user is the actor.
A user who goes back to Basic keeps `used` and `usedCount`. `available` becomes false. `canCompare` stays employer-only.

| Role | Benefit key | Label | Event type |
|---|---|---|---|
| Employer | `all_talent` | See every talent profile, not only the top 5 | `talent_list_full` |
| Employer | `invite` | Invite talent to apply | `invite` |
| Employer | `compare` | Compare up to 5 talent profiles | `compare_view` |
| Employer | `advanced_charts` | Pipeline by stage and interest per job | `advanced_charts_view` |
| Talent | `skills_to_learn` | Skills to learn next | `insights_view` |
| Talent | `skill_demand` | Demand for your skills | `insights_view` |

When the server writes the events:
- `talent_list_full`: a Premium employer gets a page of `GET /recruiter/candidates` with MORE than 5 items. Once for each request. Target: `feature` / `talent_list`.
- `invite`: after `POST /recruiter/candidates/:id/contact` works. Target: `application` / the application id.
- `compare_view`: after `GET /recruiter/compare` works (not after a 400, 403 or 404). Target: `job` / the job id.
- `advanced_charts_view`: `GET /stats` of an employer returns `advanced` (Premium). Target: `feature` / `advanced_charts`.
- `insights_view`: `GET /stats` of a talent returns `advanced` (Premium and a profile). Target: `feature` / `insights`. Both talent benefits use this event, so they change together.

Privacy: a user sees only their own counts. No response has the id or the alias of the other side next to these events. The stats of a talent (`basic.profile`) still count only `appear`, `watch` and `saved`. The stats of an employer do not count these events.

New helpers: `store.plan_flags()` (the cheap check that the routes use) and `store.entitlements_of()` (the full answer).

## 7. Other changes

- `util.page_params(query, sorts)` and `util.paginate(items, params, cap=None)`: the one helper for pages.
- `reference.py`: `LEVELS`, `SKILL_LEVEL_LABELS` (`{1: "Beginner", ... 5: "Expert"}`), `WORK_MODES`. No other list.
- `config.COMPARE_MAX = 5`.
- `engine_bridge.job_dict()` adds `level`, `specialisation`, `min_years`, `max_years`, `work_mode`, `education_min`, `certifications_required`, `certifications_preferred`, `awards_preferred`, `skill_requirements`. A key is added only when the job has a value, so that an old job gives the old dictionary. The formulas do not use them yet.
- `catalogue.summary_of()` gives at most 200 characters and skips headings and bullet marks.
- `catalogue.TalentContext.level_of(skill)`: the level of the talent for a skill.

## 8. Tests

- New: `tests/test_v2_migration.py` (migration and the new columns) and `tests/test_v2_infra.py` (pages and sorts, compare, profile keys, job keys, the description, the benefits and events).
- Changed on purpose:
  - `test_talent_flow.py`: `?limit=N` became `?pageSize=N`. `limit=100` and `limit=500` became `pageSize=50` and a check of the clamp. A new helper `all_pages()` reads every page. The key list of the shared profile has the new keys.
  - `test_radar.py`: compare takes 2 to 5 jobs (message "Choose 2 to 5 jobs to compare."). The employer compare uses `ids=` and `jobId=`. The radar has `series`. The test "without a job" is now "a job is needed" (400).
  - `test_employer_flow.py`: the key list of a talent card has the new keys. `PUT /entitlements` has `crown`, `compareMax` and `benefits`. A Premium list has 10 items by default. The compare calls use the new form. Two tests look for their new talent with `sort=updated&pageSize=50` (the list has pages now).
  - `test_concurrency.py`, `test_privacy_rights.py`, `test_auth.py`: `limit` became `pageSize`, and the compare URL has the new form.
  - `test_talent_flow.py`, `test_job_detail_has_similar_jobs_and_a_bridge`: `bridge.readiness.months` can be 0 when a job has no gaps. The new gap formula (Formulas wave) gives 0 in this case. The test now asks for more than 0 months only when the job has gaps.
- The new tests build their talent profiles with the helper `make_talent()` (they do not depend on the CV reader, which changes in wave 1 and wave 4).
- Wave 4 must change on purpose: `test_v2_migration.SchemaVersion2Tests.test_the_old_catalogue_has_no_invented_values` and `test_v2_infra.JobV2Tests.test_the_catalogue_jobs_have_no_invented_values`. They check that the OLD catalogue has no level, years or work mode. The new seed data will have them.


---

# Changes of the BE agent, wave 4 (integration): the taxonomy, the formulas, the new seed

This section lists what wave 4 added or changed. **Every shape of wave 1 stays. Wave 4 only adds** (the two changes on purpose are in section 11).
The formulas are not changed. The numbers are in `docs/changes/Formulas.md`.

## 1. The taxonomy and the lists

- New `jinder/taxonomy.py`. It reads `jinder_backend_engine/data/reference/ict_taxonomy.json` once and keeps it in memory. The path is `config.TAXONOMY_PATH` (the environment variable `JINDER_TAXONOMY_PATH` can change it). If the file is missing, the loader raises `TaxonomyError` with a plain message that names the file.
- `reference.py` is built from it. New or changed lists: `DOMAINS` (3), `INDUSTRIES` (the same 3: the profile keys `industry` and `targetIndustries` hold domains), `SPECIALISATIONS` (by domain) and `ALL_SPECIALISATIONS` (20), `CITIES` and `LOCATIONS` (7 values), `ROLES` (53 titles), `FIELDS_OF_STUDY` (12), `CERTIFICATIONS`, `AWARD_KINDS` (12 slugs) and `AWARD_LABELS`, `SKILL_NAMES` (172), `SKILL_SUGGESTIONS` (7 for each domain), `JOB_CATEGORIES` (= `DOMAINS`), `CATEGORY_MAP` and `INDUSTRY_TO_CATEGORY` (identity on the 3 domains). `WORK_TYPES`, `WORK_MODES`, `LEVELS`, `QUALIFICATIONS`, `COUNTRIES`, `YEARS` stay.
- Every industry, role, field, category and sample of another field of work is gone from `reference.py`, `skills.py`, `translation.py`, `seed.py` and the other files of the platform. A test (`tests/test_taxonomy.py`) scans the code and the demo data.

## 2. Checks when data is saved (a value that is not in the taxonomy is cleaned, not kept)

| Where | Rule |
|---|---|
| `profile.industry`, `profile.targetIndustries` | Only the 3 domains. Any other value is dropped |
| `profile.specialisation` (new key) | One of the 20 specialisations of the taxonomy, else `""` |
| `profile.workModes` (new key) | A list of Onsite, Hybrid, Remote |
| `profile.awards[].kind` | A kind of the taxonomy. The slug (`hackathon`) or the label ("Hackathon") is accepted and the slug is stored. Another kind becomes `""`. The name stays free text |
| `profile.certifications[].name` | Free text (scrubbed), as before |
| `profile.skills` | A name, or a dictionary `{name, level}` (the name is kept) |
| `translation[].years` (new key) | A number 0 to 40 with one decimal, for a skill card only. Else `null` |
| Job `specialisation` | One of the taxonomy. When the job has a domain (`category`), it must belong to that domain. Error field `specialisation` |
| Job `awards.preferred` | Kinds of the taxonomy (slug or label, stored as slug). Error field `awards` ("Choose award kinds from the list.") |
| Job `category` | One of the 3 domains (as before, with the new list) |

## 3. Skills (`skills.py`)

What changed in `skills.py` (for the CV agent and the lead: **the signatures that others use did not change**; the CV files do not import this file):
- `SKILL_PATTERNS`: one pattern for each skill of the taxonomy, built from the name and the aliases, as whole words. Short or common names are handled: `C`, `R` and `Go` count only in a list ("Python, R, SQL"); `Swift`, `Rust`, `Ruby` and `Spark` count only with a capital letter; a term that starts with a letter does not follow a dot (`js` is not found in `Node.js`); `C#`, `C++`, `.NET`, `Node.js` and `CI/CD` are found.
- `skills_in(text)`: the same signature. The names come in the order of their place in the text. A whole text that is a name or an alias gives that skill ("golang" gives "Go").
- `RELATED` is now `{lower name: {lower names}}` from the `related` lists of the taxonomy (both ways). It was a list of lists. `TRANSFERABLE_SKILLS` has the skills of the kind `method` and `soft`.
- `job_skills(title, text, limit=8)` and `catalogue.suggest_skills(title, description)`: the same signatures. They give taxonomy names.
- New: `canonical_skill_name(text)`, `suggest_requirements(title, text, domain, limit)`, `occupation_of_title(title)`, `occupation_for_job(title, specialisation, domain)`, `results_from_breakdown(...)`, `STATUS_OF_FIT`, `SKILL_NAMES`, and `skill_match(job_skills, names, levels=None, required=None)`, which is level-aware (`job_skills` can hold dictionaries `{name, level, must}`).
- Not changed: `canonical_skills`, `skill_names_from`, `_js_round`.

### SkillResult (one skill that a job asks for) and the mapping of the statuses

`match.skills[]` of a talent, `skills[]` of an application and `skills[]` of an employer card have these keys:

| Key | Meaning |
|---|---|
| `name`, `status`, `reason` | As before. `status` stays one of `match`, `partial`, `gap`, so old clients keep working |
| `fitStatus` (new) | The word of the formula: `meets`, `below`, `related` or `missing` |
| `required` (new) | The level that the job asks for (1 to 5) |
| `level` (new) | The level of the person (1 to 5). `null` if the person does not have the skill (also for `related`) |
| `must` (new) | `true` for a must-have skill |
| `via` | Only for `related`: the name of the related skill that the person has |

The mapping: **meets gives match. below gives partial. related gives partial. missing gives gap.**
`coverage` is the level-aware skill coverage of the formula, rounded to a whole number. `matched` counts `meets`. `partial` counts `below` and `related`. `matchedSkills`, `partialSkills` and `gaps` (names) follow the same mapping.

## 4. The match, the list and the page

- `match.score = round(0.55 x fit + 0.45 x FRS*, 1)`. `fit` is `evaluate_job_fit(...)["fit"]` (Formula 1). FRS* is the feed score of Formula 5 after the feedback loop, with one decimal.
- The feed ranks ALL the open jobs together. The lists remove the jobs that the talent skipped or applied to after the ranking. So **the score in a list is the score on the page of the job** (tested). A closed job is ranked together with the open jobs and does not change their scores.
- `match.recommended` is `true` when `score` is 45 or more (`catalogue.RECOMMEND_MIN_SCORE`). About 36% of the open jobs are recommended for a talent. The number 45 is a choice of the platform (see Questions in the report).
- `match.reasons` and `match.notes` come from the parts of the fit: the target role, the skills ("You meet 6 of the 11 skills (1 below the asked level, 3 related)"), the level, the domain, the location.
- The numbers of the platform path (51 talents with the demo talent, 53 open jobs): different scores in the top 20: at least 18 (mean 19.49; 2 talents have exactly 18). Best minus worst: at least 45.4 (mean 55.5). No radar axis is constant. Employer order: at most 1 tie in a top 10 (to one decimal).

## 5. `bridge` of `GET /jobs/:id`

- **Added**: `bridge.path` = `evaluate_path(...)` of Formula 2, as in plan 5.3: `{axes[{key,label,group,required,have,status}], fit[], gaps[], summary{fitCount,gapCount,monthsToClose,readinessTier}}`.
- **Removed**: `bridge.projection` (and `engine_bridge.projection`). The 12-month chart is gone.
- Kept: `occupation`, `readiness` (`statutoryBlocker` is always `false`), `gaps` (names from the formula; `blocker` is always `false`), `axes` (the same 8 keys), `score`.
- A job without a profile of the talent gives `bridge: null`, as before.

## 6. Pay and jobs

- New column `jobs.salary_unit` (`year`, `day` or `hour`; default `year`). The numbers `salary_min` and `salary_max` are stored **as given** (a day rate stays a day rate).
- `salary` is the text: `$900 per day`, `$150,000 – $170,000 per year`. New key `salaryUnit` on every job (cards, detail, employer job). `salaryMin` and `salaryMax` stay private.
- `engine_bridge.job_dict` sends `salary_min`, `salary_max` and `salary_unit` to the engine. **The change to a yearly pay happens only in the engine** (`annual_salary`: day x 220, hour x 1950). The platform never converts.
- An employer job gets its numbers and unit from the salary text (`catalogue.parse_salary`): "per day", "a day", "daily" or "day rate" gives `day`; "per hour", "an hour" or "hourly" gives `hour`; else `year`. A text with no amount ("Market competitive") gives no numbers. An edit of `salary` changes them.
- The occupation (`anzsco`, `occupation`) of an employer job comes from the taxonomy: the longest role of the role list found in the title, else the occupation of the specialisation. No match: both are empty.
- `POST /recruiter/jobs/suggest-skills` keeps `skills` (names) and **adds** `skillRequirements` (`[{name, level: 3, must: true}]`). It also reads `category` (a domain) from the body. Order: the skills that the text shows, the core skills of the occupation of the title, the usual skills of the domain. All names are taxonomy names.
- `summary` is now the first whole sentences that fit in 200 characters (it ends with "…" only if the first sentence alone is longer). Headings and bullets are left out.

## 7. Translation (`POST /profile/translate`)

- The library has 45 role pairs and about 40 skill pairs. Every name is a name of the taxonomy.
- A role card: `mapped` is a title of the role list. `anzsco` and `occupation` come from the taxonomy (`roles` to `occupationCode`). `kind` is `cross-border` (an overseas title: "BI Specialist", "MIS Executive", "Programmer", "Software Developer (Vietnam)" gives "Software Engineer"), `cross-industry` (for example "Quantitative Analyst" gives "Data Scientist") or `direct`. A title is read without its level words, its company and its place in brackets. Two titles that give the same role make one card ("BI Specialist; MIS Executive"). A title that is not an ICT title gives **no** role card.
- A skill card: `mapped` is the name of the taxonomy (a name, an alias, or a pair: "spreadsheets" gives "Microsoft Excel", "Informatica" gives "ETL and ELT pipelines"). A skill that the taxonomy does not know keeps its name.
- `level` of a skill card: the level from the profile (`skillLevels: [{name, level}]`, or a skill `{name, level}`, which is the form of the CV result), else the level that the evidence gives (Strong 4, Moderate 3, Limited 2: rule F8). A role or qualification card has `level: null`. New key `years` (`null` at first).
- `translate_keeping` keeps the decisions, the levels and the years that the talent set.
- Role cards no longer add skills: the shared `skills` list has the skill cards only. A role card gives `roles` (title and ANZSCO code).

## 8. Employer side

- `GET /recruiter/candidates` and `/recruiter/candidates/:id`: the cards have the same keys. The per-skill match and the order come from Formula 6 on the **shared profile only** (`engine_bridge.shared_candidate_dict`). The order is `order_value` of the engine (0.6 coverage + 0.4 TSS). No score is sent.
- The shared profile has **new keys**: `specialisation`, `workModes`, and `years` in each item of `skillLevels` (`{name, level, years}`). `issuer` and `kind` stay (the lead decided so).
- `GET /recruiter/compare`: the radar has **2 more axes**: `level` ("Level standing") and `evidence` ("Evidence"). The label of the axis with the key `statutory` is now **"Certification readiness"** (the key stays). `areas` has up to **8 areas** (new: Level standing, Evidence, Certifications, Awards). `skillMatrix` has the same shape; the levels and statuses come from the formula (`meets`, `below`, `related`, `missing`).
- The legacy functions `_areas` and `_order_value` are removed from `routes/recruiter.py`. `engine_bridge.OccupationIndex` and `engine_bridge.projection` are removed.
- **The errors of both compare endpoints name the ids that cannot be compared**: `{ "error": { code, message, fields: { ids: "..." } }, "missing": [ids] }`. For an unknown id: 404 and `missing` has the unknown ids. For a wrong number of ids: 400 and `missing` has the ids above the limit (it is `[]` if there are too few). A good answer has no `missing`. `error.code` and `error.message` did not change. This holds for `GET /jobs/compare` (talent) and `GET /recruiter/compare` (employer).

## 9. Premium insights of the talent (`GET /stats`, `advanced`)

Level-aware, from the skills of the 20 best jobs:
- `gapRanking[]`: `{skill, count, needLevel, yourLevel, missing, below}`. A skill counts when it is missing or below the asked level (`count = missing + below`).
- `demandForYourSkills[]`: `{skill, count, needLevel, yourLevel}`. A skill counts when the talent meets the asked level.
- `needLevel` is the mean level that the jobs ask for (one decimal). `yourLevel` is the level of the talent (`null` for a missing skill).

## 10. The seed

Everything comes from `jinder_backend_engine/data/synthetic` (`config.SYNTHETIC_DIR`). The old `australian_*` files, `international_candidates_dataset.csv` and `real_resumes_dataset.csv` are not read any more (the files are not deleted).

- **Catalogue**: the 50 jobs of `jobs.json`. Id: `job-<key>`. `postedDaysAgo` and `closesInDays` count from now (`refresh_catalogue_dates` keeps the dates fresh at each start). The description is stored with its line breaks (never flattened, never cut). `summary` is the first sentences of the description. All new keys of a job are set. Pay: numbers as given with the unit (44 jobs by year, 6 by day).
- **Sample talent**: the 50 profiles of `talents.json` (`is_sample = 1`, no password, alias only). Each has the level, the years, the specialisation, the skills with level and years (accepted cards), the certifications, the awards, the cities, the work modes, the work types, the private evidence lines, and the role card with the ANZSCO code. `updated_at` is now minus `updatedDaysAgo` (spread over 60 days, F12).
- **Seed version**: `SEED_VERSION = "2"`. A database that was seeded with version 1 (the old data) gets the new data at the next start: the old catalogue jobs (and their bookmarks and skips) and the old sample talent are removed and the new ones are made. Real accounts stay. The demo story is made again (the demo accounts stay; their old jobs, applications and alerts go).
- **Old version 2 databases** from the time of the development get the new columns (`jobs.salary_unit`, `profiles.specialisation`, `profiles.work_modes`, `translated_skills.years`) at the start (`db._add_late_columns`). The schema version stays 2.
- **Demo accounts** (`python start.py --demo`):
  - Employer **Alex Morgan**, company **Bluebushworks**, owns the 4 jobs of `demo.json`: "Data Engineer, Solar Analytics" (Mid, open, posted 6 days ago), "Senior Backend Engineer, Installer Platform" (open), "Machine Learning Engineer, Solar Forecasting" (closes in 4 days) and "Contract Data Engineer, Billing Migration" (a day rate, closed 2 days ago).
  - Talent **Teal Heron** (Linh Nguyen): a **Mid data analyst** who studied in Vietnam and wants to be a Data Engineer. Her overseas titles "BI Specialist" and "MIS Executive" become one **cross-border** role card. She has 8 skills with levels (SQL 4, Python 3, Power BI 4, Microsoft Excel 4 from "spreadsheets", Data analysis 4, Data visualisation 3 from "dashboards", ETL and ELT pipelines 2 from "Informatica", Data modelling 3 from "ER diagrams"), one certification (Microsoft Certified: Power BI Data Analyst Associate, 2024) and one award (Smart City Hackathon Runner-up, kind `hackathon`, 2023). She has strong, medium and weak jobs in her list.
  - The story: Teal Heron is in **interview** for the Data Engineer job (3 interview times to choose). For each demo job, the sample talent with the **best cover of the must-have skills** applies (chosen by `seed._must_coverage`; one talent applies to one job only): 3 applications for the Data Engineer job (applied, review and Teal Heron in interview), 2 for the Backend job (applied, review), 1 for the ML job (applied), and 1 finished application for the closed job (confirmed, with an offer and the name shared). The employer has alerts for the new applications. The jobs have activity events for the charts.

## 11. What is different for the clients

- **Changed on purpose** (the only two): (a) `bridge.projection` is gone (planned). (b) The shared `skills` list and `TalentContext` no longer count a role card as a skill (a role is not a skill).
- `GET /jobs/recommended` has fewer jobs than before (about 36% of the open jobs). The home page asks `?pageSize=5`.
- A profile that is saved with `industry: ["Technology"]` (or another value that is not a domain) has `industry: []` afterwards. The CV reader still returns such a value in `fields.industry`: see "Needs from the CV agent" in the report.
- `match.skills[].status` keeps the old words (`match`, `partial`, `gap`). The new word `below` is in `fitStatus`. See section 3.

## 12. Tests of wave 4

- New: `test_taxonomy.py` (the 4 checkers of the data agents run as sub-processes, the loader, the word patterns, no word of another field), `test_seed_v2.py` (50 jobs, 50 sample talents, complete descriptions, pay and unit, F12, a second run, an old seed, the demo accounts, a new start with `--demo --reset-db`), `test_differentiation_platform.py` (plan section 9 through `TalentContext`, the list score equals the page score, the employer order, privacy of the dictionaries of the engine), `test_wave4.py` (SkillResult, `bridge.path`, the pay unit, the checks of the new values, the errors with `missing`, the insights, the cost of the password hash).
- Changed on purpose (old tests with the old data): `helpers.CV_LINES` (an ICT CV), `test_talent_flow.py` (translation, shared profile, search, detail, closed job), `test_employer_flow.py` (a data engineer job, a job file in Perth, the privacy CV), `test_radar.py` (9 radar axes and the new label), `test_review_fixes.py` (related skills from the taxonomy, status words, word boundaries, the dictionary for an employer, the occupation of a job), `test_privacy_rights.py` and `test_v2_infra.py` (ICT jobs and skills, award slugs), `test_v2_migration.py` (the new catalogue, the late columns), `test_security.py`, `test_auth.py`.
- **Run time**: the password hash costs the most when many test accounts are made. `run_tests.py` and `tests/helpers.py` set `JINDER_FAST_TEST_HASH=1` (scrypt cost 2^4 instead of 2^14). It is never the default: the server writes a warning if it starts with it, and a test starts a new process to check that the default is the strong hash (`JINDER_REAL_HASH_IN_TESTS=1` runs the tests with the real hash). The production code of the hash did not change. Result on this computer: **634 tests: about 104 s with the real hash, about 69 s with the fast hash**. The rest of the time is the CV tests (about 20 s) and the tests that make many accounts and rank 50 jobs for each.
