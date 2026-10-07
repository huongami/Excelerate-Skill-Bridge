# TECHNICAL SPECIFICATION: TALENT JOB FEED RANKING MODEL (JFR)
**Document Number:** IE-SPEC-005 (version 2)  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `05_job_seeker_ranking_feed.py`

---

## 1. PURPOSE

This document gives the equations of the Feed Ranking Score (FRS).
The FRS says how good one job is for one talent as a place in the feed. It has a range from 0 to 100.
The platform never shows the FRS number. It uses the FRS (after the behaviour loop) together with the product fit:

$$\text{score} = 0.55 \cdot \text{fit} + 0.45 \cdot FRS^{*}$$

`fit` comes from `01_SKILL_MATCHING_MODEL.md`. $FRS^{*}$ is the FRS after the feedback loop of the platform (saved employer +10%, saved domain +5%, three skipped jobs of one employer -25%).
The feedback loop is made by the platform, not by this file.

Version 2 changes:
- The capability part uses the skill match, the readiness and the level and years fit. It is level-aware.
- The wage upside uses a benchmark for each **domain and level**. It has no floor and no cap.
- The location part uses the city distance and the work mode. A Remote job fits everyone.
- The pay of a job is changed to a yearly pay with `annual_salary` (day $\times$ 220, hour $\times$ 1950). See `03_JOB_TO_JOB_COMPARISON.md`, section 4.3.
- The employer diversity penalty stays.

---

## 2. THE MASTER EQUATION

$$FRS = \left(w_{\text{cap}} S_{\text{cap}} + w_{\text{wage}} S_{\text{wage}} + w_{\text{loc}} S_{\text{loc}} + w_{\text{rec}} S_{\text{rec}}\right) \cdot \left(1 - \delta_{\text{div}}\right)$$

| Weight | Value |
| :--- | :---: |
| $w_{\text{cap}}$ (capability) | 0.43 |
| $w_{\text{wage}}$ (wage upside) | 0.21 |
| $w_{\text{loc}}$ (location) | 0.18 |
| $w_{\text{rec}}$ (recency) | 0.18 |

The weights sum to 1.00. They were tuned together with the weights of the fit on the demo data (see `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, section 9).

---

## 3. CAPABILITY $S_{\text{cap}}$

$$S_{\text{cap}} = 0.53 \cdot SMF + 0.27 \cdot JRS + 0.20 \cdot 100\,(0.5\, F_{\text{level}} + 0.5\, F_{\text{years}})$$

| Symbol | Meaning |
| :--- | :--- |
| $SMF$ | The skill match of Formula 1 (0 to 100) |
| $JRS$ | The job readiness of Formula 2 (0 to 100) |
| $F_{\text{level}}$, $F_{\text{years}}$ | The level fit and the years fit of Formula 1 (0.6 if not known) |

A talent who is below the level of the job, or who has few years, has a lower capability even with the same skills.

---

## 4. WAGE UPSIDE $S_{\text{wage}}$

### 4.1 Equation

$$z = 0.6 \ln\frac{M}{B(d, r_J)} + 0.4 \ln\frac{M}{B(d, r_C)} \qquad S_{\text{wage}} = \frac{100}{1 + e^{-4.3\, z}}$$

$M$ is the middle of the yearly pay of the job (AUD). $d$ is the domain of the job. $r_J$ is the level of the job. $r_C$ is the level of the talent (the level of the job if the talent level is not known).
The first term says how well the job pays for its own level. The second term says how much the talent would gain at the current level.
The function is smooth. Equal pay gives 50. A job with no pay gives 50. There is no floor and no cap.

### 4.2 Benchmark

$$B(d, r) = \text{base}(d) \cdot e^{0.20\,(r - 2)}$$

| Domain | $\text{base}(d)$ for Mid (AUD per year) |
| :--- | :---: |
| Software Engineering | 130000 |
| AI & Machine Learning | 150000 |
| Data | 125000 |
| other or unknown | 130000 |

Each level step multiplies the pay by $e^{0.20} = 1.22$. The values are demo values. They are not an official statistic.

---

## 5. LOCATION $S_{\text{loc}}$

$$S_{\text{loc}} = 100 \cdot F_{\text{loc}}$$

$F_{\text{loc}}$ is the location and work-mode fit of Formula 1 (section 5.4): Remote = 1.0 for every talent; Onsite $0.25 + 0.75\, e^{-d/700}$; Hybrid $0.40 + 0.60\, e^{-d/900}$;
$d$ in km to the nearest preferred city. An unknown value gives 60.

---

## 6. RECENCY $S_{\text{rec}}$

$$S_{\text{rec}} = 100\, e^{-0.044\, D}$$

$D$ is the age of the posting in days (`days_old`). A job with no date counts as 14 days old.

---

## 7. EMPLOYER DIVERSITY PENALTY $\delta_{\text{div}}$

$$\delta_{\text{div}} = \min(0.40,\; 0.15\, k)$$

$k$ is the number of jobs of the same employer that are ranked above this job. The penalty multiplies the score.
`rank_job_feed_for_candidate` scores all jobs with no penalty, sorts them (ties: the job id), counts $k$ from the top of the list, applies the penalty and sorts again.

---

## 8. WORKED EXAMPLE

Talent: the talent of `01_SKILL_MATCHING_MODEL.md`, section 8 (Mid, 4.0 years, Sydney). Job: Senior Data Engineer, Senior, Data, 150000 to 170000 per year, Sydney, Hybrid, 6 days old.

1. **Capability.** $SMF = 67.4$ (from Formula 1). $JRS = 43.0$ (from Formula 2: six gaps). Level and years: $100\,(0.5 \cdot 0.577 + 0.5 \cdot 0.742) = 66.0$.
   $S_{\text{cap}} = 0.53 \cdot 67.4 + 0.27 \cdot 43.0 + 0.20 \cdot 66.0 = 60.6$.
2. **Wage.** $M = 160000$. $B(\text{Data}, \text{Senior}) = 125000 \cdot e^{0.2} = 152675$. $B(\text{Data}, \text{Mid}) = 125000$.
   $z = 0.6 \ln(160000/152675) + 0.4 \ln(160000/125000) = 0.0283 + 0.0987 = 0.127$. $S_{\text{wage}} = 100/(1 + e^{-4.3 \cdot 0.127}) = 63.3$.
3. **Location.** Same city, Hybrid, and the talent chose Hybrid. $S_{\text{loc}} = 100.0$.
4. **Recency.** $100\, e^{-0.044 \cdot 6} = 76.8$.
5. **Score.** $FRS = 0.43 \cdot 60.6 + 0.21 \cdot 63.3 + 0.18 \cdot 100.0 + 0.18 \cdot 76.8 = \mathbf{71.2}$.
6. **Diversity.** Three jobs of the employer Acme and one of another employer have the base scores 71.16, 70.95, 70.75 (Acme) and 70.56 (other). The Acme jobs get $\delta = 0, 0.15, 0.30$:
   the final scores are 71.2, 60.3, 49.5, and the other employer gets 70.6.

---

## 9. FUNCTIONS AND OUTPUT

| Function | Result |
| :--- | :--- |
| `compute_feed_job_score(candidate, job, same_employer_count_ahead=0, weights=(0.43, 0.21, 0.18, 0.18))` | `job_id`, `job_title`, `employer_name`, `job_sector`, `location`, `salary_range`, `feed_ranking_score`, `overall_score`, `frs_exact`, `base_exact`, `sub_metrics` |
| `sub_metrics` | `s_cap_capability`, `s_wage_upside`, `s_loc_location`, `s_rec_recency`, `employer_diversity_penalty`, `capability_smf`, `capability_readiness`, `capability_level_years` |
| `rank_job_feed_for_candidate(candidate, all_jobs, top_limit=50, weights=...)` | `candidate_id`, `candidate_name`, `total_jobs_evaluated`, `total_ranked_output`, `top_feed` (the items above with `feed_position`) |

The four keys of `sub_metrics` that start with `s_` are the radar axes "Capability", "Pay upside", "Location" and "Freshness" of "How this job fits you".
The old input shape works (a text location, a `requirements` list, `days_old`).
