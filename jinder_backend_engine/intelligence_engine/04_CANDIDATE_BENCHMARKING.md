# TECHNICAL SPECIFICATION: PROFILE BENCHMARKING MODEL (CCF)
**Document Number:** IE-SPEC-004 (version 2)  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `04_candidate_benchmarking.py`

---

## 1. PURPOSE

This document gives the equations of the merit dimensions of one talent profile.
An employer compares profiles area by area. Each dimension has a range from 0 to 100.

**Rule of the product.** The platform shows the dimensions one by one (areas and radar axes).
It never shows the total (`relative_merit_score`). It never ranks people with the total.

The model reads the **shared profile** only:
skills with levels, level, exact years, years with each skill, certifications, awards, education.
It does not read the CV text. A long CV does not give a higher value.

Version 2 changes:
- The dimensions use the level, the exact years, the skill levels, the certifications and the awards.
- The evidence rigor uses skill levels, certifications and awards. It does not use the length of the CV text.
- There is no regulatory penalty (AHPRA, CPA). The key `gap_penalty_deduction` stays and it is 0.
- Every dimension is a smooth function.

---

## 2. SYMBOLS

| Symbol | Meaning | Range |
| :--- | :--- | :--- |
| $l_s$ | Level of skill $s$ (after a small fade for a skill that was not used for years) | 1 to 5 |
| $\rho_s$ | Rarity of skill $s$ (taxonomy) | 1.0 to 3.0 |
| $y_s$ | Years of use of skill $s$ (2 if not given) | 0 or more |
| $Y$ | Exact years of experience | 0 to 50 |
| $r$ | Level rank (Intern 0 ... Principal 5) | 0 to 5 |
| $\text{sat}(x, a)$ | $1 - e^{-x/a}$ for $x \ge 0$ | 0 to 1 |

The fade of a skill level for a skill that is not used for years is: $l \cdot (0.80 + 0.20\, e^{-\text{age}/3})$, where age is the number of years since the last use.

---

## 3. THE DIMENSIONS

### 3.1 Skill depth

Profile form (no job):

$$\text{Depth} = 100 \cdot \text{sat}\left(\sum_{s \in \text{hard}} \left(\frac{l_s}{5}\right)^{1.6} \rho_s^{0.4},\; 4.2\right)$$

Job form (the function gets a job): the weighted mean of $l_s / 5$ over the skills that the job asks for. A skill that is not held counts 0.
The weights are those of Formula 1 (see `01_SKILL_MATCHING_MODEL.md`, section 4).
The result has the key `depth_basis` ("profile" or "job").

### 3.2 Experience maturity

$$\text{Exp} = 100 \cdot \left(1 - e^{-Y/6.5}\right)$$

### 3.3 Level standing

$$\text{Level} = 100 \cdot \left(\frac{r}{5}\right)^{0.9}$$

If the level is not known, it is estimated from the title words, then from the years.

### 3.4 Certification strength and award strength

$$\text{Cert} = 100 \cdot \text{sat}\left(\sum_c w_{\text{tier}(c)} \left(0.7 + 0.3\, e^{-\text{age}_c/4}\right),\; 1.8\right)$$

The tier weights are: foundation 0.5, associate 1.0, professional 1.6, specialty 1.6, other 0.7.

$$\text{Award} = 100 \cdot \text{sat}\left(\sum_a \left(0.6 + 0.4\, e^{-\text{age}_a/6}\right),\; 1.5\right)$$

### 3.5 Evidence rigor

$$\text{Evid} = 0.50 \cdot 100\, \text{sat}(Q, 5) + 0.30 \cdot \text{Cert} + 0.20 \cdot \text{Award}$$

$$Q = \sum_{\text{all skills}} \left(\frac{l_s}{5}\right)^2 \left(0.7 + 0.3 \min\left(1, \frac{y_s}{4}\right)\right)$$

The CV text is not an input. Two profiles with the same skills, certifications and awards have the same evidence rigor.

### 3.6 Transferable agility

$$\text{Trans} = 0.7 \cdot 100\, \text{sat}\left(\sum_{s \in \text{method, soft}} \left(\frac{l_s}{5}\right)^{1.3} \rho_s^{0.3},\; 2.6\right) + 0.3 \cdot 100 \cdot \frac{\text{skill groups used}}{7}$$

### 3.7 Education

$$\text{Edu} = 100 \cdot \left(\frac{e}{5}\right)^{0.8} \cdot \phi$$

$e$ is the education rank (Certificate 1, Diploma 2, Bachelor 3, Master 4, PhD 5). $\phi$ is 1.0 for a computing or maths field, 0.6 for another field, 0.8 if the field is not known.
The key `education_bonus` is $5 \cdot \text{Edu}/100$ (from 0 to 5 points). It is 0.5 if the education is not known. Education is a soft factor and it never gives 0 to the total.

---

## 4. THE TOTAL (not shown by the platform)

$$RMS = \min\left(100,\; \frac{\sum_i w_i D_i}{\sum_i w_i} + \text{education bonus}\right)$$

| Dimension $D_i$ | Weight $w_i$ |
| :--- | :---: |
| Skill depth | 0.30 |
| Experience maturity | 0.20 |
| Evidence rigor | 0.22 |
| Transferable agility | 0.12 |
| Level standing | 0.16 |

The weights sum to 1.00. The level standing is left out if the level is not known and cannot be estimated.

---

## 5. HEAD-TO-HEAD AND GROUP

- $\Delta(A, B) = RMS(A) - RMS(B)$. If $|\Delta| \le 8$, the two profiles are in the same band. If $\Delta > 8$, A has clearly more merit. If $\Delta < -8$, B has clearly more merit.
- `rank_candidate_cohort` sorts the profiles by $RMS$ (ties: the id) and gives the position and the percentile $(1 - i/(N-1)) \cdot 100$ in the group.
- The platform uses the **dimensions** (areas, radar), not $RMS$ and not $\Delta$.

---

## 6. WORKED EXAMPLE (reference year 2026)

Profile: level Senior, 8 years, Master's degree in Computer science.
Skills (level, years of use): Python 5 (6), SQL 4 (5), Docker 4 (3), Apache Spark 3 (2), Communication 4 (5, soft), Mentoring 3 (2, soft).
One certification: SnowPro Core Certification (2025, tier associate). One award: hackathon (2024).

1. **Depth.** The sum is $P = 2.970$. $\text{Depth} = 100 (1 - e^{-2.970/4.2}) = 50.7$.
2. **Experience.** $100 (1 - e^{-8/6.5}) = 70.8$.
3. **Level.** $100 \cdot (3/5)^{0.9} = 63.1$.
4. **Cert.** $W = 1.0 \cdot (0.7 + 0.3 e^{-1/4}) = 0.934$. $\text{Cert} = 100 (1 - e^{-0.934/1.8}) = 40.5$.
5. **Award.** $W = 0.6 + 0.4 e^{-2/6} = 0.887$. $\text{Award} = 100 (1 - e^{-0.887/1.5}) = 44.6$.
6. **Evidence.** $Q = 3.484$. $\text{Evid} = 0.50 \cdot 50.2 + 0.30 \cdot 40.5 + 0.20 \cdot 44.6 = 46.2$.
7. **Transfer.** $M = 1.330$ and 4 of 7 skill groups. $\text{Trans} = 0.7 \cdot 28.0 + 0.3 \cdot 57.1 = 45.2$.
8. **Education.** $100 \cdot (4/5)^{0.8} \cdot 1.0 = 83.7$. The bonus is 4.18 points.
9. **Total.** $0.30 \cdot 50.7 + 0.20 \cdot 70.8 + 0.22 \cdot 46.2 + 0.12 \cdot 45.2 + 0.16 \cdot 63.1 + 4.18 = \mathbf{59.2}$.

---

## 7. FUNCTIONS AND OUTPUT

| Function | Result |
| :--- | :--- |
| `calculate_candidate_merit_score(cand, weights=(0.30, 0.20, 0.22, 0.12, 0.16), job=None)` | `candidate_id`, `candidate_name` (the alias), `relative_merit_score`, `overall_score`, `sub_metrics`, `depth_basis`, `verified_years_exp`, `has_statutory_gap` (always false) |
| `sub_metrics` | `skill_depth`, `experience_maturity`, `evidence_rigor`, `transferable_agility`, `level_standing`, `certification_strength`, `award_strength`, `skill_breadth`, `education_level`, `gap_penalty_deduction` (0), `education_bonus` |
| `compare_two_candidates(a, b, job=None)` | `candidate_a`, `candidate_b`, `score_delta`, `hiring_verdict`, `recommended_candidate` |
| `rank_candidate_cohort(list, job=None)` | `total_candidates`, `top_ranked_candidate`, `ranked_shortlist` (with `cohort_rank`, `cohort_percentile`) |

The old input shape (skills as text, `years_of_experience`, `rawResume`) still works. The CV text is ignored.
