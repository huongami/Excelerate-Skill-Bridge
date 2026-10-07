# TECHNICAL SPECIFICATION: EMPLOYER TALENT SEARCH RANKING MODEL (TSR)
**Document Number:** IE-SPEC-006 (version 2)  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `06_recruiter_candidate_ranking.py`

---

## 1. PURPOSE

This document gives the equations of the Talent Search Score (TSS).
The platform uses TSS to put anonymous talent profiles in order for one job of an employer.

**Rules of the product.**
- The employer sees the order, the per-skill match, the levels, the certifications and the awards. The employer never sees TSS.
- The formula reads the **shared profile** only: skills with levels, level, exact years, roles, certifications, awards, education, work preferences.
- The formula does not read the CV text, the evidence lines, a name, an email, a country or any other private field.
  A long CV does not give a higher score.

Version 2 changes:
- The seniority fit uses the level rank and the exact years. It does not use words of the job title.
- The evidence rigor uses skill levels, years with each skill, certifications and awards. It does not use the length of the CV text.
- The old statutory readiness (AHPRA, CPA) is removed. The part `s_reg_readiness` now measures the readiness for the certifications that the job lists.
- The constant audit part is now the completeness of the shared profile.
- The output has no country of origin. The key `candidate_origin` is removed.

---

## 2. THE MASTER EQUATION

$$TSS = w_{\text{req}} S_{\text{req}} + w_{\text{sen}} S_{\text{sen}} + w_{\text{evid}} S_{\text{evid}} + w_{\text{reg}} S_{\text{reg}} + w_{\text{audit}} S_{\text{audit}}$$

| Part | Meaning | Weight |
| :--- | :--- | :---: |
| $S_{\text{req}}$ | Requirement fit | 0.44 |
| $S_{\text{sen}}$ | Seniority fit | 0.25 |
| $S_{\text{evid}}$ | Evidence rigor | 0.18 |
| $S_{\text{reg}}$ | Certification readiness | 0.08 |
| $S_{\text{audit}}$ | Profile completeness | 0.05 |

The weights sum to 1.00. Every part has a range from 0 to 100.

**The order value of the platform:** $\text{order} = 0.6 \cdot \text{coverage} + 0.4 \cdot TSS$.
`coverage` is the level-aware coverage of the skills that the job lists (Formula 1, key `skill_coverage`, from 0 to 100).
The function returns `order_value`. The platform can use its own coverage number instead.

---

## 3. THE PARTS

### 3.1 Requirement fit $S_{\text{req}}$

$$S_{\text{req}} = \min\left(100,\; 100\,(0.65\,K + 0.22\,O + 0.13\,D) + 3\,A + 2\,P\right)$$

| Symbol | Meaning |
| :--- | :--- |
| $K$ | $\min(1, \bar{c} / 1.05)$. $\bar{c}$ is the weighted mean credit of the skills that the job lists (Formula 1, section 4). A skill above the required level gives a little more than 1. |
| $O$ | Occupation closeness of the roles of the talent to the job (Formula 1, section 5.3) |
| $D$ | Domain fit (Formula 1, section 5.5) |
| $A$ | Share of the preferred award kinds that the talent holds (recent awards count more) |
| $P$ | Share of the preferred certifications that the talent holds |

### 3.2 Seniority fit $S_{\text{sen}}$

$$S_{\text{sen}} = 100\,(0.55 \cdot F_{\text{level}} + 0.45 \cdot F_{\text{years}})$$

$F_{\text{level}}$ and $F_{\text{years}}$ are the level fit and the years fit of Formula 1 (sections 5.1 and 5.2).
The level rank of the talent is compared with the level rank of the job. The exact years are compared with the minimum and the maximum years of the job.
If a value is not known, 0.6 is used for that part. Words in the job title are not used.

### 3.3 Evidence rigor $S_{\text{evid}}$

$$S_{\text{evid}} = 0.50 \cdot 100\left(1 - e^{-Q/4}\right) + 0.30 \cdot \text{Cert} + 0.20 \cdot \text{Award}$$

$$Q = \sum_{\text{all skills}} \left(\frac{l_s}{5}\right)^2 \left(0.7 + 0.3 \min\left(1, \frac{y_s}{4}\right)\right) \cdot \kappa_s$$

$l_s$ is the skill level. $y_s$ is the years with the skill (2 if not given). $\kappa_s$ is 1.0 if the job asks for the skill or for a related skill, and 0.55 for another skill.
$\text{Cert}$ is $100\,(1 - e^{-W/1.8})$ with $W = \sum_c w_{\text{tier}} \cdot \kappa_c \cdot (0.7 + 0.3 e^{-\text{age}/4})$. $\kappa_c$ is 1.0 if the job lists the certification or the certification shows a skill that the job asks for, else 0.6.
The tier weights are: foundation 0.5, associate 1.0, professional 1.6, specialty 1.6, other 0.7.
$\text{Award} = 100\,(1 - e^{-W_a/1.5})$ with $W_a = \sum_a (0.6 + 0.4 e^{-\text{age}_a/6})$.

The length of the CV text is not an input.

### 3.4 Certification readiness $S_{\text{reg}}$

Each certification that the job lists has a credit: 1 if the talent holds it. If not, the credit is 0.30 (required) or 0.25 (preferred) times how well the talent holds the skills that the certification shows.
$R$ is the mean credit of the required ones. $P'$ is the mean credit of the preferred ones.

| The job lists | $S_{\text{reg}}$ |
| :--- | :--- |
| required and preferred | $100\,(0.8\,R + 0.2\,P')$ |
| only required | $100\,R$ |
| only preferred | $100\,(0.7 + 0.3\,P')$ |
| none | $90 + 0.10 \cdot \text{certification strength}$ of the profile |

A missing certification is never a legal block. There is no rule for AHPRA, CPA or any other registration.

### 3.5 Profile completeness $S_{\text{audit}}$

The share of the fields of the shared profile that are filled, with weights:
level known (1), exact years known (1), number of skills $1.5\,(1 - e^{-n/6})$, share of skills with an own level (1), and 0.5 each for certifications, awards, education, declared domain, target role, current role and city.
It checks the data contract of the shared profile. It reads no text.

---

## 4. WORKED EXAMPLE

Talent: level Senior, 7.0 years, Bachelor's degree, Sydney. Skills (level, years): SQL 5 (6), Python 4 (6), Apache Spark 4 (4), Communication 3 (5).
Certification: Databricks Certified Data Engineer Associate (2024). Award: open-source (2023).
Job: Senior Data Engineer, level Senior, 5 to 9 years, Sydney, Hybrid.
Skills: SQL 4 (must), Python 4 (must), Apache Spark 4 (must), Apache Airflow 3, Communication 3.
Required certification: Databricks Certified Data Engineer Associate. Preferred: Databricks Certified Data Engineer Professional. Preferred award: open-source.

1. **Credits.** SQL 1.068 (a level above), Python 1.0, Spark 1.0, Communication 1.0, Apache Airflow 0.45 (a related skill: Python). The weights are 2.20, 2.20, 3.23, 1.00, 1.37.
   The coverage is 92.4. $\bar{c} = 0.939$, so $K = 0.939/1.05 = 0.895$.
2. **Requirement fit.** $O = 1.0$, $D = 1.0$, $A = 0.843$, $P = 0$.
   $S_{\text{req}} = 100\,(0.65 \cdot 0.895 + 0.22 + 0.13) + 3 \cdot 0.843 + 0 = 95.7$.
3. **Seniority fit.** $F_{\text{level}} = 1.0$. $F_{\text{years}} = 0.92 + 0.08 \cdot (7 - 5)/(9 - 5) = 0.96$. $S_{\text{sen}} = 100\,(0.55 + 0.45 \cdot 0.96) = 98.2$.
4. **Evidence.** $Q = 2.64$, so the first term is $0.50 \cdot 48.3 = 24.2$. $\text{Cert} = 38.7$ and $\text{Award} = 43.0$.
   $S_{\text{evid}} = 24.2 + 0.30 \cdot 38.7 + 0.20 \cdot 43.0 = 44.4$.
5. **Certification readiness.** $R = 1$ (held). $P' = 0.05$ (the Professional exam is not held; the talent holds 20% of the skills that it shows). $S_{\text{reg}} = 100\,(0.8 + 0.2 \cdot 0.05) = 81.0$.
6. **Completeness.** $S_{\text{audit}} = 90.4$.
7. **Score.** $TSS = 0.44 \cdot 95.7 + 0.25 \cdot 98.2 + 0.18 \cdot 44.4 + 0.08 \cdot 81.0 + 0.05 \cdot 90.4 = \mathbf{85.6}$.
8. **Order value.** $0.6 \cdot 92.4 + 0.4 \cdot 85.6 = 89.7$.

---

## 5. FUNCTIONS AND OUTPUT

| Function | Result |
| :--- | :--- |
| `compute_talent_search_score(candidate, job, weights=(0.44, 0.25, 0.18, 0.08, 0.05))` | `candidate_id`, `candidate_name` (the alias), `target_role`, `talent_search_score`, `overall_score`, `tss_exact`, `sub_metrics` (`s_req_fit`, `s_sen_parity`, `s_evid_rigor`, `s_reg_readiness`, `s_audit_contract`, `s_level_fit`, `s_years_fit`, `s_skill_credit`), `skill_coverage`, `skill_breakdown`, `order_value`, `target_years_demanded`, `candidate_years_held`, `statutory_note` |
| `rank_candidates_for_job_requisition(job, candidates, top_limit=20)` | `job_id`, `job_title`, `job_company`, `job_sector`, `total_pool_evaluated`, `total_shortlist_output`, `ranked_shortlist` (with `shortlist_rank`; ties: the id) |

The old input shape works. The CV text and the evidence lines are ignored. A private field (name, email, country, visa, age, gender) changes nothing.
