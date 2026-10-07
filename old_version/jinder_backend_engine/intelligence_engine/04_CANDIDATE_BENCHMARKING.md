# TECHNICAL SPECIFICATION: CANDIDATE-TO-CANDIDATE BENCHMARKING MODEL (CCF)
**Document Number:** IE-SPEC-004  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Classification:** Core Algorithm Specification  

---

## 1. IDENTIFICATION AND PURPOSE

This document gives the mathematical formula and the calculation steps for the Candidate-to-Candidate Comparison Function (CCF).  
The algorithm compares two or more job applicants for HR recruiters and talent acquisition teams.  
The algorithm calculates:
1. The Relative Merit Score ($RMS$) of each candidate.
2. The Head-to-Head Competitive Score Delta ($\Delta$).
3. The Multi-Candidate Cohort Rank.
4. The Dimensional Strengths and Trade-off Breakdown.

---

## 2. APPLICABLE DOCUMENTS

The algorithm uses principles from these reference papers and standards:

1. **Keeney & Raiffa (1993):** Decisions with Multiple Objectives: Preferences and Value Tradeoffs (Multi-Attribute Utility Theory - MAUT).
2. **Saaty (1990):** How to Make a Decision: The Analytic Hierarchy Process (AHP).
3. **Bradley & Terry (1952):** The Rank Analysis of Incomplete Block Designs (Pairwise Comparison Models).

---

## 3. TECHNICAL TERMS AND DEFINITIONS

| Term | Approved Definition |
| :--- | :--- |
| **Relative Merit Score ($RMS$)** | A normalized score from 0.0 to 100.0 that measures total candidate capability. |
| **Score Delta ($\Delta$)** | The numerical difference between the merit scores of Candidate A and Candidate B. |
| **Skill Depth** | The volume and specificity of verified technical skills in the primary domain. |
| **Experience Maturity** | The verified career duration compared to the Australian senior benchmark (8 years). |
| **Evidence Rigor** | The level of quantifiable metrics and verifiable proof in the CV text. |
| **Regulatory Gap Penalty** | A deduction for missing Australian statutory registrations or licenses. |

---

## 4. MATHEMATICAL FORMULATION

### 4.1 Master Equation for Candidate Relative Merit Score ($RMS$)

For candidate $C_i$, the algorithm calculates $RMS(C_i)$:

$$RMS(C_i) = \max\Big(0.0, \; \min\big(100.0, \; \alpha \cdot \text{Depth}_i + \beta \cdot \text{Exp}_i + \gamma \cdot \text{Evidence}_i + \delta \cdot \text{Trans}_i - \epsilon \cdot \text{GapPen}_i\big)\Big)$$

### 4.2 Approved Parameter Weights

The positive weights must obey this condition:

$$\alpha + \beta + \gamma + \delta = 0.35 + 0.25 + 0.20 + 0.10 = 0.90$$
$$\epsilon = 0.10 \text{ (Regulatory Gap Penalty Weight)}$$

- $\alpha = 0.35$ (Skill Depth Weight)
- $\beta = 0.25$ (Experience Maturity Weight)
- $\gamma = 0.20$ (Evidence Rigor Weight)
- $\delta = 0.10$ (Transferable Agility Weight)
- $\epsilon = 0.10$ (Statutory Gap Deduction Weight)

---

## 5. DIMENSIONAL SUB-METRICS

### 5.1 Skill Depth ($\text{Depth}_i$)
Let $N_{\text{direct}}$ be the number of verified direct industry skills in the profile:

$$\text{Depth}_i = \min\left(100.0, \; 25.0 + (N_{\text{direct}} \times 25.0)\right)$$

### 5.2 Experience Maturity ($\text{Exp}_i$)
Let $Y_i$ be verified years of experience. The benchmark for senior maturity is 8.0 years:

$$\text{Exp}_i = \min\left(100.0, \; \frac{Y_i}{8.0} \times 100.0\right)$$

### 5.3 Evidence Rigor ($\text{Evidence}_i$)
Let $L_{\text{cv}}$ be the word count of verified resume excerpts.  
Let $Q_{\text{metric}}$ be the number of numerical performance indicators (e.g. percentages, budgets, team sizes):

$$\text{Evidence}_i = \min\left(100.0, \; \min(50.0, L_{\text{cv}} \times 0.25) + \min(50.0, Q_{\text{metric}} \times 12.5)\right)$$

### 5.4 Transferable Agility ($\text{Trans}_i$)
Measures leadership, standard operating procedures, and cross-functional coordination:

$$\text{Trans}_i = \min\left(100.0, \; 40.0 + (N_{\text{transferable}} \times 20.0)\right)$$

### 5.5 Regulatory Gap Penalty ($\text{GapPen}_i$)
- If candidate has an active statutory blocker (e.g., requires AHPRA, CPA, or NER): $\text{GapPen}_i = 75.0$
- If candidate has a minor local orientation gap: $\text{GapPen}_i = 20.0$
- If candidate has zero gaps: $\text{GapPen}_i = 0.0$

---

## 6. HEAD-TO-HEAD CANDIDATE COMPARISON ($\Delta$)

The algorithm calculates the competitive score delta between Candidate A and Candidate B:

$$\Delta(C_a, C_b) = RMS(C_a) - RMS(C_b)$$

### Decision Rules:
1. **Clear Advantage ($\Delta > +8.0$):**
   Candidate A demonstrates superior capability, deeper experience, or higher regulatory readiness.
2. **Equivalent Merit Tier ($|\Delta| \le 8.0$):**
   Candidates are in the same capability band. HR should select based on specific cultural fit or niche tool specialization.
3. **Clear Disadvantage ($\Delta < -8.0$):**
   Candidate B demonstrates superior capability over Candidate A.

---

## 7. MULTI-CANDIDATE COHORT RANKING ($N \ge 2$)

When HR compares an applicant pool for an open role:
1. The algorithm computes $RMS(C_i)$ for all candidates $i = 1 \dots N$.
2. The algorithm sorts candidates in descending order of $RMS$.
3. The algorithm calculates the cohort percentile:
   $$\text{Percentile}(C_i) = \frac{\text{Rank}(C_i) - 1}{N - 1} \times 100.0$$

---

## 8. VERIFICATION EXAMPLE

### 8.1 Input Data
- **Candidate A:** Minh Tuan Nguyen (10 yrs exp, clinical practice manager, requires AHPRA)
  - Direct Skills: 3 ($N_{\text{direct}} = 3 \implies \text{Depth} = 100.0$)
  - Experience: 10 yrs ($\text{Exp} = 100.0$)
  - Evidence: High ($\text{Evidence} = 90.0$)
  - Transferable: 3 ($N_{\text{trans}} = 3 \implies \text{Trans} = 100.0$)
  - Gap: AHPRA licensing blocker ($\text{GapPen} = 75.0$)

- **Candidate B:** Junior Clinic Nurse (3 yrs exp, staff nurse, requires AHPRA)
  - Direct Skills: 1 ($\text{Depth} = 50.0$)
  - Experience: 3 yrs ($\text{Exp} = 37.5$)
  - Evidence: Moderate ($\text{Evidence} = 65.0$)
  - Transferable: 1 ($\text{Trans} = 60.0$)
  - Gap: AHPRA licensing blocker ($\text{GapPen} = 75.0$)

### 8.2 Step-by-Step Calculation
1. **Calculate Merit Score for Candidate A ($RMS_A$):**
   $$RMS_A = (0.35 \times 100.0) + (0.25 \times 100.0) + (0.20 \times 90.0) + (0.10 \times 100.0) - (0.10 \times 75.0)$$
   $$RMS_A = 35.0 + 25.0 + 18.0 + 10.0 - 7.5 = \mathbf{80.5}$$

2. **Calculate Merit Score for Candidate B ($RMS_B$):**
   $$RMS_B = (0.35 \times 50.0) + (0.25 \times 37.5) + (0.20 \times 65.0) + (0.10 \times 60.0) - (0.10 \times 75.0)$$
   $$RMS_B = 17.5 + 9.38 + 13.0 + 6.0 - 7.5 = \mathbf{38.4}$$

3. **Calculate Head-to-Head Delta ($\Delta$):**
   $$\Delta(A, B) = 80.5 - 38.4 = \mathbf{+42.1\text{ points}}$$

4. **Determine Evaluation Verdict:**
   $\Delta > +8.0 \implies \textbf{Candidate A demonstrates significant senior leadership and operational superiority}$.
