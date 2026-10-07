# TECHNICAL SPECIFICATION: SKILL GAP AND READINESS MODEL (SGF)
**Document Number:** IE-SPEC-002 (version 2)  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `02_skill_gap_analysis.py`

---

## 1. PURPOSE

This document gives the equations that find what a talent has and what a talent lacks for one job.
The model gives:

1. A list of **gap items** (what is missing, below the level, not enough years, a lower level, a missing certification).
2. A list of **strength items** (what the talent already meets).
3. The **readiness** of the talent for the job (JRS) and the **gap severity** (GSI).
4. The **months to close** all gaps (with the parallel-learning rule).
5. The `path` object for "Your path to this job" (`evaluate_path`).

Version 2 changes:
- The model uses the skill levels (1 to 5) of the talent and the required levels of the job. It does not read the CV text.
- The months come from the taxonomy (`monthsToLearn` for skills, `prepMonths` for certifications), from the level difference and from the years.
- A missing required certification is a gap with a number of months. It is **not** a legal block. There is no AHPRA or CPA rule.
- There is no 12-month projection.
- The readiness is a smooth function. It has no floor and no cap.

---

## 2. SYMBOLS

| Symbol | Meaning | Range |
| :--- | :--- | :--- |
| $h_s$ | Level of the talent in skill $s$ (0 if the skill is not held) | 0 to 5 |
| $n_s$ | Level that the job needs in skill $s$ | 1 to 5 |
| $\tau_s$ | `monthsToLearn` of the skill: months from zero to level 3 (Proficient) | 0.5 to 12 |
| $E(l)$ | Effort to reach level $l$ from zero | $E(3) = 1$ |
| $\lambda$ | Learner factor (learning speed) | 0.80 to 1.00 |
| $T_k$ | Months to close gap $k$ | 0.25 to 24 |
| $w_k$ | Weight of gap $k$ | 0.35 to 1.00 |
| $O$ | Occupation closeness of the talent to the job (Formula 1) | 0 to 1 |

---

## 3. THE GAP ITEMS

Each item has: `kind`, `item` (the name), `have_level`, `need_level`, `months`, `must`, `note`, `severity_points`.
The old keys (`gap_name`, `category_code`, `category_name`, `weight`, `duration_months`, `is_statutory_blocker`) stay.

| `kind` | When | `have_level` | `need_level` |
| :--- | :--- | :--- | :--- |
| `missing` | The job asks for a skill that the talent does not hold | 0 | $n_s$ |
| `below_level` | The talent holds the skill at a level below $n_s$ | $h_s$ | $n_s$ |
| `experience` | The exact years are 0.5 or more below the job minimum | years of the talent | minimum years |
| `level` | The level rank of the talent is 0.75 or more below the rank of the job | level of the talent | level of the job |
| `certification` | A certification that the job lists (required or preferred) is not held | "none" | "Required" or "Preferred" |

The old category codes now mean: `CAT-1` certification, `CAT-2` required skill, `CAT-3` nice-to-have skill, `CAT-4` experience or level.
`has_statutory_blocker` is always false.

A **strength item** has the same keys. It is made for each skill that is met (level at or above $n_s$), for the years (at or above the minimum),
for the level (at or above the level of the job), for each held certification that the job lists, and for each held preferred award kind.

---

## 4. EQUATIONS

### 4.1 Effort and months for a skill

$$E(l) = \left(\frac{l}{3}\right)^{1.6}$$

$$T = \text{clip}\left(\tau_s \cdot \bigl(E(n_s) - E(h_s)\bigr) \cdot \left(1 - 0.30 \min\left(1, \frac{c_{\text{rel}}}{0.45}\right)\right) \cdot \lambda,\; 0.25,\; 18\right)$$

$c_{\text{rel}}$ is the credit for related skills (from Formula 1) when the skill is missing and the talent holds a related skill. It makes the learning faster.
For a skill that is held below the level, $h_s$ is the level of the talent. For a missing skill, $h_s = 0$.

### 4.2 Learner factor

$$\lambda = 1 - 0.16\left(1 - e^{-Y/8}\right) - 0.012 \cdot \min(4, e)$$

$Y$ is the exact years of experience. $e$ is the education rank (0 if not known; Bachelor 3, Master 4). The factor is from 0.80 to 1.00.

### 4.3 Months for a certification, for experience and for a level

$$T_{\text{cert}} = \text{prepMonths} \cdot (1 - 0.5\, k) \cdot \lambda$$

$k$ is how well the talent holds the skills that the certification shows (the mean of $\min(1, h/3)$ over its `evidences` skills, from 0 to 1).

$$T_{\text{exp}} = 14\left(1 - e^{-\Delta Y / 2.2}\right) \qquad T_{\text{level}} = \min\left(24,\; 6 \cdot \Delta r^{1.1}\right)$$

$\Delta Y$ is the years below the job minimum. $\Delta r$ is the number of level steps below the job level.

### 4.4 Severity, readiness and months to close

$$\text{sev}_k = w_k \left(16\left(1 - e^{-T_k/2.5}\right) + 3 \ln(1 + T_k)\right)$$

| Gap | $w_k$ |
| :--- | :---: |
| required skill (must) | 1.00 |
| nice-to-have skill | 0.45 |
| required certification | 0.90 |
| preferred certification | 0.35 |
| experience | 0.70 |
| level | 0.80 |

$$S = \sum_k \text{sev}_k + 6\,(1 - O)$$

$$JRS = 100\, e^{-S/70} \qquad GSI = 100 - JRS$$

The term $6(1-O)$ is the cost of a move to a different kind of role. The functions have no floor and no cap: a job with no gap and the same occupation gives about 100.
Gaps that are below the list threshold (experience under 0.5 years, level under 0.75 steps) still count in $S$.

$$T_{\text{total}} = \max_k T_k + 0.18\left(\sum_k T_k - \max_k T_k\right)$$

The talent learns some things at the same time (the parallel-learning rule). With no gap, $T_{\text{total}} = 0$.

### 4.5 Readiness tier (label only)

| JRS | Label | Code |
| :---: | :--- | :--- |
| 80 or more | Low Gap (Immediate Deployment) | `TIER_LOW_GAP` |
| 55 to 79.9 | Moderate Gap (Fast-Track Upskilling) | `TIER_MODERATE_GAP` |
| less than 55 | High Gap (Structural Bridging Required) | `TIER_HIGH_GAP` |

---

## 5. THE `path` OBJECT

`evaluate_path(candidate, job)` returns this object (V2_PLAN section 5.3):

```
{ "axes":  [ { "key", "label", "group", "required", "have", "status" } ],
  "fit":   [ { "kind", "label", "have", "need", "note" } ],
  "gaps":  [ { "kind", "label", "have", "need", "months", "must", "note" } ],
  "summary": { "fitCount", "gapCount", "monthsToClose", "readinessTier" } }
```

**Axes.** One axis for each skill group that the job asks for (taxonomy groups: languages, frameworks, cloud, data, ml, practices, collab; a skill that is not in the taxonomy goes to `other`).
Then the axis `experience` and the axis `level`. The axis `certifications` is there only when the job lists a certification.
For an axis that is not a skill group, `group` has the same text as `key`.

For a skill group $G$ with the skills $s$ that the job lists (the weight $u_s$ is the weight of Formula 1, section 4.1, that counts must skills double):

$$\text{required}_G = \frac{\sum_s u_s \cdot n_s/5 \cdot 100}{\sum_s u_s} \qquad \text{have}_G = \frac{\sum_s u_s \cdot \min(h_s, 5)/5 \cdot 100}{\sum_s u_s}$$

| Axis | required | have |
| :--- | :--- | :--- |
| `experience` | $\min(100,\; 100 \cdot \text{min years} / 10)$ | $\min(100,\; 100 \cdot Y / 10)$ |
| `level` | $100 \cdot r_{\text{job}} / 5$ | $100 \cdot r_{\text{talent}} / 5$ |
| `certifications` | 100 | $100 \cdot$ (weight of the held certifications) / (weight of the listed ones); required count 2, preferred count 1 |

**Status** (from the numbers with one decimal): `above` if have $\ge$ required + 15, else `fit` if have $\ge$ required, else `gap`.

**Fit list.** Skills that are met (the best credit first), experience, level, held certifications and held preferred awards.
`have` and `need` are words: the skill level words (Beginner, Working, Proficient, Advanced, Expert), the level names, "3 years", "Held", "Required".

**Gap list.** The gap items in order of severity (the largest first). The `months` of each item are the numbers of 4.1 to 4.3.

**Summary.** `fitCount` and `gapCount` are the lengths of the two lists. `monthsToClose` is $T_{\text{total}}$. `readinessTier` is the label of 4.5.

---

## 6. WORKED EXAMPLE

Talent: level Mid, 3.0 years, Bachelor's degree, skills SQL 4 and Python 3. Current role Data Analyst, target role Data Engineer.
Job: Senior Data Engineer, 5 to 9 years, skills SQL 4 (must), Python 4 (must), Apache Airflow 3 (must). Required certification: SnowPro Core Certification (prepMonths 2.0).

1. **Learner factor.** $\lambda = 1 - 0.16 \cdot (1 - e^{-3/8}) - 0.012 \cdot 3 = 1 - 0.050 - 0.036 = 0.914$.
2. **Python is below the level.** $\tau = 3$. $E(4) - E(3) = 1.585 - 1.000 = 0.585$. $T = 3 \cdot 0.585 \cdot 0.914 = 1.6$ months.
3. **Apache Airflow is missing.** $\tau = 2$, $E(3) = 1$. The talent holds the related skill Python, so $c_{\text{rel}} = 0.45$ and the speed factor is $1 - 0.30 = 0.70$. $T = 2 \cdot 1 \cdot 0.70 \cdot 0.914 = 1.3$ months.
4. **The certification is missing.** The talent holds a third of the skills that it shows ($k = 0.333$). $T = 2.0 \cdot (1 - 0.167) \cdot 0.914 = 1.5$ months.
5. **Experience.** The talent is 2.0 years below the minimum. $T = 14\,(1 - e^{-2/2.2}) = 8.4$ months.
6. **Level.** Mid to Senior is 1 step. $T = 6 \cdot 1^{1.1} = 6.0$ months.
7. **Severity.** The values $\text{sev}_k$ are: level 16.31, experience 15.50, Python 10.44, certification 9.07, Airflow 8.88. The sum is 60.20.
   The occupation closeness is $O = 0.976$, so the cost of the move is $6 \cdot 0.024 = 0.14$. $S = 60.35$.
8. **Readiness.** $JRS = 100\, e^{-60.35/70} = \mathbf{42.2}$. $GSI = 57.8$. The label is "High Gap".
9. **Months to close.** $T_{\text{total}} = 8.4 + 0.18 \cdot (6.0 + 1.6 + 1.5 + 1.3) = \mathbf{10.2}$ months.
10. **Path axes.** Languages (SQL and Python): required 80.0, have 70.0, status `gap`. Data and storage (Apache Airflow): required 60.0, have 0.0, `gap`.
    Experience: 50.0 and 30.0. Level: 60.0 and 40.0. Certifications: 100.0 and 0.0. The fit list has SQL (Advanced, needs Advanced).

---

## 7. FUNCTIONS AND OUTPUT

| Function | Result |
| :--- | :--- |
| `evaluate_skill_gaps(candidate, job, explicit_missing_skills=None)` | `candidate_id`, `candidate_name`, `job_id`, `job_title`, `total_gaps_count`, `classified_gaps` and `gaps` (the same list), `strengths`, `gap_severity_index`, `skill_gap_pct`, `job_readiness_score`, `estimated_bridge_months`, `estimated_closing_months`, `months_to_close`, `has_statutory_blocker` (false), `readiness_tier`, `readiness_tier_code`, `learner_factor`, `adaptation_friction` |
| `evaluate_path(candidate, job)` | the `path` object of section 5 |

`explicit_missing_skills` is a list of names that the caller found missing. A name that is not in the skill list of the job and not held becomes a gap with level 3.
The old input shape (skills as text, `requirements` as text) still works.
