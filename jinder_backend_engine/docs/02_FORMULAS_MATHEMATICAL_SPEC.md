# Jinder - Mathematical Formulas and Scoring Engine Specification (version 2)

**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `intelligence_engine/01_` to `06_*.py` and `engine_common.py`  
**Detail:** each formula has its own file `intelligence_engine/0N_*.md` with the full equations and a worked example. This file has the short form.

---

## 1. Design principles

The engine gives a score for each pair of a talent and a job. The user feedback was: "The jobs that are shown all have the same overall fit."
Version 2 follows these rules:

1. **Continuous.** No fixed step decides a score alone. The functions are exponential, logistic, saturation, logarithmic or linear interpolation.
2. **Detailed.** The input has the level (Intern to Principal), the exact years, the skill levels (1 to 5), the certifications, the awards and the work mode.
3. **Bounded.** Each score is from 0 to 100.
4. **Deterministic.** The same input gives the same output. Ties are broken by the id.
5. **Private.** No formula reads a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo.
   On the employer side (Formulas 4 and 6) the engine reads the shared profile only. It never reads the CV text. An employer never gets a score on a person.
6. **Taxonomy.** Names, aliases (any case), related skills, `monthsToLearn`, `rarity`, groups, occupations and certifications come from `data/reference/ict_taxonomy.json`.
   If the file is missing, the engine uses simple defaults and still runs.
7. **Old shapes.** The old dictionaries (skills as text, no level, no years of skill) still work.

---

## 2. The smooth functions

| Name | Equation | Use |
| :--- | :--- | :--- |
| Saturation | $\text{sat}(x, a) = 1 - e^{-x/a}$ | merit dimensions, learner factor |
| Logistic | $L(x; k) = 1 / (1 + e^{-kx})$ | wage upside |
| Exponential decay | $e^{-x/a}$, $e^{-b x^p}$ | level fit, years fit, distance, recency, pay closeness |
| Power credit | $(h/n)^{1.3}$ | partial credit for a skill below the level |
| Weighted Jaccard | $\sum \min / \sum \max$ | occupation skills, job skill overlap |
| Linear interpolation | piece-wise linear through control points | level rank from years |

---

## 3. Formula 1: skill match (SMF) and product fit

**Skill credit** (level $h$ of the talent, level $n$ that the job needs):

$$c = \begin{cases} 1 + 0.12\,(1 - e^{-(h-n)/1.2}) & h \ge n \\ (h/n)^{1.3} & h < n \end{cases} \qquad \text{related skill: } c = \min(0.55,\; 0.45\, r^{1.2} + 0.04\,(k-1))$$

**Weight of a skill:** $u = m \cdot \rho^{0.6} \cdot (0.7 + 0.1\, n)$ ($m = 2$ for a must skill, 1 for another; $\rho$ = rarity from 1.0 to 3.0).

**Skill scores:** $S_{\text{direct}} = 100 \min(1, \sum u c / \sum u)$ over the hard skills. $S_{\text{trans}}$ is the same over the method and soft skills.

**Level fit:** $d = r_C - r_J$. $F_{\text{level}} = e^{-0.55|d|^{1.2}}$ if $d < 0$, else $e^{-0.28\, d^{1.2}}$.

**Years fit:** $F_{\text{years}}$ is $0.92\, e^{-((Y_{\min} - Y)/s)^{1.4}}$ below the minimum, from 0.92 to 1.0 inside the range, and $1 - 0.25\,(1 - e^{-(Y - Y_{\max})/6})$ above the maximum.

**Occupation closeness $O$:** the weighted mean of the code closeness $e^{-0.26(6-c)^{1.3}}$, the core-skill overlap, the title-word overlap, the specialisation and the domain.

**Skill match:** $SMF = \min(100,\; (0.25\, S_{\text{tree}} + 0.50\, S_{\text{direct}} + 0.25\, S_{\text{trans}}) \cdot \Phi)$, $\Phi = 0.78 + 0.27\,(0.55\, F_{\text{years}} + 0.45\, F_{\text{level}})$.

**Product fit:** $\text{fit} = \text{clip}\left(100 \sum w_i P_i / \sum w_i + 7\,(G - 0.45) + 3\,A\right)$.

| Part $P_i$ | skills | methods | occupation | level | experience | domain | location | work type | education |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Weight $w_i$ | 0.39 | 0.04 | 0.16 | 0.10 | 0.09 | 0.10 | 0.07 | 0.02 | 0.03 |

$G$ is the certification credit (the adjustment is 0 if the job lists no certification). $A$ is the award credit (at most +3 points). A part that does not apply to a job is left out.

| Range | Symbol | Meaning |
| :--- | :--- | :--- |
| 0 to 1.12 | $c$ | credit of one skill |
| 0 to 1 | $F_{\text{level}}$, $F_{\text{years}}$, $O$ | fits |
| 0.2 to 1 | $F_{\text{edu}}$ | education is a soft factor: it never gives 0 |
| 0 to 100 | fit, SMF | scores |

**Worked example.** (Talent: Mid, 4 years. Job: Senior, 5 to 9 years.) Skills $S_{\text{direct}} = 65.3$, $S_{\text{trans}} = 52.7$, $O = 0.976$, $F_{\text{level}} = 0.577$, $F_{\text{years}} = 0.742$, certification $-2.71$, award $+2.66$.
$\text{fit} = 77.66 - 2.71 + 2.66 = 77.6$. $SMF = 70.2 \cdot 0.960 = 67.4$. The full steps are in `intelligence_engine/01_SKILL_MATCHING_MODEL.md`, section 8.

---

## 4. Formula 2: gaps, readiness and path

**Months of a skill gap:** $T = \text{clip}\left(\tau \,(E(n) - E(h))\,(1 - 0.30 \min(1, c_{\text{rel}}/0.45))\,\lambda,\; 0.25,\; 18\right)$, $E(l) = (l/3)^{1.6}$, $\tau$ = `monthsToLearn`.

**Learner factor:** $\lambda = 1 - 0.16\,(1 - e^{-Y/8}) - 0.012 \min(4, e)$.

**Other months:** certification $T = \text{prepMonths}\,(1 - 0.5\,k)\,\lambda$; experience $T = 14\,(1 - e^{-\Delta Y/2.2})$; level $T = \min(24, 6\, \Delta r^{1.1})$.

**Severity and readiness:** $\text{sev}_k = w_k\,(16\,(1 - e^{-T_k/2.5}) + 3 \ln(1 + T_k))$, $S = \sum \text{sev}_k + 6\,(1 - O)$, $JRS = 100\, e^{-S/70}$, $GSI = 100 - JRS$.

**Months to close (parallel rule):** $T_{\text{total}} = \max T + 0.18\,(\sum T - \max T)$.

A missing required certification is a gap with `months` = `prepMonths` (scaled). It is not a legal block. There is no 12-month projection.

**Path radar.** For a skill group: $\text{required} = \sum u \cdot n/5 \cdot 100 / \sum u$ and $\text{have} = \sum u \cdot \min(h, 5)/5 \cdot 100 / \sum u$.
Axes `experience` ($\min(100, 10 \cdot \text{years})$), `level` ($100\, r/5$) and `certifications` (only if the job lists one). Status: `above` if have $\ge$ required + 15, `fit` if have $\ge$ required, else `gap`.

| Range | Symbol | Meaning |
| :--- | :--- | :--- |
| 0.25 to 24 months | $T_k$ | time of one gap |
| 0.80 to 1.00 | $\lambda$ | learner factor |
| 0 to 100 | JRS, GSI, required, have | readiness, severity, axis values |

**Worked example.** (Talent: Mid, 3 years, SQL 4, Python 3. Job: Senior, 5 to 9 years, SQL 4, Python 4, Airflow 3, SnowPro required.)
Gaps: level 6.0 months, experience 8.4, Python 1.6, certification 1.5, Airflow 1.3. $S = 60.35$. $JRS = 100\, e^{-60.35/70} = 42.2$. $T_{\text{total}} = 8.4 + 0.18 \cdot 10.4 = 10.2$ months.
See `intelligence_engine/02_SKILL_GAP_ANALYSIS.md`, section 6.

---

## 5. Formula 3: job proximity (JPI)

$$JPI = \frac{\sum_k w_k S_k}{\sum_k w_k}$$

| Part | tree | req | comp | sec | geo | level |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Weight | 0.20 | 0.34 | 0.12 | 0.08 | 0.14 | 0.12 |

$S_{\text{req}}$ is the weighted Jaccard of the skills with levels (related pairs count 0.4). $S_{\text{comp}} = 100\, e^{-|\ln(M_a/M_b)|/0.5}$. $S_{\text{lvl}} = 100\, e^{-0.45|r_a - r_b|^{1.2}}$.
$S_{\text{geo}} = 100 \cdot P_{\text{mode}} \cdot P_{\text{city}}$ (Remote and Remote 1.0, Hybrid and Remote 0.7, Onsite and Remote 0.4; city $0.25 + 0.75\, e^{-d/700}$, 1 if a job is Remote).
The index is symmetric. **Yearly pay:** `annual_salary(min, max, unit)` gives year $\times 1$, day $\times 220$ working days, hour $\times 1950$ hours.

**Worked example.** Senior Data Engineer (Sydney, Hybrid) and Data Engineer (Melbourne, Remote): $S = (100.0,\; 43.9,\; 66.0,\; 98.1,\; 70.0,\; 63.8)$. $JPI = 68.1$. See `intelligence_engine/03_JOB_TO_JOB_COMPARISON.md`, section 6.

---

## 6. Formula 4: merit areas (RMS)

$\text{Depth} = 100\,\text{sat}(\sum (l/5)^{1.6} \rho^{0.4},\, 4.2)$. $\text{Exp} = 100\,(1 - e^{-Y/6.5})$. $\text{Level} = 100\,(r/5)^{0.9}$.
$\text{Evid} = 0.50 \cdot 100\,\text{sat}(Q, 5) + 0.30\,\text{Cert} + 0.20\,\text{Award}$ with $Q = \sum (l/5)^2 (0.7 + 0.3 \min(1, y/4))$. **The CV text length is not used.**
$\text{Trans} = 0.7 \cdot 100\,\text{sat}(M, 2.6) + 0.3 \cdot 100 \cdot (\text{groups}/7)$.
$RMS = \min(100,\; 0.30\,\text{Depth} + 0.20\,\text{Exp} + 0.22\,\text{Evid} + 0.12\,\text{Trans} + 0.16\,\text{Level} + \text{education bonus})$.

The platform shows the dimensions (areas, radar axes). It never shows RMS and it never ranks people with it.

**Worked example.** (Senior, 8 years, Master's degree, one certification, one award.) Depth 50.7, Exp 70.8, Evid 46.2, Trans 45.2, Level 63.1, bonus 4.18. $RMS = 59.2$. See `intelligence_engine/04_CANDIDATE_BENCHMARKING.md`, section 6.

---

## 7. Formula 5: feed ranking (FRS)

$$FRS = (0.43\, S_{\text{cap}} + 0.21\, S_{\text{wage}} + 0.18\, S_{\text{loc}} + 0.18\, S_{\text{rec}})\,(1 - \delta_{\text{div}})$$

$S_{\text{cap}} = 0.53\, SMF + 0.27\, JRS + 0.20 \cdot 100\,(0.5\, F_{\text{level}} + 0.5\, F_{\text{years}})$.
$S_{\text{wage}} = 100 / (1 + e^{-4.3 z})$, $z = 0.6 \ln(M / B(d, r_J)) + 0.4 \ln(M / B(d, r_C))$, $B(d, r) = \text{base}(d)\, e^{0.20 (r - 2)}$ (base for Mid: Software Engineering 130000, AI & Machine Learning 150000, Data 125000).
$S_{\text{loc}} = 100 \cdot F_{\text{loc}}$ (Remote = 100). $S_{\text{rec}} = 100\, e^{-0.044 D}$. $\delta_{\text{div}} = \min(0.40, 0.15\, k)$.
The platform score is $0.55\,\text{fit} + 0.45\, FRS^{*}$. The feedback loop of the platform (+10% saved employer, +5% saved domain, -25% after 3 skipped jobs of one employer) makes $FRS^{*}$ from FRS.

**Worked example.** $S_{\text{cap}} = 60.6$, $S_{\text{wage}} = 63.3$, $S_{\text{loc}} = 100$, $S_{\text{rec}} = 76.8$. $FRS = 71.2$. See `intelligence_engine/05_JOB_SEEKER_RANKING_FEED.md`, section 8.

---

## 8. Formula 6: talent search (TSS)

$$TSS = 0.44\, S_{\text{req}} + 0.25\, S_{\text{sen}} + 0.18\, S_{\text{evid}} + 0.08\, S_{\text{reg}} + 0.05\, S_{\text{audit}}$$

$S_{\text{req}} = 100\,(0.65\,K + 0.22\,O + 0.13\,D) + 3A + 2P$. $S_{\text{sen}} = 100\,(0.55\, F_{\text{level}} + 0.45\, F_{\text{years}})$ (level rank and exact years; not title words).
$S_{\text{evid}}$ uses skill levels, years with each skill, certifications and awards (not the CV text). $S_{\text{reg}}$ is the readiness for the certifications that the job lists (no AHPRA or CPA rule).
$S_{\text{audit}}$ is the completeness of the shared profile. The employer order is $0.6 \cdot \text{coverage} + 0.4 \cdot TSS$.

**Worked example.** $S_{\text{req}} = 95.7$, $S_{\text{sen}} = 98.2$, $S_{\text{evid}} = 44.4$, $S_{\text{reg}} = 81.0$, $S_{\text{audit}} = 90.4$. $TSS = 85.6$. Coverage 92.4, order value 89.7. See `intelligence_engine/06_RECRUITER_CANDIDATE_RANKING.md`, section 4.

---

## 9. Tuning and the differentiation numbers

The weights of the fit (Formula 1) and of the feed (Formula 5) are the only constants that were tuned on the demo data. The limits were: skills 0.26 to 0.40, occupation 0.10 to 0.20, level 0.09 to 0.16,
experience 0.06 to 0.12, domain 0.04 to 0.11, location 0.06 to 0.12, capability weight of the feed 0.40 to 0.52, wage 0.14 to 0.26, location 0.14 to 0.24, recency 0.08 to 0.18.
All other constants (exponents, scales, rates) were set from the meaning of the part, before the tuning.

Result on `data/synthetic` (50 jobs, 50 talents, product score $0.55\,\text{fit} + 0.45\,FRS$, one decimal):

| Check (V2_PLAN section 9) | Target | Result |
| :--- | :---: | :---: |
| Different scores in the top 20 (each talent) | 18 or more | min 19, mean 19.50 |
| Best minus worst (each talent) | 30 or more | min 45.4, mean 55.5, max 67.6 |
| Radar axes with the same value for all jobs | 0 | 0 of 400 |
| Exact ties in the top 10 of the employer order (each job) | 2 or fewer | max 1 |
| Near-twin jobs with the same score for a talent | 0 | 0 (the smallest difference is 0.2) |

**Note.** The target is 18 different scores in the top 20 for every talent. With one decimal, two scores that are close can be equal by chance.
For a smooth score with a top-20 range of about 40 points, the chance of more than one equal pair is about 10% for each talent.
The demo weights give at least 19 for all 50 talents (25 talents have exactly 19) when `fit` and `FRS` have one decimal.
With exact values, or with two decimals for the FRS, the result is 17 or 18 for 2 to 4 talents. The real numbers (min and mean) are printed by
`tests/test_differentiation.py --report` and by `run_verification.py`. There is no list-level step that spreads equal scores.

**Demo data caveat.** These values are demo assumptions. They are not statistics and not official data:
the pay benchmarks for a Mid level (Software Engineering 130000, AI & Machine Learning 150000, Data 125000 AUD per year);
the pay step of +22% for each level ($e^{0.20}$); the 220 working days for a day rate (1950 hours for an hourly rate);
the assumed credit for a method or soft skill that a talent did not list (half of the credit at the assumed level $0.5 + 0.3 \cdot r$);
the city centres and the distance scales (700 km Onsite, 900 km Hybrid); and the weights of section 9.
The taxonomy (`monthsToLearn`, `rarity`, `prepMonths`) is a list that people made by hand.

---

## 10. File reference

| Formula | Code | Specification |
| :--- | :--- | :--- |
| F-01 SMF and fit | `intelligence_engine/01_skill_matching_model.py` | `intelligence_engine/01_SKILL_MATCHING_MODEL.md` |
| F-02 gaps and path | `intelligence_engine/02_skill_gap_analysis.py` | `intelligence_engine/02_SKILL_GAP_ANALYSIS.md` |
| F-03 JPI | `intelligence_engine/03_job_to_job_comparison.py` | `intelligence_engine/03_JOB_TO_JOB_COMPARISON.md` |
| F-04 merit areas | `intelligence_engine/04_candidate_benchmarking.py` | `intelligence_engine/04_CANDIDATE_BENCHMARKING.md` |
| F-05 FRS | `intelligence_engine/05_job_seeker_ranking_feed.py` | `intelligence_engine/05_JOB_SEEKER_RANKING_FEED.md` |
| F-06 TSS | `intelligence_engine/06_recruiter_candidate_ranking.py` | `intelligence_engine/06_RECRUITER_CANDIDATE_RANKING.md` |
| Shared helpers | `intelligence_engine/engine_common.py` (must stay next to the six files; `run_verification.py` and the legacy `backend/scores.py` load the formulas, so they use it too) | this file, section 1 |
| Architecture | `intelligence_engine/MASTER_PLAN.md` | |
| Tests | `jinder_platform/tests/test_formulas.py`, `test_differentiation.py`, `run_verification.py` | |
The interactive slide presentation `Presentation/formulas_presentation.html` (and `intelligence_engine/formulas_presentation.html`) presents the complete Version 2 continuous formulas, worked examples, and interactive live calculators.
