# Formulas: what changed (Jinder V2, wave 2)

Owner: Formulas agent. This file is for the BE agent (to rewrite `engine_bridge.py` and `catalogue.py` without reading the formulas) and for the Docs agent.
The math is in `jinder_backend_engine/docs/02_FORMULAS_MATHEMATICAL_SPEC.md` and in `jinder_backend_engine/intelligence_engine/0N_*.md`. Text is written in simple English.

## 1. Short summary

* The six formula files were rewritten in place. The file names, the main function names and the main result keys stay. New keys were added. The old dictionary shapes still work.
* A new helper file `intelligence_engine/engine_common.py` sits in the same folder. **It must stay next to the formula files.** The formula files load it, and they load each other, by file path. The bridge does not need to do anything for this: `_load("f5")` still works.
* The engine reads the taxonomy (`../data/reference/ict_taxonomy.json`) itself. The bridge does not pass skill names, aliases or `monthsToLearn`. Names and aliases are matched in any case. If the file is missing, the engine uses simple defaults and still runs. (The environment variable `JINDER_TAXONOMY_PATH` can give another path.)
* All score math is in the engine. The platform only builds dictionaries and calls functions.
* The product **fit** is now defined in the engine: `01.evaluate_job_fit(talent, job)["fit"]` (0 to 100, one decimal, continuous).
* The statutory block (AHPRA, CPA) is gone. The 12-month projection is gone. `has_statutory_blocker` is always `false`.
* No score reads a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo. The employer side (Formulas 4 and 6) never reads the CV text.

## 2. Two rules from the lead (applied)

1. **Pay units.** A job pay has the unit `year`, `day` (6 contract jobs in the data) or `hour`. The engine changes it to AUD per year in **one** function, `03_job_to_job_comparison.annual_salary(min, max, unit) -> (yearly min, yearly max)`:
   year x 1, **day x 220 working days**, **hour x 1950 hours**. Formulas 3 and 5 use it (through `prepare_job`). The bridge can call it at seed time.
   **Do not convert twice.** Either store the yearly amount (and send `salary_unit` "year" or nothing), or send the original amount with its `salary_unit`. If no unit is given, the engine guesses from the size of the number
   (a maximum below 500 is an hourly rate, from 500 to 3999 a day rate, more is a yearly pay), so a yearly amount is never changed.
2. **Education is a soft factor.** A missing "Bachelor's degree" or "Doctorate (PhD)" lowers one small part (weight 0.03 of the fit; the part is never below 0.2). It never gives 0 and it is never a hard limit.

## 3. Loading (no change)

```python
f1 = _load("f1")    # 01_skill_matching_model.py   ... f6 = 06_recruiter_candidate_ranking.py
```

The files can be loaded in any order. `f1.C` is the common module (`prepare_candidate`, `prepare_job`, `get_taxonomy`, `annual_salary`, `salary_benchmark`).
Speed: one pair (talent, job) costs about 0.7 ms for one function. The 2,500 pairs of the demo data take 2 to 4 seconds for the fit and the feed together.
A job or a talent that has been cleaned once (`f1.C.prepare_job(job_dict)`, `f1.C.prepare_candidate(cand_dict)`) can be sent again to any function: a prepared dictionary is used as it is.

## 4. Input dictionaries

All keys are optional. A missing key has a safe default.

### 4.1 Talent (`candidate`)

| Key | Type | Notes |
|---|---|---|
| `id`, `alias` | text | The alias is the only name that a result can have (`candidate_name`) |
| `level` | Intern, Junior, Mid, Senior, Lead, Principal | If missing: the title words, then the years. `level_rank` (0 to 5) also works |
| `years_experience` | number | Exact years (`yearsExperience`), else the middle of the band. `0` is a real value; use `None` for "not known" |
| `domain`, `specialisation` | text | `domain` = `profile.industry` (one of the 3 domains). If missing: the domain with the most skills |
| `current_title`, `target_roles` (list), `target_anzsco_code` | text | The engine finds the taxonomy occupation from the code, then from the titles (the taxonomy `roles`). **The bridge does not need `OccupationIndex` any more.** Send the target roles as they are |
| `highest_education`, `field_of_study` | text, list | e.g. "Bachelor's degree", ["Computer science"]. `None` or `""` counts as no qualification |
| `skills` | list of `{skill_name, name, skill_type, level, years, last_used_year}` | `level` 1 to 5 (default 3). `years` is optional. A skill can also be a text |
| `certifications` | list of `{name, issuer, year}` | The name is matched to the taxonomy in any case, with aliases and with "-" or an en dash |
| `awards` | list of `{name, kind, year}` | `kind` is an award kind of the taxonomy |
| `preferred_location`, `locations`, `work_modes`, `work_types` | text, list, list, list | Cities of the taxonomy. A city "Remote" means that the talent wants remote work |
| `cv_raw_text` | text | **Talent screens only, and only as a fallback when `skills` is empty.** Never send it for an employer |

For an employer call (Formulas 4 and 6) the engine ignores `cv_raw_text` and any evidence line. The bridge should still not send them (`private=False`).

### 4.2 Job

| Key | Type | Notes |
|---|---|---|
| `id`, `title`, `company` | text | |
| `category` | text | The domain (one of the 3) |
| `specialisation`, `level` | text | |
| `min_years`, `max_years` | number or null | A minimum with no maximum is open-ended. No years at all: the typical years of the level |
| `city`, `location`, `work_mode`, `type` | text | `city` is a taxonomy city or "Remote". `work_mode` is Onsite, Hybrid or Remote. `type` is Full-time, Part-time, Contract or "Graduate / Internship" |
| `anzsco_code`, `anzsco_title` | text | |
| `salary_min`, `salary_max`, `salary_unit` | number, number, text | See section 2, rule 1 |
| `required_skills` | list of `{name, level, must}` | `skills` as names also works. Send `requirements` (names) too for the old code |
| `certifications_required`, `certifications_preferred` | list of names | |
| `awards_preferred` | list of award kinds | |
| `education_min` | text | A soft factor |
| `days_old` | number | Age in days. Send `days_old`, not `posted_at` (the engine would use the real clock) |

## 5. Functions, results and how to call them

### 5.1 Formula 1: `01_skill_matching_model.py`

| Function | Result keys (new keys marked +) |
|---|---|
| `evaluate_job_fit(candidate, job, weights=None)` + | `fit` (0 to 100, one decimal), `fit_exact`, `parts` (skills, methods, occupation, level, experience, domain, location, work_type, education, certifications; each 0 to 100 or null), `weights`, `bonus` (certifications, awards), `skill_breakdown`, `skill_coverage`, `counts`, `level`, `years`, `certifications`, `awards`, `occupation`, `candidate_id`, `job_id` |
| `evaluate_skill_match(candidate, job_or_code, weights=(0.25, 0.5, 0.25))` | old keys: `candidate_id`, `target_anzsco_code`, `target_anzsco_title`, `sub_metrics` (`s_tree_taxonomy`, `s_direct_competency`, `s_trans_methodology`, `phi_experience_multiplier`, + `s_level_fit`, `s_years_fit`), `competency_breakdown`, `base_composite_score`, `final_match_score`, `overall_score`, `match_tier`, `match_tier_code`, `is_direct_ready`; + `skill_breakdown`, `skill_coverage`. The 2nd argument can be a job dictionary (send the whole job) or a 6-digit code |

`skill_breakdown` item: `name`, `group`, `kind` (hard, method, soft), `must`, `need_level`, `have_level` (null if not held), `have_effective`, `credit` (0 to 1.12), `weight`, `status` (`meets`, `below`, `related`, `missing`), `related` (`{name, level}` or null), `related_count`, `rarity`, `months`.
Use `status` for the per-skill match of both sides: `meets` = match, `below` and `related` = partial, `missing` = gap. `have_level` and `need_level` give the levels for the employer compare matrix.
`skill_coverage` (0 to 100, one decimal) is the level-aware coverage. The platform may keep its own integer coverage.

```python
r = f1.evaluate_job_fit(cand, jd)
fit, items = r["fit"], r["skill_breakdown"]
```

### 5.2 Formula 2: `02_skill_gap_analysis.py`

| Function | Result |
|---|---|
| `evaluate_skill_gaps(candidate, job, explicit_missing_skills=None)` | old keys: `total_gaps_count`, `classified_gaps`, `gap_severity_index`, `skill_gap_pct`, `job_readiness_score`, `estimated_bridge_months`, `estimated_closing_months`, `has_statutory_blocker` (false), `readiness_tier`, `readiness_tier_code`; + `gaps` (same list), `strengths`, `months_to_close`, `learner_factor`, `adaptation_friction` |
| `evaluate_path(candidate, job)` + | exactly the `path` object of V2_PLAN section 5.3 |

Gap item: `kind` (`missing`, `below_level`, `experience`, `level`, `certification`), `item` (and `skill`), `have_level`, `need_level`, `months`, `must`, `note`, `severity_points`, and the old keys (`gap_name`, `category_code`, `category_name`, `weight`, `duration_months`, `is_statutory_blocker`).
The old category codes mean now: `CAT-1` certification, `CAT-2` required skill, `CAT-3` nice-to-have skill, `CAT-4` experience or level. Strength item: same keys (`kind`: skill, experience, level, certification, award).
Path: `axes` (`key`, `label`, `group`, `required`, `have`, `status` fit / above / gap), `fit`, `gaps`, `summary` (`fitCount`, `gapCount`, `monthsToClose`, `readinessTier`). For the axes `experience`, `level` and `certifications`, `group` has the same text as `key`.
The path is plain JSON. Put it in `bridge.path` as it is.

### 5.3 Formula 3: `03_job_to_job_comparison.py`

| Function | Result |
|---|---|
| `compare_two_jobs(job_a, job_b, weights=(0.20, 0.34, 0.12, 0.08, 0.14, 0.12))` | `job_a`, `job_b`, `job_proximity_index`, `sub_metrics` (`s_tree_taxonomy`, `s_req_jaccard`, `s_comp_salary_parity`, `s_sec_sector_affinity`, `s_geo_alignment`, + `s_level_proximity`), `differentials` (`salary_delta_aud`, `salary_delta_label`, + `level_delta`, `shared_competency_sample`, + `unique_to_a_sample`, `unique_to_b_sample`), `operational_tier`, `career_mobility_advice` |
| `compare_multiple_jobs(jobs)` | `pairwise_proximity_matrix` (symmetric) and `baseline_comparisons_vs_first_job` |
| `get_job_salary_midpoint(job)` | yearly middle of the pay (AUD) |
| `annual_salary(min, max, unit)` + | `(yearly min, yearly max)` |

For the compare `parts` list add a sixth part `level` from `sub_metrics.s_level_proximity` (it can be null). The index is symmetric.

### 5.4 Formula 4: `04_candidate_benchmarking.py`

| Function | Result |
|---|---|
| `calculate_candidate_merit_score(cand, weights=..., job=None)` | `relative_merit_score` (never show it), `sub_metrics`: old `skill_depth`, `experience_maturity`, `evidence_rigor`, `transferable_agility`, `education_bonus`, `gap_penalty_deduction` (0); + `level_standing`, `certification_strength`, `award_strength`, `skill_breadth`, `education_level`; + `depth_basis` ("profile" or "job") |
| `compare_two_candidates(a, b, job=None)`, `rank_candidate_cohort(list, job=None)` | as before |

Send the **shared** profile only. Pass `job=` when the compare page has a chosen job: then `skill_depth` is the mean level of the skills that the job asks for. The platform shows the dimensions, never the total.
Suggested areas for the employer compare: Skill depth, Experience, Level standing, Evidence, Transferable skills, Certifications (`certification_strength`), Awards (`award_strength`), Qualification (`education_level`).

### 5.5 Formula 5: `05_job_seeker_ranking_feed.py`

| Function | Result |
|---|---|
| `rank_job_feed_for_candidate(candidate, jobs, top_limit=50)` | `top_feed`: one item for each job, with `job_id`, `feed_ranking_score` (one decimal, after the employer diversity penalty), `frs_exact`, `sub_metrics` (`s_cap_capability`, `s_wage_upside`, `s_loc_location`, `s_rec_recency`, `employer_diversity_penalty`, + `capability_smf`, `capability_readiness`, `capability_level_years`), `feed_position` |
| `compute_feed_job_score(candidate, job, same_employer_count_ahead=0)` | one item, without the list-level penalty |

Call `rank_job_feed_for_candidate` with **all open jobs** of the list, as now (`eb.feed_scores`). A single job in a list gets no diversity penalty, so the score of a job in `GET /jobs/:id` can differ from its score in the list.
To keep them equal, rank all open jobs and pick the one (the feed takes about 1 ms for each job).

### 5.6 Formula 6: `06_recruiter_candidate_ranking.py`

| Function | Result |
|---|---|
| `compute_talent_search_score(candidate, job)` | `talent_search_score`, `tss_exact`, `sub_metrics` (`s_req_fit`, `s_sen_parity`, `s_evid_rigor`, `s_reg_readiness`, `s_audit_contract`, + `s_level_fit`, `s_years_fit`, `s_skill_credit`), `skill_coverage`, `skill_breakdown`, `order_value`, `target_years_demanded`, `candidate_years_held`, `statutory_note`. **`candidate_origin` is removed** |
| `rank_candidates_for_job_requisition(job, pool, top_limit=20)` | `ranked_shortlist` |

`order_value` = `0.6 x skill_coverage + 0.4 x TSS` (not rounded). The platform order can use it, or its own coverage: `0.6 x coverage + 0.4 x talent_search_score`. Never send a score to an employer.
The label of the axis `s_reg_readiness` is now "Certification readiness" (not "Licence readiness").

## 6. How `fit` and the 8 axes of "How this job fits you" are obtained

| What | From |
|---|---|
| `match.score` of a job card | `round(0.55 x fit + 0.45 x FRS*, 1)`. `fit` = `evaluate_job_fit(...)["fit"]`. FRS = `feed_ranking_score` of the feed of all open jobs. FRS* = after `behavioural_adjust` (stays in the bridge) |
| `bridge.axes` (8 values, one decimal) | `occupation` = `evaluate_skill_match(...)["sub_metrics"]["s_tree_taxonomy"]`, `skills` = `s_direct_competency`, `methods` = `s_trans_methodology`, `readiness` = `evaluate_skill_gaps(...)["job_readiness_score"]`, `capability` = F5 `sub_metrics.s_cap_capability`, `pay` = `s_wage_upside`, `location` = `s_loc_location`, `freshness` = `s_rec_recency` |
| `bridge.path` | `evaluate_path(cand, job)` |
| `bridge.score` | `match.score` |
| `bridge.occupation` | `alignment` = `evaluate_skill_match(...)["final_match_score"]`, `tier`, `tierCode` from `match_tier`, `match_tier_code` |
| `bridge.readiness` | `readiness` = `job_readiness_score`, `gapSeverity` = `gap_severity_index`, `months` = `estimated_bridge_months`, `tier`, `tierCode`; `statutoryBlocker` is always false |
| `bridge.gaps` (kept for compatibility) | from `classified_gaps`: `name` = `gap_name`, `category`, `categoryName`, `months` = `duration_months`, `blocker` (false) |

The keys of the 8 axes are the same as before, so `JOB_FIT_AXES` and `job_fit_axes` need no change. The 8 axes are not totals and are not added up.

Text rule: every text that a result returns for a user (tier names, `career_mobility_advice`, gap and path `note`, `statutory_note`, verdicts) says "you" or "talent". It never says "job seeker", "candidate" or "applicant" (a test checks this). Keys such as `candidate_id` stay.

## 7. What changed against the old behaviour

| Area | Before | Now |
|---|---|---|
| Steps | many (capability 95/82/68/32, location 100/82/58/38, occupation 10 for an unknown code) | none: smooth functions. Unknown code: the title, the skills, the specialisation and the domain still give a value |
| Skills | text match with a fixed IDF table | per skill: credit from the levels (partial credit below the level, a small bonus above, related skills through `related`), weight by `must` (x2) and `rarity` |
| Level and years | title words and a multiplier | level rank fit (asymmetric: a step up costs more), years fit against `min_years` and `max_years` |
| Gaps | text rules, 4 categories, statutory | per skill, level, experience and certification; months from `monthsToLearn`, the level difference and `prepMonths`; the parallel rule (max + 0.18 x the rest) stays |
| Readiness | 100 - GSI, cap 5 and 95 | $100 e^{-S/70}$, no floor and no cap |
| Wage | one benchmark for each sector, floor 20 | benchmark for each domain and level, logistic, no floor |
| Location | 4 steps | city distance and work mode; Remote = 100 for everyone |
| Pay unit | hourly only | year, day (x 220), hour (x 1950) in `annual_salary` |
| Merit and TSS evidence | CV text length and numbers in the text | skill levels, years with a skill, certifications and awards. The CV text is not read |
| TSS seniority | words in the job title | level rank and exact years |
| TSS audit part | constant 100 | completeness of the shared profile |
| Privacy | names in some results, `candidate_origin` | the alias only. No private key is read (tests check this) |

## 8. Needs from BE (wave 4)

1. `engine_bridge.candidate_dict`: build the keys of section 4.1 (`level`, exact `years_experience`, `skills` with `level` and `years`, `certifications`, `awards`, `target_roles`, `domain`, `specialisation`, `field_of_study`, `work_modes`, `work_types`). Remove the use of `OccupationIndex` for the engine (keep it only if something else needs it). For the employer side use the shared profile only (no `cv_raw_text`, no evidence).
2. `engine_bridge.job_dict`: build the keys of section 4.2. Use `required_skills` with levels. Send `days_old`. Convert the pay: use `annual_salary` once (see section 2).
3. Replace `smf`, `gap_analysis` calls: `gap_analysis(cand, job, [])` is enough (the engine finds the gaps itself). Remove `projection` and `bridge.projection`. Add `bridge.path = f2.evaluate_path(cand, job)`.
4. `catalogue.TalentContext.fit`: take `fit` and the per-skill statuses from `evaluate_job_fit`. Keep the reasons text in the platform. Use `fit` (one decimal) and `feed_ranking_score` (one decimal): `round(0.55 * fit + 0.45 * frs, 1)`. This is the combination that `tests/test_differentiation.py` checks.
5. Remove `_friendly_gap` rules for AHPRA and CPA and the test `test_a_statutory_gap_is_found_for_a_nurse_job` (it was replaced by the new tests of this agent).
6. `routes/recruiter.py`: `_order_value` can use `compute_talent_search_score(...)["order_value"]`. `_radar_values` keeps the F6 keys; the F4 keys `skill_depth`, `experience_maturity`, `transferable_agility` stay and there are new ones (`level_standing`, `evidence_rigor`, `certification_strength`, `award_strength`). The axis "Licence readiness" becomes "Certification readiness". Remove `_areas` (legacy).
7. The seed: store the level, years, skill levels, certifications and awards from `data/synthetic`. A pay with the unit `day` must reach the engine as a yearly pay (section 2).
8. Keep a platform-level privacy test: the old test `test_formulas_use_no_sensitive_field` (the keys of `TalentContext.engine_candidate` have no name, email, origin, country, nationality, visa, gender, age, birth, phone or photo) was removed with the old `test_formulas.py`. The engine-level privacy tests are in the new `test_formulas.py` (`PrivacyTests`: private keys change no result, and the engine code reads no private key).
9. The test `tests/test_radar.py` expects the F4 and F6 axis keys of version 1. Keep them or change the test.

## 9. Differentiation numbers (`data/synthetic`, 50 jobs, 50 talents)

Score = `round(0.55 x fit + 0.45 x FRS, 1)` with `fit` and `FRS` at one decimal, no behaviour data.

| Check | Target | Result |
|---|---|---|
| Different scores in the top 20, each talent | 18 or more (plan section 9, relaxed by the lead) | min 19, mean 19.50 |
| Best minus worst, each talent | 30 or more | min 45.4, mean 55.5, max 67.6 |
| Radar axes with one value for all jobs | 0 | 0 of 400 |
| Exact ties in the top 10 of `0.6 x coverage + 0.4 x TSS`, each job | 2 or fewer | max 1 |
| Near-twin jobs with the same score for a talent | 0 | 0 (the smallest difference is 0.2) |

The target is 18 different scores in the top 20 for every talent. With one decimal, equal scores can happen by chance: for a top-20 range of about 40 points, each talent has a chance of about 10% to have two equal pairs.
The weights of the fit (Formula 1) and of the feed (Formula 5) were chosen inside fixed limits. With the combination above, all 50 talents have 19 or more (25 talents have exactly 19).
If the BE agent rounds in a different way (for example `fit_exact`, or two decimals for FRS*), or if the data changes, 2 to 4 talents can have 17 or 18 different scores. The result then still holds for most talents, and the test target is 18.
The weights are in `FIT_WEIGHTS` (file 01) and `DEFAULT_WEIGHTS`, `CAP_WEIGHTS`, `WAGE_SLOPE`, `RECENCY_RATE` (file 05).
There is no list-level step that spreads equal scores (decision of the lead). If the test fails after a change, tell the Formulas agent.

**Demo data caveat.** These values are demo assumptions, not statistics: the pay benchmarks (130000 Software Engineering, 150000 AI & Machine Learning, 125000 Data, for Mid, AUD per year), the +22% pay step for each level,
the 220 working days for a day rate, the assumed credit for a method or soft skill that a talent did not list, and the weights. They are listed in `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, section 9.

## 10. Files

Changed: `intelligence_engine/01_` to `06_*.py`, the six `.md` files, `MASTER_PLAN.md`, `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, `docs/04_DATA_AND_SCORING_SPEC.md`, `run_verification.py`, `jinder_backend_engine/README.md`, `tests/test_formulas.py`, `tests/test_differentiation.py`.
New: `intelligence_engine/engine_common.py`, this file.
**`engine_common.py` must stay in the same folder as the six formula files.** The formula files load it by path. `run_verification.py` and the legacy `backend/scores.py` import the formula files, so they use it too. The platform bridge needs no change for it.
`formulas_presentation.html`: not rewritten. A note at the top says that its slides show version 1.
