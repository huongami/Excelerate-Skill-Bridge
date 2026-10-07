# Jinder Intelligence Engine - Master Plan (version 2)

> Mathematical model for the matching of talents and jobs in the ICT product: Software Engineering, AI & Machine Learning and Data.
> This file describes the architecture. The equations are in the six specification files (`01_` to `06_`) and in `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`.

---

## 1. Why version 2

The user said: "The jobs that are shown all have the same overall fit. There is no difference. Give detail to each job and each candidate, and rewrite the calculation formulas behind if needed."

The formulas of version 1 had fixed steps (for example, capability 95, 82, 68 or 32; location 100, 82, 58 or 38; a score of 10 for an unknown occupation code).
They also had eight occupations of other domains and a legal block for AHPRA and CPA. Many jobs got the same number.

Version 2 changes:

| Area | Version 1 | Version 2 |
| :--- | :--- | :--- |
| Scope | 8 sectors, ANZSCO occupations of health, finance, trade | 3 domains. All names come from `data/reference/ict_taxonomy.json` |
| Talent facts | skill names, years band | level (Intern to Principal), exact years, skill levels 1 to 5, years with each skill, certifications, awards, work mode |
| Job facts | skill names, title | level, minimum and maximum years, skill levels, must or nice, certifications (required and preferred), awards (preferred), work mode, specialisation, pay with unit |
| Scores | tiers and steps | smooth functions (exponential, logistic, saturation, linear interpolation) |
| Unknown values | one fixed number | the other facts (titles, skills, domain) give a value |
| Gaps | text rules, statutory blocker | per-skill gaps with months from `monthsToLearn`; certification gaps with months from `prepMonths`; no legal block |
| Path | 12-month projection | radar of "You have" and "Job requires", a fit list and a gap list |
| Employer view | CV text length gave evidence | evidence from skill levels, certifications and awards. The CV text is not read |

---

## 2. Architecture

```
                         data/reference/ict_taxonomy.json
                                      |
                              engine_common.py
        (taxonomy index, input cleaners, smooth functions, annual_salary, loader)
                                      |
   +----------------+-----------------+------------------+------------------+
   |                |                 |                  |                  |
01 Skill match   02 Gap and path   03 Job vs job     04 Merit areas     05 Feed rank    06 Talent search
 + product fit     (needs 01)        (needs 01)        (needs 01)       (needs 01, 02)    (needs 01, 04)
```

| File | Formula | Who uses it in the product |
| :--- | :--- | :--- |
| `01_skill_matching_model.py` | SMF and the product **fit** | Talent: job card score, "How this job fits you" (occupation, skills, methods) |
| `02_skill_gap_analysis.py` | SGF, readiness and `path` | Talent: "Your path to this job" (radar, fit list, gap list), readiness axis |
| `03_job_to_job_comparison.py` | JPI | Talent: similar jobs, compare jobs |
| `04_candidate_benchmarking.py` | merit areas | Employer: compare profiles area by area (Premium). No total is shown |
| `05_job_seeker_ranking_feed.py` | FRS | Talent: order of the feed (with the fit). No number is shown |
| `06_recruiter_candidate_ranking.py` | TSS | Employer: order of the talent list. No number is shown |

`engine_common.py` is not a formula. It loads the taxonomy, cleans the input dictionaries, and has the smooth functions.
The file names of the formulas start with a digit. A formula file uses another one through `engine_common.load_sibling`.

The product score is $\text{score} = 0.55 \cdot \text{fit} + 0.45 \cdot FRS^{*}$, where `fit` is from Formula 1 and $FRS^{*}$ is Formula 5 after the platform feedback loop.
The employer order is $0.6 \cdot \text{coverage} + 0.4 \cdot TSS$.

---

## 3. Rules that every formula follows

1. **Continuous.** No fixed step decides a score alone. A label (tier) may use thresholds, but the label does not change the number.
2. **Bounded.** Every score is from 0 to 100. Every part is from 0 to 100 (or from 0 to 1 inside the code).
3. **Deterministic.** The same input gives the same output. Ties are broken by the id.
4. **Private.** A formula reads skills, levels, years, roles, certifications, awards, places and work preferences. It never reads a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo.
5. **Shared profile on the employer side.** Formulas 4 and 6 never read the CV text or the evidence lines. The platform never shows a score on a person to an employer.
6. **Old shapes work.** A skill can be a text. A job can list `requirements` as text. A missing key has a safe default.
7. **Taxonomy optional.** If `ict_taxonomy.json` is missing, the engine uses simple defaults and still runs. A name is matched in any case, with its aliases.
8. **Explain each result.** Each score has parts. The parts are returned and they sum up to the score by the stated equation.

---

## 4. Tuning

The demo data is in `data/synthetic` (50 jobs and 50 talents). The acceptance targets (V2_PLAN section 9) are tests:

- For each talent, the top 20 jobs have 18 or more different scores (1 decimal).
- For each talent, best minus worst is 30 points or more.
- No radar axis of "How this job fits you" has the same value for all jobs.
- For each job, the order of the 50 talents has at most 2 exact ties in the top 10.

The weights of the fit and of the feed were chosen inside fixed limits so that the targets hold (see `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, section 9). The tests are `jinder_platform/tests/test_differentiation.py` and `run_verification.py`.

---

## 5. References

1. Bastian et al. (KDD 2014). LinkedIn Skills: Large-Scale Topic Modeling and Graph Analysis.
2. Peterson et al. (2001). Understanding Work Using the O*NET Content Model.
3. Le et al. (WWW 2019). Job2Vec: Learning Representations of Jobs for Career Path Modeling.
4. Borisyuk et al. (KDD 2016). LiJar: Latent Factor Models for Job Recommendations at LinkedIn.
5. Ramanath et al. (RecSys 2018). Two-Sided Marketplace Recommendations in Talent Acquisition.
6. Keeney and Raiffa (1993). Decisions with Multiple Objectives (multi-attribute utility).
7. Ruzicka similarity (weighted Jaccard) for the overlap of skills with levels.

The taxonomy is a demo list that people made by hand. It is not an official standard.
