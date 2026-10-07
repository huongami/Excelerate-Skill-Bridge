# Jinder — Mathematical Formulas & Scoring Engine Specification (ASD-STE100)

**Standard:** ASD-STE100 Issue 8 Compliant Technical Specification  
**Architecture:** 6 Deterministic Continuous Models (Zero Static Defaults, Zero PII Leakage)  
**Visual Reference:** Open [`../intelligence_engine/formulas_presentation.html`](../intelligence_engine/formulas_presentation.html) in your browser for live KaTeX equations and interactive sliders.

---

## 1. Executive Summary & Design Principles

The **Jinder Intelligence Engine** evaluates candidate skills and job requirements using exact mathematical models. It completely avoids coarse round integers, arbitrary scoring tables, and heuristic guessing.

### Core Mathematical Commitments:
1. **Zero Static Defaults:** Every candidate and job generates distinct, continuous decimal scores (e.g. `90.2%` vs `88.5%`).
2. **Continuous Experience Multipliers:** Experience curves use logarithmic and Gaussian scaling functions rather than step-function cliffs.
3. **Deterministic Execution:** Identical inputs yield identical outputs in under 5 milliseconds.
4. **Zero PII Bias:** Personal identifiers (names, photos, genders) are scrubbed before evaluation.

---

## 2. Formula 1: Candidate vs ANZSCO Skill Match Model (SMF)

### 2.1 Formula
$$\text{SMF}(C, O) = \min\left(100.0, \, \left(0.25 S_{\text{tree}} + 0.50 S_{\text{direct}} + 0.25 S_{\text{trans}}\right) \times \Phi(Y_C, L_O)\right)$$

### 2.2 Continuous Experience Multiplier $\Phi(Y_C, L_O)$
$$\Phi(Y_C, L_O) = 0.80 + 0.15 \ln\left(1 + \frac{Y_C}{Y_{\text{req}}(L_O)}\right) + 0.05 \min\left(2.0, \frac{Y_C}{Y_{\text{req}}(L_O)}\right)$$
Clamped strictly to $[0.75, 1.15]$.

### 2.3 Component Definitions
- **$S_{\text{tree}}$ (25%):** Hierarchical ANZSCO code tree overlap (100% for 6-digit exact match, 85% for 4-digit unit group match, 65% for 2-digit sub-major match).
- **$S_{\text{direct}}$ (50%):** Inverse Document Frequency (IDF)-weighted skill vector overlap between candidate verified skills and occupational requirements.
- **$S_{\text{trans}}$ (25%):** Universal methodology agile score (quality assurance, compliance, crisis management, leadership).

---

## 3. Formula 2: Skill Gap Severity & Job Readiness Model (GSI & JRS)

### 3.1 Gap Severity Index (GSI)
$$\text{GSI}(C, J) = \min\left(95.0, \, \max\left(2.0, \, \sum_{k=1}^m W_{\text{cat}}(g_k) \times \left(14.0 + 4.5 \ln\left(1 + T_k \cdot \lambda_{\text{lrn}}\right)\right) + S_{\text{sen\_deficit}}\right)\right)$$

### 3.2 Job Readiness Score (JRS)
$$\text{JRS}(C, J) = \max\left(5.0, \, 100.0 - \text{GSI}(C, J)\right)$$

### 3.3 Parallel Learning Bridge Duration ($T_{\text{total}}$)
$$T_{\text{total}} = \max_k\left(T_k \cdot \lambda_{\text{lrn}}\right) + 0.18 \sum_{k \neq \max} \left(T_k \cdot \lambda_{\text{lrn}}\right)$$

### 3.4 Gap Category Weights ($W_{\text{cat}}$)
- **CAT-1: Statutory License / Legal Registration (AHPRA, CPA, Bar):** $W = 1.00$, Base duration = 8.0 months.
- **CAT-2: Core Discipline Competency (Clinical Triage, Distributed Systems):** $W = 0.60$, Base duration = 4.0 months.
- **CAT-3: Tool / Platform / Framework (Snowflake, dbt, Revit):** $W = 0.25$, Base duration = 1.5 months.
- **CAT-4: Local Standard / Orientation (PBS billing, WHS laws):** $W = 0.10$, Base duration = 0.8 months.

### 3.5 Learnability Acceleration Factor ($\lambda_{\text{lrn}}$)
$$\lambda_{\text{lrn}} = 0.82 \quad \text{if candidate holds a Bachelor/Master/PhD degree; else } 1.00$$

---

## 4. Formula 3: Job Proximity Index (JPI)

### 4.1 Formula
$$\text{JPI}(J_A, J_B) = 0.35 S_{\text{tree}} + 0.35 S_{\text{req}} + 0.15 S_{\text{comp}} + 0.10 S_{\text{sec}} + 0.05 S_{\text{geo}}$$

### 4.2 Continuous Compensation Parity ($S_{\text{comp}}$)
$$S_{\text{comp}} = 100.0 \times \exp\left(-\frac{|\text{Sal}_A - \text{Sal}_B|}{\max(\text{Sal}_A, \text{Sal}_B) \times 0.60}\right)$$

### 4.3 Interpretation
- $\ge 80\%$: Direct Lateral Transfer.
- $60\% - 79\%$: Adjacent Career Mobility.
- $< 60\%$: Cross-Disciplinary Career Pivot.

---

## 5. Formula 4: Candidate Benchmarking & Relative Merit Score (RMS)

### 5.1 Relative Merit Score
$$\text{RMS}(C) = 0.40 S_{\text{direct}} + 0.25 \left(100 \times \frac{\Phi(Y_C) - 0.75}{0.40}\right) + 0.20 S_{\text{trans}} + 0.15 \left(100 \times (1.0 - \lambda_{\text{lrn}})\right)$$

### 5.2 Head-to-Head Comparison Delta
$$\Delta(C_A, C_B) = \text{RMS}(C_A) - \text{RMS}(C_B)$$
If $|\Delta| \le 3.0 \text{ pts}$, candidates are in the **Equivalent Competency Band**; recruiters should evaluate domain portfolio instead of raw tenure.

---

## 6. Formula 5: Job Seeker Feed Ranking (FRS) & Behavioural Loop

### 6.1 Base Feed Score
$$\text{FRS}(C, J) = 0.45 \times \text{SMF} + 0.25 \times \text{JRS} + 0.15 \times S_{\text{comp\_fit}} + 0.10 \times S_{\text{geo}} + 0.05 \times S_{\text{fresh}}$$

### 6.2 Freshness Decay
$$S_{\text{fresh}} = 100.0 \times \exp\left(-\frac{\text{Age in Days}}{28.0}\right)$$

### 6.3 Behavioural Affinity Loop ($\text{FRS}^*$)
- **Saved Employer Affinity:** $+10\%$ if applicant previously saved a vacancy from this employer.
- **Saved Sector Affinity:** $+5\%$ if applicant previously saved a vacancy in this sector.
- **Ignore Penalty:** $-25\%$ if applicant ignored $\ge 3$ vacancies from this employer.
Clamped to $[0.0, 100.0]$.

---

## 7. Formula 6: Recruiter Talent Search Score (TSS)

### 7.1 Formula
$$\text{TSS}(C, R) = \min\left(100.0, \, \left(0.50 S_{\text{req}} + 0.20 S_{\text{trans}} + 0.20 S_{\text{sen}} + 0.10 S_{\text{growth}}\right) \times M_{\text{statutory}}\right)$$

### 7.2 Continuous Seniority Parity ($S_{\text{sen}}$)
$$S_{\text{sen}} = 100.0 \times \exp\left(-\frac{(Y_C - Y_{\text{req}})^2}{2 \times (2.5)^2}\right) \quad \text{for } Y_C < Y_{\text{req}}$$
$$S_{\text{sen}} = \min\left(100.0, \, 90.0 + 2.0 \times (Y_C - Y_{\text{req}})\right) \quad \text{for } Y_C \ge Y_{\text{req}}$$

### 7.3 Statutory Multiplier ($M_{\text{statutory}}$)
$$M_{\text{statutory}} = 0.40 \quad \text{if a mandatory license (AHPRA, CPA) is missing; else } 1.00$$

---

## 8. File Reference Matrix

| Formula | Python Implementation | Technical Spec Markdown |
| :--- | :--- | :--- |
| **F-01 (SMF)** | `intelligence_engine/01_skill_matching_model.py` | `intelligence_engine/01_SKILL_MATCHING_MODEL.md` |
| **F-02 (GSI & JRS)** | `intelligence_engine/02_skill_gap_analysis.py` | `intelligence_engine/02_SKILL_GAP_ANALYSIS.md` |
| **F-03 (JPI)** | `intelligence_engine/03_job_to_job_comparison.py` | `intelligence_engine/03_JOB_TO_JOB_COMPARISON.md` |
| **F-04 (RMS)** | `intelligence_engine/04_candidate_benchmarking.py` | `intelligence_engine/04_CANDIDATE_BENCHMARKING.md` |
| **F-05 (FRS)** | `intelligence_engine/05_job_seeker_ranking_feed.py` | `intelligence_engine/05_JOB_SEEKER_RANKING_FEED.md` |
| **F-06 (TSS)** | `intelligence_engine/06_recruiter_candidate_ranking.py` | `intelligence_engine/06_RECRUITER_CANDIDATE_RANKING.md` |
| **Full Pipeline** | `intelligence_engine/MASTER_PLAN.md` | `intelligence_engine/formulas_presentation.html` |
