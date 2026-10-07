# TECHNICAL SPECIFICATION: JOB-TO-JOB COMPARISON AND SUBSTITUTABILITY MODEL (JJF)
**Document Number:** IE-SPEC-003  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Classification:** Core Algorithm Specification  

---

## 1. IDENTIFICATION AND PURPOSE

This document gives the mathematical formula and the calculation steps for the Job-to-Job Comparison Function (JJF).  
The algorithm compares two or more Australian job vacancies.  
The algorithm helps job seekers:
1. Find adjacent career opportunities.
2. Calculate skill overlap between different jobs.
3. Compare salary ranges and work conditions.
4. Measure career mobility between different Australian industries.

---

## 2. APPLICABLE DOCUMENTS

The algorithm uses principles from these reference papers and standards:

1. **Le et al. (WWW 2019):** Job2Vec: Learning Representations of Jobs for Career Path Modeling.
2. **Sivani et al. (ACM RecSys 2021):** Multi-Aspect Job Similarity in Online Recruitment.
3. **Australian Bureau of Statistics (ABS):** ANZSCO Major and Minor Group Crosswalks.

---

## 3. TECHNICAL TERMS AND DEFINITIONS

| Term | Approved Definition |
| :--- | :--- |
| **Job Proximity Index ($JPI$)** | A numerical score from 0.0 to 100.0 that shows how similar two jobs are. |
| **Substitutable Role** | A job that a worker can do with their current skills with minimal retraining. |
| **Adjacent Career Path** | A role in a different sub-sector with high transferable methodology overlap. |
| **Compensation Delta ($\Delta_{\text{sal}}$)** | The difference between the midpoint annual salaries of two jobs in Australian Dollars (AUD). |

---

## 4. MATHEMATICAL FORMULATION

### 4.1 Master Equation for Pairwise Proximity ($JPI$)

Let $J_a$ and $J_b$ be two Australian job vacancies.  
The algorithm calculates the Job Proximity Index ($JPI$):

$$JPI(J_a, J_b) = \sum_{k=1}^{5} w_k \cdot S_k(J_a, J_b) \quad \in [0.0, 100.0]$$

### 4.2 Approved Parameter Weights

The weights must obey this condition:

$$\sum_{k=1}^{5} w_k = 0.30 + 0.35 + 0.15 + 0.10 + 0.10 = 1.00$$

- $w_1 = 0.30$ (Taxonomy Tree Proximity: $S_{\text{tree}}$)
- $w_2 = 0.35$ (Requirement & Skill Jaccard Overlap: $S_{\text{req}}$)
- $w_3 = 0.15$ (Salary Parity: $S_{\text{comp}}$)
- $w_4 = 0.10$ (Sector Affinity: $S_{\text{sector}}$)
- $w_5 = 0.10$ (Geographic and Work Mode Alignment: $S_{\text{geo}}$)

---

## 5. SUB-METRIC DEFINITIONS

### 5.1 Taxonomy Tree Proximity ($S_{\text{tree}}$)
Calculated from the ABS ANZSCO 6-digit codes:
- Same 6 digits: $100.0\%$
- Same 4 digits (Unit Group): $85.0\%$
- Same 3 digits (Minor Group): $65.0\%$
- Same 2 digits (Sub-Major Group): $40.0\%$
- Same 1 digit (Major Group): $20.0\%$
- Different: $0.0\%$

### 5.2 Requirement Overlap ($S_{\text{req}}$)
Let $R_a$ and $R_b$ be token sets extracted from the requirements of $J_a$ and $J_b$:

$$S_{\text{req}}(J_a, J_b) = \frac{|R_a \cap R_b|}{|R_a \cup R_b|} \times 100.0$$

### 5.3 Compensation Parity ($S_{\text{comp}}$)
Let $M_a = \frac{\text{Min}_a + \text{Max}_a}{2}$ and $M_b = \frac{\text{Min}_b + \text{Max}_b}{2}$ be the midpoint annual salaries in AUD:

$$S_{\text{comp}}(J_a, J_b) = \max\left(0.0, \; \left(1.0 - \frac{|M_a - M_b|}{\max(M_a, M_b, 1.0)}\right) \times 100.0\right)$$

### 5.4 Sector Affinity ($S_{\text{sector}}$)
- Same industry sector: $100.0\%$
- Related transferable sectors (e.g. Operations $\leftrightarrow$ Supply Chain): $65.0\%$
- Unrelated sectors: $25.0\%$

### 5.5 Geographic & Work Mode Alignment ($S_{\text{geo}}$)
- Same metropolitan area or both Remote: $100.0\%$
- Same Australian state (e.g., NSW): $75.0\%$
- Interstate metropolitan areas: $50.0\%$
- Capital city vs remote regional: $25.0\%$

---

## 6. N-ARY (MULTI-JOB) COMPARISON

When a job seeker compares $N$ jobs ($N \ge 2$), the algorithm computes:
1. **Pairwise Proximity Matrix ($N \times N$):** All mutual $JPI$ scores.
2. **Salary Difference Vector:**
   $$\Delta_{\text{sal}}(J_b, J_a) = M_b - M_a$$
3. **Skill Additions and Deletions:**
   - Skills needed in $J_b$ but not in $J_a$: $R_b \setminus R_a$
   - Skills in $J_a$ that are not required in $J_b$: $R_a \setminus R_b$

---

## 7. OPERATIONAL TIER CLASSIFICATION

The algorithm classifies the relationship into three tiers:

```
[JPI >= 80.0]  --> DIRECTLY SUBSTITUTABLE
                   Job seeker can apply to both jobs with the same primary CV.

[60.0 <= JPI < 80.0] --> ADJACENT CAREER MOBILITY
                         Job seeker can transition with minor CV tailoring.

[JPI < 60.0]   --> CROSS-DISCIPLINARY CAREER PIVOT
                   Roles have significant differences in core tasks and requirements.
```

---

## 8. VERIFICATION EXAMPLE

### 8.1 Input Data
- **Job A:** *Data Engineer (ekino Vietnam / Australia)* — ANZSCO `261313`, \$140,000 AUD, Sydney
- **Job B:** *Analytics Engineer (Entobel / Australia)* — ANZSCO `261312`, \$130,000 AUD, Sydney

### 8.2 Step-by-Step Calculation
1. **Taxonomy Tree ($S_{\text{tree}}$):**
   Both jobs are in Unit Group `2613` (Software & Applications Programmers) $\implies S_{\text{tree}} = 85.0\%$.

2. **Requirements Overlap ($S_{\text{req}}$):**
   Shared competencies: `sql`, `python`, `data pipeline`, `orchestration`, `dbt`, `git`.  
   Overlap ratio: $75.0\%$.

3. **Compensation Parity ($S_{\text{comp}}$):**
   $$S_{\text{comp}} = \left(1.0 - \frac{|140000 - 130000|}{140000}\right) \times 100.0 = \left(1.0 - \frac{10000}{140000}\right) \times 100.0 = 92.9\%$$

4. **Sector Affinity ($S_{\text{sector}}$):**
   Both are *Technology & Data* $\implies S_{\text{sector}} = 100.0\%$.

5. **Geographic Alignment ($S_{\text{geo}}$):**
   Both are *Sydney Metro* $\implies S_{\text{geo}} = 100.0\%$.

6. **Calculate Master Proximity ($JPI$):**
   $$JPI = (0.30 \times 85.0) + (0.35 \times 75.0) + (0.15 \times 92.9) + (0.10 \times 100.0) + (0.10 \times 100.0)$$
   $$JPI = 25.5 + 26.25 + 13.94 + 10.0 + 10.0 = \mathbf{85.7\%}$$

7. **Determine Operational Tier:**
   $JPI = 85.7\% \ge 80.0\% \implies \textbf{DIRECTLY SUBSTITUTABLE}$.
