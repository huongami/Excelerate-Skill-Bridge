# 04 - Data and Scoring Integration Specification (version 2)

Source of truth for the data that the formulas read, for the wiring of the formulas to a product, for the behaviour loop, and for the mathematics of the charts.

**Scope.** The product is `jinder_platform` (see its own `docs/`). It calls the six formulas of `intelligence_engine/` through `engine_bridge.py`.
The stand-alone prototype in `backend/` (port 8095) is the earlier version. Its database (appendix A) is not changed. The formulas accept the old dictionary shapes, so the prototype still runs.

---

## 1. Data

### 1.1 Files

| File | Content |
| :--- | :--- |
| `data/reference/ict_taxonomy.json` | The one list of names: levels, skill levels, domains, skill groups, skills (aliases, related, `monthsToLearn`, `rarity`), occupations (ANZSCO code, core skills, methods), certifications (`prepMonths`, evidences), award kinds, roles, cities, work modes, work types |
| `data/synthetic/jobs.json` | 50 synthetic jobs |
| `data/synthetic/talents.json` | 50 synthetic talent profiles (private evidence lines are only for the talent) |
| `data/synthetic/demo.json` | 4 jobs of the demo employer account |
| `data/australian_*.json`, `*.csv` | The data of the prototype (version 1). The product does not use it |

All sample data is synthetic. The taxonomy is a demo list that people made by hand. It is not an official standard.
The engine finds the taxonomy file itself (`../data/reference/ict_taxonomy.json`, or the path in the environment variable `JINDER_TAXONOMY_PATH`). Without the file, it uses simple defaults.

### 1.2 Levels and skill levels

| Rank | Level | Typical years |
| :---: | :--- | :---: |
| 0 | Intern | 0 |
| 1 | Junior | 0 to 2 |
| 2 | Mid | 2 to 5 |
| 3 | Senior | 5 to 9 |
| 4 | Lead | 7 to 12 |
| 5 | Principal | 10 or more |

The typical years are a guide. A job with no years uses them. A skill level is 1 Beginner, 2 Working, 3 Proficient, 4 Advanced, 5 Expert.

### 1.3 Talent dictionary (input of the formulas)

| Key | Type | Meaning |
| :--- | :--- | :--- |
| `id`, `alias` | text | The alias is the only name of a person that a formula returns |
| `level` or `level_rank` | text or 0 to 5 | If missing, the engine uses the title words, then the years |
| `years_experience` | number | Exact years. Use the middle of the band if the exact value is not known |
| `domain`, `specialisation` | text | From the taxonomy |
| `current_title`, `target_roles`, `target_anzsco_code` | text, list, text | The roles of the talent. The engine finds the occupation in the taxonomy |
| `highest_education`, `field_of_study` | text, list | |
| `skills` | list | Each skill: `name` (or `skill_name`), `level` 1 to 5, `years`, `last_used_year`, `skill_type` |
| `certifications` | list | `{name, issuer, year}` |
| `awards` | list | `{name, kind, year}` |
| `preferred_location`, `locations`, `work_modes`, `work_types` | text, list | |
| `cv_raw_text` | text | The talent own screens only. Formulas 4 and 6 never read it |

### 1.4 Job dictionary (input of the formulas)

| Key | Type | Meaning |
| :--- | :--- | :--- |
| `id`, `title`, `company` | text | |
| `category` | text | The domain |
| `specialisation`, `level` | text | |
| `min_years`, `max_years` | number or null | A job with a minimum and no maximum is open-ended |
| `city`, `location`, `work_mode`, `type` | text | `work_mode` is Onsite, Hybrid or Remote |
| `anzsco_code`, `anzsco_title` | text | |
| `salary_min`, `salary_max`, `salary_unit` | number, number, text | Unit `year`, `day` or `hour`. The engine changes the pay to a yearly pay with `annual_salary` (day $\times$ 220 working days, hour $\times$ 1950 hours) |
| `required_skills` | list | `{name, level 1 to 5, must}` (a list of names also works) |
| `certifications_required`, `certifications_preferred` | list | |
| `awards_preferred` | list | Award kinds |
| `education_min` | text | A soft factor |
| `days_old` | number | Age of the posting in days |

### 1.5 Rule for the pay

`annual_salary(min, max, unit)` in `03_job_to_job_comparison.py` is the one function that changes a pay to a yearly pay: year $\times 1$, day $\times 220$, hour $\times 1950$.
If no unit is given, a maximum below 500 is an hourly rate, from 500 to 3999 a day rate, and a larger number is a yearly pay. A job with no pay gets the benchmark of its domain and level.

### 1.6 Rule for education

Education is a soft factor. A missing degree lowers a small part of the fit smoothly (the part is at least 0.2 of its weight of 0.03). It never gives 0 and it is never a hard limit.

---

## 2. Formula integration

```
 ict_taxonomy.json -> engine_common.py -> 01 -> 02 -> 05
                                           |-> 03
                                           |-> 04 -> 06
```

| Screen or use | Function | Output that is used |
| :--- | :--- | :--- |
| Job card and job detail (talent): the score | `01.evaluate_job_fit(talent, job)` and `05.rank_job_feed_for_candidate` | `fit`, `feed_ranking_score`. The platform shows $0.55\,\text{fit} + 0.45\, FRS^{*}$ with one decimal |
| Per-skill match (talent and employer) | `01.evaluate_job_fit(...)["skill_breakdown"]` | `status` (meets, below, related, missing), `credit`, `need_level`, `have_level` |
| "How this job fits you" (8 axes) | `01.evaluate_skill_match`, `02.evaluate_skill_gaps`, `05.compute_feed_job_score` | see section 4.1 |
| "Your path to this job" | `02.evaluate_path(talent, job)` | the `path` object |
| Similar jobs, compare jobs | `03.compare_two_jobs`, `03.compare_multiple_jobs` | `job_proximity_index`, `sub_metrics`, `differentials` |
| Employer: talent list order | `06.compute_talent_search_score(shared profile, job)` | $0.6 \cdot \text{coverage} + 0.4 \cdot TSS$. Never shown |
| Employer: compare profiles (Premium) | `04.calculate_candidate_merit_score(shared profile, job=job)` | `sub_metrics` (the dimensions). The total is never shown |

The platform shows no score on a person to an employer. It shows the per-skill match, the coverage, the levels, the certifications and the awards, and an order.

---

## 3. Behavioural ranking feedback loop

The platform (not the engine) changes the feed score after the engine gave it:

$$FRS^{*}(J \mid C) = \min\left(100,\; FRS(J \mid C) \cdot \left(1 + \Delta_{\text{save}} - \Delta_{\text{ignore}}\right)\right)$$

1. **Save affinity** $\Delta_{\text{save}}$: +0.10 if the talent saved a job of the same employer; +0.05 if the talent saved a job in the same domain.
2. **Ignore penalty** $\Delta_{\text{ignore}}$: 0.25 if the talent skipped 3 or more jobs of the same employer.
3. A job that the talent skipped is removed from the feed. A job with 3 or more reports is hidden.

---

## 4. Mathematics of the charts

All values are from 0 to 100. Every chart has a table with the same numbers.

### 4.1 "How this job fits you" (8 axes, one polygon)

| Axis | Key | Source |
| :--- | :--- | :--- |
| Occupation fit | `occupation` | `01 evaluate_skill_match` -> `sub_metrics.s_tree_taxonomy` = $100\, O$ |
| Skills | `skills` | `01` -> `sub_metrics.s_direct_competency` = $S_{\text{direct}}$ |
| Work methods | `methods` | `01` -> `sub_metrics.s_trans_methodology` = $S_{\text{trans}}$ |
| Readiness | `readiness` | `02 evaluate_skill_gaps` -> `job_readiness_score` = JRS |
| Capability | `capability` | `05 compute_feed_job_score` -> `sub_metrics.s_cap_capability` |
| Pay upside | `pay` | `05` -> `sub_metrics.s_wage_upside` |
| Location | `location` | `05` -> `sub_metrics.s_loc_location` |
| Freshness | `freshness` | `05` -> `sub_metrics.s_rec_recency` |

The 8 values are shown part by part. They are never added up.

### 4.2 "Your path to this job" (radar with 2 layers)

The radar has one axis for each skill group that the job asks for, and the axes `experience`, `level` and `certifications` (only if the job lists one).
The layer "Job requires" is the `required` value. The layer "You have" is the `have` value. The equations are in `02_FORMULAS_MATHEMATICAL_SPEC.md`, section 4.
The panel also shows the fit list, the gap list (with `months` and `must`) and the summary (`fitCount`, `gapCount`, `monthsToClose`, `readinessTier`).

**There is no 12-month line chart.** The version 1 curves $SMF(t)$ and $GSI(t)$ are removed. The months of each gap come from the taxonomy (`monthsToLearn`, `prepMonths`), from the level difference and from the years.

### 4.3 Compare jobs (2 to 5 jobs)

One polygon for each job on the 8 axes of 4.1. A table of pairs gives, for each pair of jobs, `job_proximity_index` and its parts:
taxonomy ($S_{\text{tree}}$), requirements ($S_{\text{req}}$), salary ($S_{\text{comp}}$), sector ($S_{\text{sec}}$), place ($S_{\text{geo}}$) and level ($S_{\text{lvl}}$).

### 4.4 Compare profiles (employer, Premium, 2 to 5 profiles)

For one chosen job, each profile has one polygon. The axes are values of one profile for one job, never a total:

| Axis | Source |
| :--- | :--- |
| Skills for this job (coverage) | `06` -> `skill_coverage` |
| Requirement fit | `06` -> `sub_metrics.s_req_fit` |
| Seniority fit | `06` -> `sub_metrics.s_sen_parity` |
| Certification readiness | `06` -> `sub_metrics.s_reg_readiness` |
| Skill depth | `04` -> `sub_metrics.skill_depth` |
| Experience | `04` -> `sub_metrics.experience_maturity` |
| Level standing | `04` -> `sub_metrics.level_standing` |
| Evidence | `04` -> `sub_metrics.evidence_rigor` |
| Transferable skills | `04` -> `sub_metrics.transferable_agility` |

The page also shows the positions inside one area (never added up) and a per-skill table of levels. It shows no total and no ranking of people.

---

## 5. Application lifecycle (unchanged)

```
[1. SUBMITTED] -> [2. CV_SCANNING] -> [3. UNDER_REVIEW] -> [4. SHORTLISTED] -> [5. INTERVIEW] -> [6. FINAL_ASSESSMENT] -> [7. OFFER] -> [8. HIRED]
Any stage by the employer -> [REJECTED].  Any stage before the offer by the talent -> [WITHDRAWN].
```

Each stage records the checkpoint, the time, the actor (`Candidate`, `Employer` or `System`) and a note.

---

## Appendix A. Database of the prototype in `backend/` (version 1, not changed)

The product `jinder_platform` has its own schema (`jinder_platform/jinder/schema.sql`, `jinder_platform/docs/DATABASE.md`). The tables below belong to the earlier prototype.

```sql
CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT, role TEXT NOT NULL CHECK(role IN ('seeker', 'hr', 'admin')),
                    auth_provider TEXT NOT NULL DEFAULT 'local', google_sub TEXT UNIQUE, terms_version TEXT NOT NULL, terms_accepted_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE seeker_profiles (id TEXT PRIMARY KEY, alias TEXT UNIQUE NOT NULL, legal_name TEXT NOT NULL, phone TEXT, origin_country TEXT NOT NULL,
                              current_title TEXT NOT NULL, years_experience REAL NOT NULL, highest_education TEXT, target_anzsco_code TEXT NOT NULL,
                              target_anzsco_title TEXT NOT NULL, preferred_location TEXT NOT NULL DEFAULT 'Sydney', cv_file_name TEXT, cv_raw_text TEXT,
                              profile_completeness REAL NOT NULL DEFAULT 85.0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE seeker_skills (id TEXT PRIMARY KEY, seeker_id TEXT NOT NULL, skill_name TEXT NOT NULL, skill_type TEXT NOT NULL CHECK(skill_type IN ('Direct', 'Transferable')),
                            evidence_quote TEXT, source TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE jobs (id TEXT PRIMARY KEY, employer_id TEXT, title TEXT NOT NULL, company TEXT NOT NULL, short_description TEXT NOT NULL, full_description TEXT NOT NULL,
                   location TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL, category TEXT NOT NULL, anzsco_code TEXT NOT NULL, anzsco_title TEXT NOT NULL,
                   employment_type TEXT NOT NULL DEFAULT 'Full-time', salary_min REAL NOT NULL, salary_max REAL NOT NULL, salary_display TEXT NOT NULL,
                   requirements_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', posted_at TIMESTAMP NOT NULL, expires_at TIMESTAMP NOT NULL);
CREATE TABLE applications (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, seeker_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'submitted',
                           overall_score_snapshot REAL NOT NULL, anzsco_match_snapshot REAL NOT NULL, skill_gap_snapshot REAL NOT NULL, tss_score_snapshot REAL NOT NULL,
                           message_to_employer TEXT, share_gaps_consent INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
```

The prototype tables for hr profiles, impressions, clicks, saved jobs, ignored jobs, job reports, timeline events and the compare tray are as in version 1.
The prototype stores a snapshot of the scores of Formulas 1, 2, 5 and 6 on each application. This is not done in the product: the employer never gets a score on a person.
