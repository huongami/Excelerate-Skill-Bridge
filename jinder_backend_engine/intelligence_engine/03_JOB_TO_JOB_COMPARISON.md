# TECHNICAL SPECIFICATION: JOB-TO-JOB COMPARISON MODEL (JJF)
**Document Number:** IE-SPEC-003 (version 2)  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `03_job_to_job_comparison.py`

---

## 1. PURPOSE

This document gives the equations of the Job Proximity Index (JPI).
The index tells how close two jobs are. It has a range from 0 to 100.
A talent uses it to compare jobs. The platform also uses it to find similar jobs.

Version 2 changes:
- The model uses the facts of the ICT product: level, work mode, skill levels, domain.
- The skill overlap uses the required level of each skill.
- Every part is a smooth function. There are no fixed steps.
- The pay is changed to a yearly pay in one function, `annual_salary`.

---

## 2. SYMBOLS

| Symbol | Meaning | Range |
| :--- | :--- | :--- |
| $J_a$, $J_b$ | The two jobs | |
| $S_{\text{tree}}$ | Occupation closeness | 0 to 100 |
| $S_{\text{req}}$ | Skill overlap, weighted by level | 0 to 100 |
| $S_{\text{comp}}$ | Pay closeness | 0 to 100 |
| $S_{\text{sec}}$ | Domain closeness | 0 to 100 |
| $S_{\text{geo}}$ | Place and work-mode closeness | 0 to 100 |
| $S_{\text{lvl}}$ | Level closeness | 0 to 100 |
| $w_k$ | Weight of part $k$ | sum = 1 |

---

## 3. THE MASTER EQUATION

$$JPI(J_a, J_b) = \frac{\sum_k w_k S_k}{\sum_k w_k} \qquad k \in \{\text{tree}, \text{req}, \text{comp}, \text{sec}, \text{geo}, \text{lvl}\}$$

The sum runs over the parts that apply. A part that is not known (for example, a job with no level) is left out.
Then the other weights grow, so that the sum is 1 again.

Default weights `(tree, req, comp, sec, geo, lvl)`:

| Part | Weight |
| :--- | :---: |
| $S_{\text{tree}}$ | 0.20 |
| $S_{\text{req}}$ | 0.34 |
| $S_{\text{comp}}$ | 0.12 |
| $S_{\text{sec}}$ | 0.08 |
| $S_{\text{geo}}$ | 0.14 |
| $S_{\text{lvl}}$ | 0.12 |

An old 5-value weight tuple `(tree, req, comp, sec, geo)` still works. The level part then has no weight.

The index is symmetric: $JPI(J_a, J_b) = JPI(J_b, J_a)$. Two equal jobs give 100.

---

## 4. THE PARTS

### 4.1 Occupation closeness $S_{\text{tree}}$

The function uses the same closeness as Formula 1 (see `01_SKILL_MATCHING_MODEL.md`, section 5.3).
It is the mean of the two directions, so it is symmetric:

$$S_{\text{tree}} = 100 \cdot \tfrac{1}{2}\left(O(J_a \to J_b) + O(J_b \to J_a)\right)$$

$O$ is the weighted mean of: the closeness of the ANZSCO codes, the overlap of the occupation core skills, the words of the titles,
the specialisation and the domain.

### 4.2 Skill overlap $S_{\text{req}}$

For each skill $s$ of a job, the weight is:

$$u_s = L_s \cdot m_s \cdot \rho_s^{0.3}$$

$L_s$ is the required level (1 to 5). $m_s$ is 1.0 for a must skill and 0.6 for another skill. $\rho_s$ is the rarity of the skill (1.0 to 3.0, from the taxonomy).

The overlap is a weighted Jaccard index (Ruzicka):

$$S_{\text{req}} = 100 \cdot \frac{\sum_{s \in A \cap B} \min(u_s^{a}, u_s^{b}) + 0.40 \sum_{(p, q)} \min(u_p^{a}, u_q^{b})}{\sum_{s \in A \cap B} \max(u_s^{a}, u_s^{b}) + \sum_{(p, q)} \max(u_p^{a}, u_q^{b}) + \sum_{\text{rest}} u}$$

A pair $(p, q)$ is a skill that only job A has and a skill that only job B has, and the two skills are related in the taxonomy.
Each skill is in one pair at most. The pairs are made from the largest weights first, so the result does not depend on the order of the jobs.
"Rest" is the weight of the skills that are in no pair and not shared.

The same skill at a different level counts only for the lower level. So the same stack at level 2 and at level 4 overlaps less than the same stack at level 4 and 4.

If a job lists no skills, the function uses the words of the title and the description:
$S_{\text{req}} = 100 \cdot \min(1, 2.2 \cdot J)$, where $J$ is the Jaccard index of the two word sets.

### 4.3 Pay closeness $S_{\text{comp}}$

$$S_{\text{comp}} = 100 \cdot \exp\left(-\frac{|\ln(M_a / M_b)|}{0.5}\right)$$

$M$ is the middle of the pay range for one year, in AUD. The function does not give a value below 0, and it gives 100 for equal pay.

**Yearly pay.** The function `annual_salary(min, max, unit)` is the one place that changes a pay to a pay for one year:

| Unit | Rule |
| :--- | :--- |
| `year` | no change |
| `day` | $\times$ 220 working days |
| `hour` | $\times$ 1950 hours (37.5 hours $\times$ 52 weeks) |
| not given | a maximum below 500 is an hourly rate, from 500 to 3999 it is a day rate, a larger number is a yearly pay |

A job with no pay gets the benchmark of its domain and its level (see `05_JOB_SEEKER_RANKING_FEED.md`, section 4.2). With no domain and no level, the pay is 110000.

### 4.4 Domain closeness $S_{\text{sec}}$

$$S_{\text{sec}} = 100 \cdot \left(0.5 \cdot \mathbb{1}[\text{same domain}] + 0.5 \cdot \cos(\vec d_a, \vec d_b)\right)$$

$\vec d$ is the share of each domain in the skill list of the job. Each skill gives its required level, shared by the domains that it belongs to in the taxonomy.
A job with no skills uses 100 for the same domain, and 45 to 62 for two different known domains (25 for an unknown domain).

### 4.5 Place and work-mode closeness $S_{\text{geo}}$

$$S_{\text{geo}} = 100 \cdot P_{\text{mode}}(m_a, m_b) \cdot P_{\text{city}}$$

| Work modes | $P_{\text{mode}}$ |
| :--- | :---: |
| same mode | 1.00 |
| Hybrid and Onsite | 0.75 |
| Hybrid and Remote | 0.70 |
| Onsite and Remote | 0.40 |

$$P_{\text{city}} = \begin{cases} 1 & \text{if a job is Remote} \\ 0.25 + 0.75\, e^{-d/700} & \text{otherwise (} d \text{ in km)} \\ 0.6 & \text{if a city is not known} \end{cases}$$

### 4.6 Level closeness $S_{\text{lvl}}$

$$S_{\text{lvl}} = 100 \cdot \exp\left(-0.45\, |r_a - r_b|^{1.2}\right)$$

$r$ is the level rank (Intern 0, Junior 1, Mid 2, Senior 3, Lead 4, Principal 5).

---

## 5. TIERS (labels only)

| JPI | Label |
| :---: | :--- |
| 80 or more | Directly Substitutable Role |
| 60 to 79.9 | Adjacent Career Mobility |
| less than 60 | Cross-Disciplinary Career Pivot |

The label does not change the number.

---

## 6. WORKED EXAMPLE

| | Job A | Job B |
| :--- | :--- | :--- |
| Title | Senior Data Engineer | Data Engineer |
| Level, years | Senior, 5 to 9 | Mid, 2 to 5 |
| Place | Sydney, Hybrid | Melbourne, Remote |
| Pay | 150000 to 170000 per year | 120000 to 140000 per year |
| Code | 262111 | 262111 |
| Skills (level, must) | SQL 4 must, Python 4 must, Apache Spark 4 must, Apache Airflow 3 nice | SQL 3 must, Python 3 must, Apache Airflow 3 must, Data modelling 3 nice |

1. **Occupation.** The two codes are equal and the titles have the same words. $S_{\text{tree}} = 100.0$.
2. **Skills.** The weights $u$ are: A: SQL 4.00, Python 4.00, Apache Spark 4.85, Apache Airflow 2.11. B: SQL 3.00, Python 3.00, Apache Airflow 3.52, Data modelling 2.11.
   The sum of the minimum values for the three shared skills is $3.00 + 3.00 + 2.11 = 8.11$. The sum of the maximum values is $4.00 + 4.00 + 3.52 = 11.52$.
   Apache Spark (only A) adds 4.85 and Data modelling (only B) adds 2.11. They are not related, so there is no pair.
   $S_{\text{req}} = 100 \cdot 8.11 / 18.48 = 43.9$.
3. **Pay.** $M_a = 160000$, $M_b = 130000$. $S_{\text{comp}} = 100 \cdot \exp(-0.2076/0.5) = 66.0$.
4. **Domain.** The domains are equal and the skill shares are almost equal. $S_{\text{sec}} = 98.1$.
5. **Place.** Hybrid and Remote: $P_{\text{mode}} = 0.70$. A job is Remote, so $P_{\text{city}} = 1$. $S_{\text{geo}} = 70.0$.
6. **Level.** $|3 - 2| = 1$. $S_{\text{lvl}} = 100 \cdot \exp(-0.45) = 63.8$.
7. **Index.**
   $$JPI = 0.20 \cdot 100.0 + 0.34 \cdot 43.9 + 0.12 \cdot 66.0 + 0.08 \cdot 98.1 + 0.14 \cdot 70.0 + 0.12 \cdot 63.8 = \mathbf{68.1}$$
   The label is "Adjacent Career Mobility". The result for B and A is the same.

---

## 7. FUNCTIONS AND OUTPUT

| Function | Result |
| :--- | :--- |
| `compare_two_jobs(job_a, job_b, weights)` | `job_a`, `job_b` (id, title, company, location, anzsco, midpoint_salary_aud, level, work_mode), `job_proximity_index`, `sub_metrics` (`s_tree_taxonomy`, `s_req_jaccard`, `s_comp_salary_parity`, `s_sec_sector_affinity`, `s_geo_alignment`, `s_level_proximity`), `differentials` (`salary_delta_aud`, `salary_delta_label`, `level_delta`, `shared_competency_sample`, `unique_to_a_sample`, `unique_to_b_sample`), `operational_tier`, `career_mobility_advice` |
| `compare_multiple_jobs(job_list)` | `total_jobs_compared`, `job_titles`, `pairwise_proximity_matrix` ($N \times N$, symmetric, 100 on the diagonal), `baseline_comparisons_vs_first_job` |
| `get_job_salary_midpoint(job)` | The middle of the yearly pay range (AUD) |
| `annual_salary(min, max, unit)` | `(yearly min, yearly max)` |

The old input shape (`requirements` as a list of text, `location` as text, no level) still works.
