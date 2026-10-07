# Formula Architecture Detail: Jinder Intelligence Engine

> **Code:** `jinder_backend_engine/intelligence_engine/` (`01_` to `06_*.py`, `engine_common.py`)
> **Platform caller:** `jinder_platform/jinder/engine_bridge.py`
> **Short math reference:** `jinder_backend_engine/docs/02_FORMULAS_MATHEMATICAL_SPEC.md`
> **Product rules:** `jinder_platform/docs/FORMULAS_IN_THE_PRODUCT.md`

This document describes the six formulas (F-01 to F-06) as the code implements them.
Each statement names the file that holds it. If this document and the code differ, the code is correct.

**Names.** Each formula file has a model name, and the model computes a score with its own name: F-01 SMF (SMF, fit) · F-02 SGF (GSI, JRS) · F-03 JJF (JPI) · F-04 CCF (RMS) · F-05 JFR (FRS) · F-06 TSR (TSS). This document uses the score names.

---

## 1. Pipeline

![Intelligence engine pipeline](diagrams/04_intelligence_engine_pipeline.png)

Diagram source: [`diagrams/04_intelligence_engine_pipeline.html`](diagrams/04_intelligence_engine_pipeline.html).

The pipeline has five steps:

1. **Inputs.** The platform reads the Talent profile, the job and its `job_skills`, and the taxonomy.
2. **Dictionaries.** `engine_bridge.py` builds one talent dictionary and one job dictionary. It does no score math.
3. **Shared analysis.** `engine_common.prepare_candidate` and `prepare_job` clean the dictionaries. `01_skill_matching_model.analyse()` computes the parts that F-01, F-02, F-05 and F-06 all use.
4. **Formulas.** The six formula files compute their scores. Each score is from 0 to 100.
5. **API.** The routes cut the results down to what each side may see. Nothing is written to the database.

### 1.1 Which formula uses which

| Formula | Reads the result of | Called by (platform) |
|---|---|---|
| F-01 | `analyse()` | `catalogue.TalentContext` → `eb.job_fit`; `catalogue.formula_values` → `eb.smf` |
| F-02 | F-01 `analyse()` | `catalogue.formula_values` → `eb.gap_analysis`; `catalogue.bridge_for` → `eb.path` |
| F-03 | F-01 `code_closeness`, `_anchor_closeness` | `catalogue.similar_jobs`, `routes/jobs.jobs_compare` → `eb.proximity` |
| F-04 | F-01 `effective_level`, `requirement_weight` | `routes/recruiter._metrics` → `eb.merit_dimensions` |
| F-05 | F-01 `analyse()`, `smf_from_analysis`; F-02 `gaps_and_strengths` | `catalogue.TalentContext._analyse_open` → `eb.feed_scores` |
| F-06 | F-01 `analyse(shared_only=True)`; F-04 strengths | `routes/recruiter._card`, `_metrics`; `routes/applications.snapshot_match` → `eb.talent_score` |

`routes/platform.py` calls `eb.engine_status()` only. The health check uses it to report which formula files load.

---

## 2. Inputs

### 2.1 Talent (`engine_bridge.candidate_dict`, `shared_candidate_dict`)

| Key | Source |
|---|---|
| `skills` (name, level 1 to 5, years) | The translated skills. A skill with no level set gets its level from the evidence: Strong 4, Moderate 3, Limited 2. Else it gets 3 (`store.EVIDENCE_LEVEL`, `store.DEFAULT_SKILL_LEVEL`). |
| `level` | The level of the profile. If it is empty, the engine reads level words in the title, then estimates a rank from the years. |
| `years_experience` | The exact years. Else the middle of the band, for example "3–5 years" gives 4.0 (`reference.YEARS_MIDPOINT`). |
| `domain`, `specialisation` | `profile.industry` and the specialisation. |
| `highest_education`, `field_of_study` | The highest qualification, by AQF level. |
| `target_roles`, `target_anzsco_code` | The target roles. The bridge finds the code from the first role. |
| `certifications`, `awards` | Lists with name, issuer or kind, and year. |
| `preferred_location`, `locations`, `work_modes`, `work_types` | The goals of the Talent. "Remote" as a place means that the Talent wants remote work. |
| `cv_raw_text` | Talent screens only, and only when the skill list is empty. |

There are two talent dictionaries:

- `candidate_dict(private=True)` is for the Talent's own screens. It holds the whole profile.
- `shared_candidate_dict()` is for Employer screens. It holds the shared profile only. It has no CV text and no evidence lines.

`engine_common.prepare_candidate(shared_only=True)` also refuses to read any CV text.

### 2.2 Job (`engine_bridge.job_dict`)

- `required_skills`: `[{name, level, must}]` from `job_skills`.
- `level`, `min_years`, `max_years`, `specialisation`, `work_mode`, `city`, `type`.
- `salary_min`, `salary_max`, `salary_unit`. The bridge sends the pay as stored.
- `certifications_required`, `certifications_preferred`, `awards_preferred`, `education_min`.
- `days_old`: the age of the posting in days. With no posting date, the bridge sends 3.0.

The bridge adds a version 2 key only when the job has a value. A missing key gets a safe default in the engine.

### 2.3 Taxonomy (`jinder_backend_engine/data/reference/ict_taxonomy.json`)

| Content | Count |
|---|---|
| Skills (aliases, related skills, group, kind, `monthsToLearn`, `rarity`) | 172 |
| Occupations (ANZSCO-style 6-digit code, core skills) | 17 |
| Levels: Intern 0, Junior 1, Mid 2, Senior 3, Lead 4, Principal 5 | 6 |
| Domains: Software Engineering, AI & Machine Learning, Data | 3 |
| Skill groups: Languages, Frameworks & libraries, Cloud & DevOps, Data & storage, ML & AI, Engineering practices, Collaboration | 7 |
| Certifications (tier, `prepMonths`, evidence skills) | 38 |
| Award kinds | 12 |

People made this list by hand. It is not an official standard. Some codes are the nearest real ANZSCO code (`approximate: true`).
Name lookup is case-insensitive and uses the aliases.

---

## 3. Shared functions (`engine_common.py`)

| Name | Equation | Use |
|---|---|---|
| Saturation | $\text{sat}(x, a) = 1 - e^{-x/a}$ | merit areas, learner factor, gap severity |
| Logistic | $L(x) = 1 / (1 + e^{-k(x - m)})$ | wage upside (F-05, $k = 4.3$) |
| Exponential decay | $e^{-x/a}$, $e^{-b x^p}$ | level fit, years fit, distance, recency, pay closeness |
| Power credit | $(h/n)^{1.3}$ | a skill below the level |
| Weighted Jaccard | $\sum \min / \sum \max$ | occupation skills, job skill overlap |
| Linear interpolation | through control points | level rank from years (only when the level is not known) |

**Level rank.** A known level gives a whole rank from 0 to 5. With no level and no level word in the title, `Taxonomy.rank_from_years` gives a fractional rank.

**Yearly pay** (`annual_salary`): year × 1, day × 220, hour × 1950. With no unit, the size of the number decides. This is the only place that converts pay.

**Pay benchmark** (`salary_benchmark`): $B(d, r) = \text{base}(d) \cdot e^{0.20 (r - 2)}$.
The Mid base is 130000 (Software Engineering), 150000 (AI & Machine Learning) and 125000 (Data) AUD per year. These are assumptions, not statistics.

---

## 4. The formulas

Symbols: $h$ = the level that the Talent has, $n$ = the level that the job needs, $r_C$ and $r_J$ = level ranks, $Y$ = years.

### 4.1 F-01 Skill match (SMF) and product fit (`01_skill_matching_model.py`)

**Skill credit** (`skill_credit`):

$$c = \begin{cases} 1 + 0.12\,(1 - e^{-(h-n)/1.2}) & h \ge n \\ (h/n)^{1.3} & h < n \end{cases}$$

A missing skill with related skills gets $c = \min(0.55,\; 0.45\, r^{1.2} + 0.04\,(k - 1))$, with $r = \min(1, h_{\text{rel}}/n)$ and $k$ = the number of related skills held.
The credit is from 0 to 1.12.

**Skill weight** (`requirement_weight`): $u = m \cdot \rho^{0.6} \cdot (0.7 + 0.1\, n)$. $m = 2$ for a `must` skill, else 1. $\rho$ = rarity.

**Skill parts:** $S_{\text{direct}} = 100 \min(1, \sum u c / \sum u)$ over the hard skills.
$S_{\text{trans}}$ is the same over the method and soft skills. A method that the Talent did not list gets half the credit of an assumed level $0.5 + 0.3\, r_C$.
The methods of the job occupation count with weight × 0.4.

**Coverage:** $100 \sum u \min(1, c) / \sum u$ over the skills that the job lists.

**Level fit** (`level_fit`): $d = r_C - r_J$. $F_{\text{level}} = e^{-0.55 |d|^{1.2}}$ if $d < 0$, else $e^{-0.28\, d^{1.2}}$.

**Years fit** (`years_fit`), with $s = \max(1.5, 0.6\, Y_{\min})$:

- below the minimum: $0.92\, e^{-((Y_{\min} - Y)/s)^{1.4}}$
- inside the range: $0.92 + 0.08\,(Y - Y_{\min})/(Y_{\max} - Y_{\min})$
- above the maximum: $1 - 0.25\,(1 - e^{-(Y - Y_{\max})/6})$

**Occupation closeness $O$** (`occupation_closeness`): the weighted mean of five parts. The weights are code 0.26, core skills 0.22, title words 0.22, specialisation 0.16 and domain 0.14.
The code part is $e^{-0.26 (6 - c)^{1.3}}$, with $c$ = the number of equal leading digits. $O$ is the best value over the target roles (weight 1.0) and the current title (weight 0.85).

**Skill match:**

$$SMF = \min\left(100,\; (0.25\, S_{\text{tree}} + 0.50\, S_{\text{direct}} + 0.25\, S_{\text{trans}}) \cdot \Phi\right), \quad \Phi = 0.78 + 0.27\,(0.55\, F_{\text{years}} + 0.45\, F_{\text{level}})$$

$S_{\text{tree}} = 100\, O$. $\Phi$ is from 0.78 to 1.05.

**Product fit** (`fit_from_analysis`):

$$\text{fit} = \text{clip}_{0}^{100}\left(100 \frac{\sum w_i P_i}{\sum w_i} + 7\,(G - 0.45) + 3\,A\right)$$

| Part $P_i$ | skills | occupation | level | domain | experience | location | methods | education | work type |
|---|---|---|---|---|---|---|---|---|---|
| $w_i$ (`FIT_WEIGHTS`) | 0.39 | 0.16 | 0.10 | 0.10 | 0.09 | 0.07 | 0.04 | 0.03 | 0.02 |

- A part that does not apply to the job is left out. The other weights then grow to sum 1.
- $G$ = the certification credit. The term is 0 if the job lists no certification. It is from −3.15 (none held) to +3.85 (all held).
- $A$ = the award credit. It adds at most 3 points.
- Education is a soft factor: $0.2 + 0.8\, e^{-0.7 \cdot \text{steps}}$. It never gives 0.
- Location: Remote gives 1. Onsite gives $0.25 + 0.75\, e^{-d/700}$. Hybrid gives $0.40 + 0.60\, e^{-d/900}$ ($d$ in km). A work mode that the Talent did not choose gives × 0.9.

### 4.2 F-02 Gaps, readiness (JRS) and path (`02_skill_gap_analysis.py`)

**Months for one skill gap:**

$$T = \text{clip}\left(\tau\,(E(n) - E(h))\,(1 - 0.30 \min(1, c_{\text{rel}}/0.45))\,\lambda,\; 0.25,\; 18\right), \quad E(l) = (l/3)^{1.6}$$

$\tau$ = `monthsToLearn`. The learner factor is $\lambda = 1 - 0.16\,\text{sat}(Y, 8) - 0.012 \min(4, \text{education rank})$. It is from 0.792 to 1.00. (The docstring in the code says 0.80. The lowest value with education rank 4 is 0.792.)

**Other gaps:**

- Certification: $T = \text{prepMonths}\,(1 - 0.5\,k)\,\lambda$. $k$ = how well the Talent holds the evidence skills.
- Experience: $T = 14\,\text{sat}(\Delta Y, 2.2)$.
- Level: $T = \min(24,\; 6\,\Delta r^{1.1})$.

**Gap weights** (`GAP_WEIGHTS`): must skill 1.0, nice-to-have skill 0.45, required certification 0.90, preferred certification 0.35, experience 0.70, level 0.80.

**Readiness:**

$$S = \sum_k w_k\left(16\,\text{sat}(T_k, 2.5) + 3 \ln(1 + T_k)\right) + 6\,(1 - O), \quad JRS = 100\, e^{-S/70}, \quad GSI = 100 - JRS$$

Tiers: JRS 80 or more is Low Gap. JRS 55 or more is Moderate Gap. Less is High Gap.

**Months to close** (parallel rule): $T_{\text{total}} = \max T + 0.18\,(\sum T - \max T)$.

A missing required certification is a gap with months. It is not a block. `has_statutory_blocker` is always `false`.

**Path** (`evaluate_path`): one radar axis for each skill group that the job asks for.
"Job requires" $= \sum u \cdot n/5 \cdot 100 / \sum u$. "You have" $= \sum u \cdot \min(h, 5)/5 \cdot 100 / \sum u$.
The path also has the axes Experience ($\min(100, 10\,Y)$), Level ($100\, r/5$) and Certifications (only when the job lists one).
Status: `above` if have ≥ required + 15, `fit` if have ≥ required, else `gap`. The path also gives a Fit list, a Gap list and a summary.

### 4.3 F-03 Job proximity index (JPI) (`03_job_to_job_comparison.py`)

$$JPI = \frac{\sum_k w_k S_k}{\sum_k w_k}$$

| Part | occupation $S_{\text{tree}}$ | requirements $S_{\text{req}}$ | salary $S_{\text{comp}}$ | sector $S_{\text{sec}}$ | place and mode $S_{\text{geo}}$ | level $S_{\text{lvl}}$ |
|---|---|---|---|---|---|---|
| Weight (`DEFAULT_WEIGHTS`) | 0.20 | 0.34 | 0.12 | 0.08 | 0.14 | 0.12 |

- $S_{\text{tree}}$: the mean of the F-01 occupation closeness in both directions.
- $S_{\text{req}}$: the weighted Jaccard of the skills. Each skill weighs $n \cdot (1 \text{ or } 0.6) \cdot \rho^{0.3}$. A pair of related skills counts 0.4.
- $S_{\text{comp}} = 100\, e^{-|\ln(M_a/M_b)|/0.5}$ on the yearly pay midpoint.
- $S_{\text{sec}} = 50 \cdot \text{same domain} + 50 \cdot \cos(\text{domain shares of the two skill lists})$.
- $S_{\text{geo}} = 100 \cdot P_{\text{mode}} \cdot P_{\text{city}}$. $P_{\text{city}} = 0.25 + 0.75\, e^{-d/700}$, or 1 if a job is Remote.
- $S_{\text{lvl}} = 100\, e^{-0.45 |r_a - r_b|^{1.2}}$. It is left out if a level is not known.

The index is symmetric: JPI(A, B) = JPI(B, A). Tiers: 80 or more is "Directly Substitutable Role". 60 or more is "Adjacent Career Mobility". Less is "Cross-Disciplinary Career Pivot".

### 4.4 F-04 Merit areas (RMS) (`04_candidate_benchmarking.py`)

| Area | Equation |
|---|---|
| Skill depth (with a job) | weighted mean of $h/5$ over the skills that the job asks for (weight $u$) |
| Skill depth (no job) | $100\,\text{sat}(\sum (h/5)^{1.6} \rho^{0.4},\; 4.2)$ over the hard skills |
| Experience | $100\,\text{sat}(Y, 6.5)$ |
| Level standing | $100\,(r/5)^{0.9}$ |
| Evidence | $0.50 \cdot 100\,\text{sat}(Q, 5) + 0.30\,\text{Cert} + 0.20\,\text{Award}$, $Q = \sum (h/5)^2 (0.7 + 0.3 \min(1, y/4))$ |
| Transferable skills | $0.7 \cdot 100\,\text{sat}(M, 2.6) + 0.3 \cdot 100 \min(1, \text{groups}/7)$ |
| Certifications | $100\,\text{sat}(W, 1.8)$; tier weight foundation 0.5, associate 1.0, professional and specialty 1.6 |
| Awards | $100\,\text{sat}(\sum (0.6 + 0.4\, e^{-\text{age}/6}),\; 1.5)$ |
| Qualification level | education bonus, 0 to 5 points |

$$RMS = \min\left(100,\; 0.30\,D + 0.20\,E + 0.22\,V + 0.12\,T + 0.16\,L + \text{bonus}\right)$$

F-04 reads the shared profile only. It does not use the CV text or its length.
The code computes RMS, but the platform never sends it and never ranks people with it.

### 4.5 F-05 Feed ranking score (FRS) (`05_job_seeker_ranking_feed.py`)

$$FRS = \left(0.43\, S_{\text{cap}} + 0.21\, S_{\text{wage}} + 0.18\, S_{\text{loc}} + 0.18\, S_{\text{rec}}\right) \cdot (1 - \delta_{\text{div}})$$

- $S_{\text{cap}} = 0.53\, SMF + 0.27\, JRS + 0.20 \cdot 100\,(0.5\, F_{\text{level}} + 0.5\, F_{\text{years}})$ (`CAP_WEIGHTS`).
- $S_{\text{wage}} = 100\, L(z;\, k = 4.3)$, $z = 0.6 \ln(M / B(d, r_J)) + 0.4 \ln(M / B(d, r_C))$. A job with no pay gives 50.
- $S_{\text{loc}} = 100 \cdot$ the F-01 location fit (0.6 if not known).
- $S_{\text{rec}} = 100\, e^{-0.044\, D}$, $D$ = days since posting.
- $\delta_{\text{div}} = \min(0.40,\; 0.15\, k)$, $k$ = the jobs of the same employer above this job in the first ranking.

`rank_job_feed_for_candidate` ranks all jobs, applies the penalty, and ranks again. Ties are broken by the job id.

**Feedback loop** (`engine_bridge.behavioural_adjust`): FRS* = FRS × 1.10 for a saved employer, × 1.05 for a saved domain, × 0.75 after 3 skipped jobs of one employer. The result stays from 0 to 100.

### 4.6 F-06 Talent search score (TSS) (`06_recruiter_candidate_ranking.py`)

$$TSS = 0.44\, S_{\text{req}} + 0.25\, S_{\text{sen}} + 0.18\, S_{\text{evid}} + 0.08\, S_{\text{reg}} + 0.05\, S_{\text{audit}}$$

- $S_{\text{req}} = \min(100,\; 100\,(0.65\,K + 0.22\,O + 0.13\,D) + 3A + 2P)$. $K = \min(1, \text{mean credit}/1.05)$.
- $S_{\text{sen}} = 100\,(0.55\, F_{\text{level}} + 0.45\, F_{\text{years}})$. It uses the level rank and the years, not title words.
- $S_{\text{evid}}$: like the F-04 evidence, with $\text{sat}(Q, 4)$. A skill that the job does not ask for counts 0.55.
- $S_{\text{reg}}$: certification readiness. Required and preferred: $100\,(0.8R + 0.2P)$. Required only: $100R$. Preferred only: $100\,(0.7 + 0.3P)$. None listed: $90 + 0.10 \cdot$ certification strength.
- $S_{\text{audit}}$: the share of filled shared-profile fields. It reads no text.

**Order value:** $\text{order} = 0.6 \cdot \text{coverage} + 0.4 \cdot TSS$ (`ORDER_WEIGHTS`). The value stays on the server.

---

## 5. Where the product uses each formula

| Formula | Screen | What the user sees |
|---|---|---|
| F-01 | Job card, Job detail (Talent) | The Fit score (with F-05), per-skill status (meets, below, related, missing), coverage, reasons. Radar axes Occupation fit, Skills, Work methods. |
| F-02 | Job detail (Talent) | Readiness axis, readiness tier, gap list with months, "Your path to this job". |
| F-03 | Job detail, Compare (Talent) | Up to 3 similar jobs in JPI order, with a tier. On Compare: the index, the tier and 5 parts for each pair of jobs. |
| F-04 | Compare (Employer, Premium) | Radar axes Skill depth, Experience, Transferable skills, Level standing, Evidence. The position of each profile inside one area. |
| F-05 | Feed, search, bookmarks (Talent) | No number. It sets the order and is part of the Fit score. Radar axes Capability, Pay upside, Location, Freshness. |
| F-06 | Talent list, profile, applications, Compare (Employer) | The per-skill match and coverage. Radar axes Requirement fit, Seniority fit, Certification readiness. No number. |

### 5.1 Talent side (`catalogue.py`)

$$\text{match.score} = \text{round}(0.55 \cdot \text{fit} + 0.45 \cdot FRS^{*},\; 1)$$

- `FIT_WEIGHT = 0.55`, `FRS_WEIGHT = 0.45`.
- A job is recommended when the score is 45 or more (`RECOMMEND_MIN_SCORE`).
- F-05 ranks all open jobs together. So a job has the same score in every list and on its page.
- The lists have two sorts: Best match and Newest posted. Ties are broken by the job id.
- `GET /jobs/:id` returns `bridge` with `axes` (8), `occupation`, `readiness`, `gaps` and `path`.
- `GET /jobs/compare` takes 2 to 5 jobs. It returns the 8 axes for each job and the pairs.

### 5.2 Employer side (`routes/recruiter.py`)

- `GET /recruiter/candidates`: the talent list in order of the order value (sort "best"), or by the last update (sort "updated").
- A Basic plan sees the first 5 (`config.TOP_N`). The response gives the real total.
- `GET /recruiter/compare` (Premium): 2 to 5 profiles. It returns 9 radar axes (coverage, 3 from F-06, 5 from F-04). It keeps an axis only if all profiles have a value.
- `AREAS` gives the position of each profile in one F-04 area. Profiles within 3 points of the leader share its position (`AREA_TIE_BAND`).

---

## 6. Product rules

These rules come from `jinder_platform/docs/FORMULAS_IN_THE_PRODUCT.md`. The code applies them as follows.

1. **No single score on a person goes to an Employer.** The API never sends TSS, RMS, the order value or a rank number to an Employer. The Employer gets an order, the coverage and the per-skill match.
2. **No total in Compare.** The Employer Compare shows axes and per-area positions. The platform never adds the axes up.
3. **Scores are never stored.** The formulas run on each request. An application stores a snapshot of the shared profile and of the per-skill match (`match_json`: coverage and skill items). It stores no fit, FRS, TSS or RMS.
4. **No protected attributes.** No formula reads a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo (header of `engine_common.py` and of each formula file).
5. **Employer formulas read the shared profile only.** F-04 and F-06 get `shared_candidate_dict()`. They do not read the CV, the evidence lines or the CV length.
6. **A level is not a title word.** The seniority fit uses the level rank and the exact years.
7. **A missing certification is a gap, not a block.**
8. **Education is a soft factor.** Its weight in the fit is 0.03, and its value never goes below 0.2.

The Talent sees their own Fit score, readiness and path as a guide. Employers never see them.

---

## 7. Worked example

The numbers below come from a run of the code (Python 3.12, reference year 2026). The input is the F-01 self-check input of `01_skill_matching_model.py`.

**Talent:** level Mid, 4 years, domain Data, current title Data Analyst, city Sydney. Skills: SQL 4, Python 3, Tableau 3.
**Job:** Data Engineer, domain Data, level Mid, 3 to 6 years, Sydney, Hybrid. Skills: SQL 4 (must), Python 4 (must), Apache Airflow 3 (not must). No pay, no certification, no award.

**Per-skill match (F-01):**

| Skill | Need | Have | Status | Credit $c$ | Weight $u$ |
|---|---|---|---|---|---|
| SQL | 4 | 4 | meets | 1.000 | 2.200 |
| Python | 4 | 3 | below | $(3/4)^{1.3} = 0.688$ | 2.200 |
| Apache Airflow | 3 | none | related | 0.450 | 1.375 |

Coverage $= 100 \cdot (2.2 \cdot 1 + 2.2 \cdot 0.688 + 1.375 \cdot 0.45) / 5.775 = 75.0$.

**Parts (0 to 1):** skills 0.750, methods 0.136, occupation 0.282, level 1.000, experience 0.947, domain 1.000, location 1.000.
Work type and education do not apply, so the weights are divided by 0.95.

**Fit:** $100 \cdot (0.39 \cdot 0.750 + 0.04 \cdot 0.136 + 0.16 \cdot 0.282 + 0.10 + 0.09 \cdot 0.947 + 0.10 + 0.07) / 0.95 = 73.5$.

**SMF:** $(0.25 \cdot 28.2 + 0.50 \cdot 75.0 + 0.25 \cdot 13.6) \cdot 1.042 = 47.9 \cdot 1.042 = 50.0$.

**F-02:** gaps Python (1.6 months, severity 10.62) and Apache Airflow (1.3 months, severity 4.07). Friction $6 \cdot (1 - 0.282) = 4.31$.
$S = 19.0$. $JRS = 100\, e^{-19.0/70} = 76.2$ (Moderate Gap). $GSI = 23.8$. Months to close: 1.9.

**F-05:** $S_{\text{cap}} = 66.5$, $S_{\text{wage}} = 50.0$ (no pay), $S_{\text{loc}} = 100$, $S_{\text{rec}} = 54.0$ (no `days_old`, so the engine uses 14 days). $FRS = 66.8$.

**Platform score** (no saves or skips, so FRS* = FRS): $\text{round}(0.55 \cdot 73.5 + 0.45 \cdot 66.8, 1) = 70.5$. The job is recommended (70.5 ≥ 45).

**F-06** (same profile, seen by an Employer): $S_{\text{req}} = 65.6$, $S_{\text{sen}} = 97.6$, $S_{\text{evid}} = 11.2$, $S_{\text{reg}} = 90.0$, $S_{\text{audit}} = 63.6$. $TSS = 65.7$.
Order value $= 0.6 \cdot 75.0 + 0.4 \cdot 65.7 = 71.3$. The Employer sees only the coverage (75) and the per-skill status.

To run the self-checks of all six files:

```bash
cd jinder_backend_engine/intelligence_engine
python -B 01_skill_matching_model.py   # and 02_ to 06_
```

---

## 8. Tests

- `jinder_platform/tests/test_formulas.py`: properties of each formula, and that no private key changes a result.
- `jinder_platform/tests/test_differentiation.py`, `test_differentiation_platform.py`: the spread of the scores.
- `jinder_platform/tests/test_employer_flow.py::PrivacyTests`: no Employer response has a score or personal data.
- `python jinder_backend_engine/run_verification.py`: the formula self-check.
