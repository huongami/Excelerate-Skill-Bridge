# The six formulas in the product

The formulas are in `jinder_backend_engine/intelligence_engine`. Their mathematics is in
`jinder_backend_engine/docs/02_FORMULAS_MATHEMATICAL_SPEC.md` and in the file `0N_*.md` of each formula. This document says **where the product uses each one**,
**what the user sees**, and **what the product never shows**.

Version 2 rewrote the six formulas in place (same file names, same main function names). The reason was the feedback "the jobs that are shown all have the same overall fit".
The formulas now use smooth functions (no fixed steps), the level of the job and of the talent (Intern, Junior, Mid, Senior, Lead, Principal), exact years, the level of each skill (1 to 5),
certifications, awards, work mode and the pay unit. The names of skills, roles, certifications and levels come from the taxonomy (`jinder_backend_engine/data/reference/ict_taxonomy.json`).
All score math is in the formula files. The platform (`jinder/engine_bridge.py`) only builds dictionaries and calls the functions.

## Product rules that limit the formulas

1. **No single score on a person** (PRD, section 5; Feature 3 and 5 backlog). A score about a person goes only to the person, as a guide. Employers get an order, per-skill matches and reasons. They never get a total.
2. **Skills only.** No formula reads a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo (Feature 3, AC11). A test checks this.
3. **Employers see the shared profile only.** The formulas that run for an employer (Formulas 4 and 6) read the shared profile: accepted skills with their levels, roles, level, years, certifications and awards.
   They do not read the CV, the evidence lines or the length of the CV text.
4. **Explain each result.** A number comes with its reasons.
5. **A level is not a title word.** The seniority fit uses the level and the exact years, not words in a job title.
6. **A missing certification is a gap, not a block.** The old legal block (AHPRA, CPA) is gone. A missing required certification is a gap with the months to prepare for it.
7. **Education is a soft factor.** A missing degree lowers one small part (weight 0.03). It never gives 0 and it is never a hard limit.

## Where each formula runs

| Formula | Code | Input | Output used | Who sees it |
|---|---|---|---|---|
| F-01 SMF and **fit** | `catalogue.TalentContext` (`analyse`, `_match`) → `engine_bridge.job_fit` (the fit and the per-skill result); `catalogue.fit_axes_for` and `bridge_for` → `engine_bridge.smf` (the axes) | The talent: level, exact years, skills with level, certifications, awards, target roles, domain, places, work modes. The job: level, years, skills with level and `must`, certifications, awards, city, work mode | `fit` (0 to 100, one decimal), the per-skill result (meets, below, related, missing), the coverage, and the axes Occupation fit, Skills and Work methods | The talent: every job card, Job detail |
| F-02 GSI, JRS and **path** | `catalogue.bridge_for` → `engine_bridge.gap_analysis` and `engine_bridge.path` | The same talent and job | The gap list (kind, have, need, months), the readiness tier, the months to close, and the `path` object | The talent, on Job detail ("How this job fits you" and "Your path to this job") |
| F-03 JPI | `catalogue.similar_jobs`, `routes/jobs.jobs_compare` → `engine_bridge.proximity` | Two jobs: occupation, skills with levels, level, salary (as a yearly pay), domain, place and work mode | The order of similar jobs and a label. On the Compare page: the parts of each pair of jobs | The talent: Job detail and Compare |
| F-04 RMS | `routes/recruiter._metrics` → `engine_bridge.merit_dimensions` | The **shared** profile of 2 to 5 talents, and the chosen job | The dimensions (areas): skill depth, experience, level standing, evidence, transferable skills, certifications, awards, qualification level. Positions inside one area. **The total is not used** | The employer, in Compare (Premium) |
| F-05 FRS | `catalogue.TalentContext.frs_star` → `engine_bridge.feed_scores` | The talent profile and **all open jobs** | The feed score, with the employer diversity penalty | Nobody sees the number. It is a part of the Fit score and sets the order |
| F-05 feedback loop | `engine_bridge.behavioural_adjust` | Bookmarks and skips of the talent | +10% saved employer, +5% saved domain, -25% after 3 skipped jobs of one employer | Nobody sees the number |
| F-06 TSS | `routes/recruiter` (talent list, compare) and `routes/applications` (the match of an application snapshot) → `engine_bridge.talent_score` | The **shared** profile of a talent, one job | The per-skill match and one part (40%) of the order of the employer's talent list | The employer sees the per-skill match. Nobody sees the number |

## The Fit score and the order of jobs

**Talent: recommended jobs, search, bookmarks.**

```
Fit score (match.score) = round(0.55 × fit + 0.45 × FRS*, 1)
```

- `fit` is **defined in the engine** (`01_skill_matching_model.evaluate_job_fit`). It is a weighted mean of nine parts: skills 0.39, methods 0.04, occupation 0.16, level 0.10, experience 0.09, domain 0.10, location 0.07, work type 0.02, education 0.03.
  A certification adjustment (a missing required certification lowers it, a held preferred one raises it) and a preferred award (at most +3 points) are added. A part that does not apply to a job is left out. The weights are in the math document.
- `FRS*` is Formula 5 (capability, wage upside, location, recency, minus the diversity penalty) after the feedback loop.
- A job is **recommended** when the Fit score is 45 or more (`catalogue.RECOMMEND_MIN_SCORE`). A choice of the platform. About 36% of the open jobs are recommended for a talent.
- The feed ranks **all** open jobs together. The lists remove the jobs that the talent skipped or applied for after the ranking. So the Fit score in a list is the same number as on the page of the job (a test checks this).
- The product shows the Fit score on the job card and on Job detail with one decimal. The lists have two sorts: **Best match** (highest Fit score first) and **Newest posted**. Equal values are ordered by the job id.

**Employer: talent list.**

```
order = 0.6 × skill coverage for the chosen job + 0.4 × TSS
```

The employer sees the coverage and the per-skill match. The order number is never sent. The two sorts are **Best fit for this job** and **Recently updated** (the profile that changed last comes first).
On the Basic plan the employer sees the top 5 of the order (Feature 5, AC7), and is told the real number of profiles.

## What the user sees: the radar charts

The numbers of the formulas are shown **part by part**, never as one total of the parts. Every chart has a table with the same numbers, so that colour is not the only signal.

| Screen | Chart | Axes (0 to 100, one decimal) |
|---|---|---|
| Job detail, "How this job fits you" | One polygon | Occupation fit, Skills, Work methods (F-01); Readiness (F-02); Capability, Pay upside, Location, Freshness (F-05) |
| Job detail, **"Your path to this job"** | **Two layers**: "You have" (filled) and "Job requires" (outline) | The 7 skill groups of the job (see below), plus Experience, Level and Certifications (only when the job lists a certification) (F-02) |
| Compare, talent (2 to 5 jobs) | One line for each job, same axes | The same 8 axes of "How this job fits you". A table gives the pairs of jobs: occupation, requirements, salary, sector, place and level (F-03) |
| Compare, employer (2 to 5 talent, Premium) | One line for each profile | Skills for this job (coverage); Requirement fit, Seniority fit, **Certification readiness** (F-06); Skill depth, Experience, Transferable skills, Level standing, Evidence (F-04). An axis stays only if all profiles have a value for it |

The **7 skill groups** of the path radar are: Languages, Frameworks & libraries, Cloud & DevOps, Data & storage, ML & AI, Engineering practices and Collaboration.
For a skill group, "Job requires" is the weighted mean of the levels that the job asks for (level ÷ 5 × 100). "You have" is the same for the levels of the talent (a level above 5 counts as 5).
A skill that the job marks as required (`must`) weighs 2 times more. The status of an axis is **Fit** (you have as much as the job asks), **Above** (15 points or more over) or **Gap** (less).
The path also gives a **Fit list** (what meets a requirement: skills, experience, level, certification, award) and a **Gap list** (missing skill, below level, experience, level, certification), each with what the talent has, what the job needs and the months.
The months of a skill gap come from the taxonomy (`monthsToLearn`), the difference of the levels and a learner factor. Gaps close in parallel, so the total is less than the sum: the largest gap + 0.18 × the rest.
**There is no 12-month chart and no projection** in version 2.

## What the talent sees on a job (`GET /jobs/:id` → `bridge`)

```json
{
  "score": 71.4,
  "axes": [ { "key": "occupation", "label": "Occupation fit", "formula": "F1", "value": 80.2 }, "…8 values…" ],
  "occupation": { "anzsco": "261313", "title": "Software Engineer", "alignment": 74.5, "tier": "Direct Industry Alignment", "tierCode": "TIER_1_DIRECT" },
  "readiness": { "gapSeverity": 38.1, "readiness": 61.9, "months": 5.5, "tier": "Moderate Gap (Fast-Track Upskilling)", "tierCode": "TIER_MODERATE_GAP", "statutoryBlocker": false },
  "gaps": [ { "name": "Kubernetes", "category": "CAT-2", "categoryName": "Required skill", "months": 3.5, "blocker": false } ],
  "path": {
    "axes": [ { "key": "languages", "label": "Languages", "group": "languages", "required": 80, "have": 60, "status": "gap" } ],
    "fit":  [ { "kind": "skill", "label": "Python", "have": "Advanced", "need": "Proficient", "note": "" } ],
    "gaps": [ { "kind": "missing", "label": "Kubernetes", "have": "none", "need": "Proficient", "months": 3.5, "must": true, "note": "" } ],
    "summary": { "fitCount": 7, "gapCount": 3, "monthsToClose": 5.5, "readinessTier": "Moderate Gap (Fast-Track Upskilling)" }
  }
}
```

The values above are examples. `bridge.projection` does not exist any more. `statutoryBlocker` and `blocker` are always `false`. The old codes `CAT-1` to `CAT-4` mean: certification, required skill, nice-to-have skill, experience or level.
The screen shows the tiers as words, the gaps with their kind and months, and the two radar charts. It states that this is a guide for the talent and that employers never see it.

## How the input is built (`engine_bridge.candidate_dict`, `engine_bridge.job_dict`)

| Formula input | Source |
|---|---|
| `skills` (name, level 1 to 5, years) | The accepted translated skills. The level is the one that the talent set or the CV gave. A skill with no level gets 3 from Moderate evidence (Strong 4, Limited 2; rule F8). A role card is not a skill |
| `level`, `years_experience` | The level of the profile (if empty: the title words, then the years). The exact years; else the middle of the band ("3–5 years" → 4.0) |
| `domain`, `specialisation` | `profile.industry` (one of the 3 domains) and the specialisation |
| `highest_education`, `field_of_study` | The highest qualification, by level, and the fields of study. Education is a soft factor |
| `target_roles`, `target_anzsco_code` | The target roles as the talent wrote them. The engine finds the occupation from the code, then from the role titles of the taxonomy |
| `certifications`, `awards` | The lists of the profile (name, issuer or kind, year) |
| `preferred_location`, `locations`, `work_modes`, `work_types` | The goals of the talent. A city "Remote" means that the talent wants remote work |
| `cv_raw_text` | **Talent screens only, and only if the skill list is empty.** The evidence lines are private. **Never sent for an employer** |
| job `required_skills` | `[{name, level, must}]` from `skillRequirements`. A job without levels gives level 3 and `must` |
| job pay | `salary_min`, `salary_max` and `salary_unit` as stored. The engine changes a day rate (x 220) or an hour rate (x 1950) to a yearly pay in one function, `annual_salary`. The platform never converts |
| job `days_old` | The age of the job in days (not the real clock) |

For an employer call the bridge uses the **shared profile** only (`shared_candidate_dict`).

## What is never shown

- A total of the radar axes, or any one verdict on a person.
- A score or a rank number on a person for an employer. The order of the talent list is the only thing that the employer gets.
- The `FRS`, `TSS`, `RMS` and `order` numbers.
- The path and the gap list to an employer (they are for the talent).
- The CV text, the evidence lines, the name, the email, the country, the nationality, the visa, the age or the gender in any formula.

## Differentiation numbers (the tuning target)

The feedback said that the shown jobs had the same fit. The test `tests/test_differentiation.py` (formula level) and `tests/test_differentiation_platform.py` (through the platform) check these numbers on the 50 jobs and 50 talents.

| Check | Target | Result |
|---|---|---|
| Different Fit scores in the top 20, each talent | 18 or more | Formula level: min 19, mean 19.50. Platform level (51 talents with the demo talent, 53 open jobs): min 18, mean 19.49 (2 talents have exactly 18) |
| Best minus worst Fit score, each talent | 30 or more | Min 45.4, mean 55.5, max 67.6 |
| Radar axes with one value for all jobs | 0 | 0 of 400 |
| Exact ties in the top 10 of the employer order, each job | 2 or fewer | At most 1 |
| Near-twin jobs with the same score for a talent | 0 | 0 (the smallest difference is 0.2) |

The plan first asked for 19 different scores in the top 20. The lead changed it to 18, because a smooth score with a range of about 40 points cannot promise 19 for every talent when the scores have one decimal.
If the rounding changes, or the data changes, 2 to 4 talents can have 17 or 18 different scores.
The weights of the fit (Formula 1) and of the feed (Formula 5) are the only constants that were tuned on the demo data. They are in `FIT_WEIGHTS` (file 01) and in `DEFAULT_WEIGHTS`, `CAP_WEIGHTS`, `WAGE_SLOPE` and `RECENCY_RATE` (file 05).

> **Demo values.** The pay benchmarks for a Mid level (Software Engineering 130000, AI & Machine Learning 150000, Data 125000 AUD per year), the pay step of +22% for each level, the 220 working days of a day rate, the 1950 hours of an hourly rate,
> the credit that a talent gets for a method or soft skill that they did not list, the city distances and the weights are **demo assumptions**. They are not statistics and not official data.
> The taxonomy (`monthsToLearn`, `rarity`, `prepMonths`) and the ANZSCO-style codes were made by hand and were not checked against the official ANZSCO list.

## Tests

- `tests/test_formulas.py`: the properties of each formula (continuous scores, parallel learning time, symmetric job proximity, the feedback-loop numbers, the diversity penalty, the path object), and that no private key changes any result.
- `tests/test_differentiation.py` and `tests/test_differentiation_platform.py`: the numbers above.
- `tests/test_wave4.py`, `tests/test_radar.py`: the per-skill result, `bridge.path`, the pay unit and the compare radar and areas.
- `tests/test_employer_flow.py::PrivacyTests`: no employer response has a score or personal data.
- The formula self-check: `python jinder_backend_engine/run_verification.py` (or `python run_tests.py --formulas`).
- The file `intelligence_engine/formulas_presentation.html` still shows the slides of version 1. A note at the top says so.
