# TECHNICAL SPECIFICATION: SKILL MATCH MODEL (SMF) AND TALENT-JOB FIT
**Document Number:** IE-SPEC-001 (version 2)  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Code:** `01_skill_matching_model.py` (with `engine_common.py`)

---

## 1. PURPOSE

This document gives the equations for two scores of a talent and a job:

1. **`evaluate_skill_match`** (SMF). The skill match. The old name and the old keys stay.
2. **`evaluate_job_fit`**. The **fit** of the product. It has a range from 0 to 100 and one decimal. The platform mixes it with the feed score: `score = 0.55 x fit + 0.45 x FRS`.

Both use one analysis (`analyse`). The other formulas (gap, feed, talent search) read the same analysis.

**Rules of version 2.**
- The model is for the ICT product: Software Engineering, AI & Machine Learning and Data.
- The model uses the level (Intern to Principal), the exact years, the skill levels (1 to 5), the certifications, the awards and the work mode.
- No score is a fixed step. Every part is a smooth function of levels, years, rarity, pay or distance. Two different jobs seldom have the same score.
- An unknown value does not give one fixed number for all people. The part uses the other facts (titles, skills, domain).
- The model reads no name, email, country, nationality, visa, age or gender.
- The taxonomy file `../data/reference/ict_taxonomy.json` gives the names, the aliases, the related skills, `monthsToLearn`, `rarity`, the groups, the occupations and the certifications.
  The match of names and aliases ignores the case. If the file is missing, the engine uses simple defaults and still runs.

---

## 2. INPUT (V2_PLAN section 6)

| Object | Keys that the model reads |
| :--- | :--- |
| Talent | `id`, `alias`, `level` or `level_rank`, `years_experience`, `domain`, `specialisation`, `current_title`, `target_roles`, `target_anzsco_code`, `highest_education`, `skills` (name, `level` 1 to 5, `years`, `last_used_year`, `skill_type`), `certifications` (name, issuer, year), `awards` (name, kind, year), `preferred_location`, `locations`, `work_modes`, `work_types` |
| Job | `id`, `title`, `category` (domain), `specialisation`, `level`, `min_years`, `max_years`, `city`, `location`, `work_mode`, `type`, `anzsco_code`, `salary_min`, `salary_max`, `salary_unit`, `required_skills` (name, `level` 1 to 5, `must`), `certifications_required`, `certifications_preferred`, `awards_preferred`, `education_min`, `days_old` |

The old shapes work. A skill can be a text. A job can list `requirements` as text. A missing key has a safe default:
a skill with no level has level 3; a talent with no level gets a level from the title words, then from the years; a job with no years gets the typical years of its level.

---

## 3. SYMBOLS

| Symbol | Meaning | Range |
| :--- | :--- | :--- |
| $h_s$ | Level of the talent in skill $s$ after the fade (section 4.4). 0 if not held. | 0 to 5 |
| $n_s$ | Level that the job needs in skill $s$ | 1 to 5 |
| $c_s$ | Credit of the skill | 0 to 1.12 |
| $u_s$ | Weight of the skill | greater than 0 |
| $r_C$, $r_J$ | Level rank of the talent and of the job (Intern 0, Junior 1, Mid 2, Senior 3, Lead 4, Principal 5) | 0 to 5 |
| $Y$ | Exact years of experience of the talent | 0 to 50 |
| $Y_{\min}$, $Y_{\max}$ | Years that the job asks for ($Y_{\max}$ can be open) | 0 to 40 |
| $O$ | Occupation closeness | 0 to 1 |

---

## 4. THE PER-SKILL MATCH

### 4.1 Weight of a required skill

$$u_s = m_s \cdot \rho_s^{0.6} \cdot (0.7 + 0.1\, n_s)$$

$m_s$ is 2 for a **must** skill and 1 for another skill. $\rho_s$ is the rarity from the taxonomy (1.0 for a common skill, 3.0 for a rare skill). A level 5 skill counts more than a level 1 skill.
This weight is also used by the `path` of Formula 2 and by the compare views.

### 4.2 Credit of a skill

$$c_s = \begin{cases} 1 + 0.12\left(1 - e^{-(h_s - n_s)/1.2}\right) & h_s \ge n_s \quad \text{(a small bonus above the level)} \\[4pt] \left(\dfrac{h_s}{n_s}\right)^{1.3} & 0 < h_s < n_s \quad \text{(partial credit below the level)} \end{cases}$$

Examples for $n_s = 3$: $h = 1$ gives 0.24, $h = 2$ gives 0.59, $h = 3$ gives 1.00, $h = 4$ gives 1.06, $h = 5$ gives 1.09. The function is continuous.

### 4.3 Credit of a related skill

If the talent does not hold the skill, the model looks for the related skills in the taxonomy (`related`; the relation counts in both directions).
With $r = \min(1, \text{best related level} / n_s)$ and $k$ the number of related skills that the talent holds:

$$c_s = \min\left(0.55,\; 0.45\, r^{1.2} + 0.04\,(k - 1)\right)$$

### 4.4 Fade for an old skill

If the year of the last use is known, the level is $h_s = l_s \cdot (0.80 + 0.20\, e^{-a/3})$, where $l_s$ is the level of the talent and $a$ is the years since the last use.

### 4.5 Skill scores

The job skills are split into hard skills and method (and soft) skills with the `kind` of the taxonomy.

$$S_{\text{direct}} = 100 \cdot \min\left(1,\; \frac{\sum_{s \in \text{hard}} u_s c_s}{\sum_{s \in \text{hard}} u_s}\right)$$

$S_{\text{trans}}$ is the same formula over the method skills. The method skills are: the method and soft skills in the list of the job, and the `methods` of the occupation of the job
(level 3, not required, weight $\times 0.4$). The implied methods are not in the skill breakdown.
A method skill that is missing (or only related) gets at least $0.5 \cdot c(a, n_s)$, with $a = 0.5 + 0.3\, r_C$ the assumed level of a person who did not list it.
People seldom list the way they work, and a more senior person works in more ways.

The **coverage** is the level-aware share of the listed skills that the talent meets:

$$\text{coverage} = 100 \cdot \frac{\sum_s u_s \min(1, c_s)}{\sum_s u_s}$$

If a job lists no hard skills, $S_{\text{direct}} = 100\,(0.25 + 0.5\, D)$ ($D$ is the domain fit, 5.5).

The **skill breakdown** has one item for each listed skill: `name`, `group`, `kind`, `must`, `need_level`, `have_level`, `credit`, `weight`, and a `status`:
`meets` ($h_s \ge n_s$), `below` (held, lower level), `related` (only a related skill), `missing`.

---

## 5. THE OTHER PARTS

### 5.1 Level fit $F_{\text{level}}$ (0 to 1)

With $d = r_C - r_J$:

$$F_{\text{level}} = \begin{cases} e^{-0.55\,|d|^{1.2}} & d < 0 \quad \text{(the talent is below the level)} \\ e^{-0.28\, d^{1.2}} & d \ge 0 \quad \text{(the talent is at or above the level)} \end{cases}$$

A step up costs more than a step down: $d = -1$ gives 0.58 and $d = +1$ gives 0.76.

### 5.2 Years fit $F_{\text{years}}$ (0 to 1)

$$F_{\text{years}} = \begin{cases} 0.92\, \exp\left(-\left(\dfrac{Y_{\min} - Y}{s}\right)^{1.4}\right),\; s = \max(1.5,\, 0.6\, Y_{\min}) & Y < Y_{\min} \\[8pt] 0.92 + 0.08\, \dfrac{Y - Y_{\min}}{Y_{\max} - Y_{\min}} & Y_{\min} \le Y \le Y_{\max} \\[8pt] 1 - 0.25\left(1 - e^{-(Y - Y_{\max})/6}\right) & Y > Y_{\max} \end{cases}$$

A job with no maximum is open-ended. Then $F_{\text{years}} = 0.92 + 0.08 \min(1, (Y - Y_{\min})/\max(2, 0.6\, Y_{\min}))$ for $Y \ge Y_{\min}$.
A job with no years uses the typical years of its level (from the taxonomy). The function is continuous.

The experience multiplier of the skill match is $\Phi = 0.78 + 0.27\,(0.55\, F_{\text{years}} + 0.45\, F_{\text{level}})$. It is from 0.78 to 1.05.
The function `calculate_experience_multiplier(years, skill_level)` of the old call still works.

### 5.3 Occupation closeness $O$ (0 to 1)

The talent has up to three kinds of roles: the target occupation (the code), the target roles (titles) and the current title (weight 0.85).
For one role the closeness to the job is the weighted mean of the parts that are known:

| Part | Weight | Value |
| :--- | :---: | :--- |
| Code | 0.26 | $e^{-0.26\,(6 - c)^{1.3}}$, $c$ = the number of equal first digits of the two 6-digit ANZSCO codes (1 for equal codes) |
| Skills | 0.22 | Weighted Jaccard of the core skills of the two occupations in the taxonomy ($\sum \min / \sum \max$ of level $\times$ 1.0 for must, 0.6 for other) |
| Title | 0.22 | Jaccard index of the title words (level words and small words removed) |
| Specialisation | 0.16 | 1 if equal to the specialisation of the talent; 0.85 if the occupation covers it; 0.35 for the same domain; 0.05 otherwise |
| Domain | 0.14 | 1 if equal, 0.15 otherwise |

$O$ is the largest value over the roles of (role weight $\times$ closeness). A job with an unknown code still has a value from the title, the specialisation and the domain.
The talent role is found in the taxonomy by the code, then by the title (the `roles` list), then by the words of the title.

### 5.4 Location and work mode $F_{\text{loc}}$ (0 to 1)

| Work mode of the job | Value |
| :--- | :--- |
| Remote | 1.0 for every talent |
| Onsite | $0.25 + 0.75\, e^{-d/700}$ |
| Hybrid | $0.40 + 0.60\, e^{-d/900}$ |

$d$ is the distance in km from the nearest preferred city of the talent to the city of the job (great-circle distance of the city centres).
If the talent chose a work mode and the job mode is not in the list (and the job is not Remote), the value is $\times\, 0.9$.
If a city is not known, the base value is 0.6. A talent who wants only Remote work and gives no city has 0.40 for an Onsite job and 0.60 for a Hybrid job.

### 5.5 Domain fit $F_{\text{dom}}$ (0 to 1)

$$F_{\text{dom}} = 0.5 \cdot \mathbb{1}[\text{declared domain} = \text{job domain}]_{(1 \text{ or } 0.15)} + 0.5 \cdot \frac{\text{share of the skills of the talent in the job domain}}{\text{share in the top domain of the talent}}$$

Each skill of the talent gives its level, shared by the domains that it belongs to in the taxonomy.

### 5.6 Work type $F_{\text{type}}$ (0 to 1)

1 if the job type is one of the types that the talent chose. Otherwise the best similarity: Full-time and Part-time 0.50, Full-time and Contract 0.40, Part-time and Contract 0.50,
Graduate / Internship and Full-time 0.45, and 0.20 or less for other pairs.

### 5.7 Education $F_{\text{edu}}$ (0.2 to 1)

Education is a **soft factor**. It is never a hard limit and it never gives 0.

$$F_{\text{edu}} = \begin{cases} 1 & e_C \ge e_J \\ 0.2 + 0.8\, e^{-0.7\,(e_J - e_C)} & e_C < e_J \end{cases}$$

$e$ is the education rank (Certificate 1, Diploma 2, Bachelor 3, Master 4, PhD 5). A talent with no qualification has $e_C = 0$. A job with no minimum has no education part.

### 5.8 Certifications (adjustment in points)

Each certification that the job lists has a credit: 1 if the talent holds it (the name is matched in any case, with aliases).
If not, the credit is 0.30 (required) or 0.25 (preferred) times $k$, the mean of $\min(1, h/3)$ over the skills that the certification shows.
Required ones count 2 and preferred ones count 1:

$$G = \frac{\sum_i w_i\, \text{credit}_i}{\sum_i w_i} \qquad \text{adjustment} = 7\,(G - 0.45)$$

A job that lists no certification gets no adjustment. A held required certification removes the gap (see Formula 2).

### 5.9 Awards (bonus in points)

$A$ is the mean over the preferred award kinds of the job: 0 if the talent has no award of that kind; else $\max(0.6 + 0.4\, e^{-\text{age}/6})$ over the awards of that kind (0.8 if the year is not known).
The bonus is $3 \cdot A$ points. It is at most 3 points.

---

## 6. THE SKILL MATCH (SMF)

$$SMF = \min\left(100,\; \left(0.25\, S_{\text{tree}} + 0.50\, S_{\text{direct}} + 0.25\, S_{\text{trans}}\right) \cdot \Phi\right) \qquad S_{\text{tree}} = 100\, O$$

The tiers (labels only): 85 or more "Direct Industry Alignment"; 70 to 84.9 "Transferable Cross-Sector Capability"; less than 70 "Emerging Career Bridge".
The sub-metrics keep their old keys: `s_tree_taxonomy`, `s_direct_competency`, `s_trans_methodology`, `phi_experience_multiplier`. The new keys are `s_level_fit` and `s_years_fit`.

---

## 7. THE PRODUCT FIT

$$\text{fit} = \text{clip}_{[0,100]}\left(100\,\frac{\sum_i w_i P_i}{\sum_i w_i} + \text{certification adjustment} + \text{award bonus}\right)$$

The sum runs over the parts that apply to the job. A part that does not apply is left out and the other weights grow, so that the total weight is 1.

| Part $P_i$ | Value | Weight $w_i$ |
| :--- | :--- | :---: |
| skills | $S_{\text{direct}} / 100$ | 0.39 |
| methods | $S_{\text{trans}} / 100$ | 0.04 |
| occupation | $O$ | 0.16 |
| level | $F_{\text{level}}$ | 0.10 |
| experience | $F_{\text{years}}$ | 0.09 |
| domain | $F_{\text{dom}}$ | 0.10 |
| location | $F_{\text{loc}}$ | 0.07 |
| work_type | $F_{\text{type}}$ | 0.02 |
| education | $F_{\text{edu}}$ | 0.03 |

The weights are the defaults of the demo. They were tuned on the 50 jobs and 50 talents of `data/synthetic`, inside these limits: skills 0.26 to 0.40, occupation 0.10 to 0.20, level 0.09 to 0.16,
experience 0.06 to 0.12, domain 0.04 to 0.11, location 0.06 to 0.12, so that jobs seldom have the same score (see `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, section 9).
The function `evaluate_job_fit(candidate, job, weights=None)` takes a dictionary to change them.

---

## 8. WORKED EXAMPLE

Talent: level Mid, 4.0 years, Bachelor's degree, domain Data, specialisation Data analytics, current title Data Analyst, target role Data Engineer.
Skills (level): SQL 4, Python 3, Tableau 3, Communication 4. Award: hackathon (2024). Place: Sydney, Hybrid, Full-time.
Job: Senior Data Engineer (code 262111, Data, Data engineering), Senior, 5 to 9 years, Sydney, Hybrid, Full-time, Bachelor's degree.
Skills (needed level, must): SQL 4 (must), Python 4 (must), Apache Airflow 3 (must), Data modelling 3, Communication 3.
Preferred certification: dbt Analytics Engineering Certification. Preferred award: hackathon. Reference year 2026.

| Skill | Weight $u$ | $h$ | Credit | Status |
| :--- | :---: | :---: | :---: | :--- |
| SQL | 2.20 | 4 | 1.000 | meets |
| Python | 2.20 | 3 | $(3/4)^{1.3} = 0.688$ | below |
| Apache Airflow | 2.75 | none (related: Python) | 0.45 | related |
| Data modelling | 1.37 | none (related: SQL) | 0.45 | related |
| Communication | 1.00 | 4 | $1 + 0.12(1 - e^{-1/1.2}) = 1.068$ | meets |

1. **Hard skills.** $S_{\text{direct}} = 100 \cdot (2.20 + 1.514 + 1.237 + 0.619) / 8.525 = 65.3$.
2. **Methods.** The job occupation adds 5 methods (weight $\times 0.4$). A Mid talent has an assumed level of $0.5 + 0.3 \cdot 2 = 1.1$, so a missing method gets $0.5 \cdot (1.1/3)^{1.3} = 0.14$. $S_{\text{trans}} = 52.7$.
3. **Occupation.** The target role equals the job: code 1.0, skills 1.0, title 1.0, specialisation 0.85 (the occupation covers it), domain 1.0. $O = 0.976$.
4. **Level.** $d = 2 - 3 = -1$. $F_{\text{level}} = e^{-0.55} = 0.577$.
5. **Years.** $Y = 4 < Y_{\min} = 5$, $s = 3.0$. $F_{\text{years}} = 0.92\, e^{-(1/3)^{1.4}} = 0.742$.
6. **Domain, place, type, education.** All are 1.0.
7. **Certification.** The talent holds none. $k = 0.25$, credit $= 0.25 \cdot 0.25 = 0.0625$. Adjustment $= 7\,(0.0625 - 0.45) = -2.71$.
8. **Award.** The talent holds a hackathon award 2 years old: $0.6 + 0.4\, e^{-1/3} = 0.887$. Bonus $= +2.66$.
9. **Fit.** $0.39 \cdot 65.3 + 0.04 \cdot 52.7 + 0.16 \cdot 97.6 + 0.10 \cdot 57.7 + 0.09 \cdot 74.2 + 0.10 \cdot 100 + 0.07 \cdot 100 + 0.02 \cdot 100 + 0.03 \cdot 100 = 77.66$.
   $\text{fit} = 77.66 - 2.71 + 2.66 = \mathbf{77.6}$.
10. **Skill match.** $\Phi = 0.78 + 0.27\,(0.55 \cdot 0.742 + 0.45 \cdot 0.577) = 0.960$. $SMF = (0.25 \cdot 97.6 + 0.50 \cdot 65.3 + 0.25 \cdot 52.7) \cdot 0.960 = 70.2 \cdot 0.960 = \mathbf{67.4}$ ("Emerging Career Bridge").
11. **Coverage.** 69.0.

---

## 9. FUNCTIONS AND OUTPUT

| Function | Result |
| :--- | :--- |
| `evaluate_skill_match(candidate, job_or_code, weights=(0.25, 0.50, 0.25))` | `candidate_id`, `candidate_name` (the alias), `target_anzsco_code`, `target_anzsco_title`, `sub_metrics`, `competency_breakdown`, `skill_breakdown`, `skill_coverage`, `base_composite_score`, `final_match_score`, `overall_score`, `match_tier`, `match_tier_code`, `is_direct_ready` |
| `evaluate_job_fit(candidate, job, weights=None)` | `fit`, `fit_exact`, `parts` (10 values from 0 to 100, or null), `weights` (the weights that were used), `bonus` (`certifications`, `awards`), `skill_breakdown`, `skill_coverage`, `counts` (required, meets, below, related, missing), `level` (candidate, job, estimated, gap), `years` (candidate, min, max, known), `certifications`, `awards`, `occupation`, `candidate_id`, `job_id` |
| `analyse(candidate, job, shared_only=False)` | The shared analysis (all parts from 0 to 1). It is for the other formula files. |

The `competency_breakdown` keeps its old keys. `statutory_requirements` now lists the required certifications.
The functions `calculate_taxonomy_tree_score`, `calculate_competency_overlap`, `extract_candidate_text_corpus` and `tokenize_text` of version 1 stay.
