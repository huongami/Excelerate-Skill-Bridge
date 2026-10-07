# TECHNICAL SPECIFICATION: RECRUITER TALENT SEARCH RANKING ENGINE (TSR)
**Document Number:** IE-SPEC-006  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Classification:** Core System Algorithm Specification  

---

## 1. IDENTIFICATION AND PURPOSE

This document gives the mathematical formula and the calculation steps for the Recruiter Talent Search Ranking Function (TSR).  
The algorithm ranks and sorts candidate profiles displayed to HR recruiters for a specific Australian job vacancy.  
The algorithm optimizes:
1. Requisition capability match.
2. Experience seniority parity.
3. Verifiable CV evidence rigor.
4. Australian statutory credential readiness.
5. Algorithmic fairness and zero Personally Identifiable Information (PII) bias.

---

## 2. APPLICABLE DOCUMENTS

The algorithm uses principles from these reference papers and standards:

1. **Ha-Thuc et al. (ACM SIGIR 2015):** Search and Recommendation Systems for LinkedIn Recruiter.
2. **Peng et al. (ACM KDD 2020):** Fair and Balanced Two-Sided Marketplace Search.
3. **Australian Privacy Act 1988 (Cth):** Privacy and Personal Information Governance Standards.

---

## 3. TECHNICAL TERMS AND DEFINITIONS

| Term | Approved Definition |
| :--- | :--- |
| **Talent Search Score ($TSS$)** | The final sorting score that sets the display position of a candidate on the recruiter dashboard. |
| **Requisition Fit ($S_{\text{req}}$)** | The degree of overlap between candidate competencies and job requirements. |
| **Seniority Parity ($S_{\text{sen}}$)** | How well the candidate experience matches the seniority level demanded by the employer. |
| **Statutory Readiness ($S_{\text{reg}}$)** | The candidate credential status regarding Australian regulatory registrations. |
| **Fairness Constraint** | Removal of age, gender, nationality, and photo identifiers to prevent unconscious bias. |

---

## 4. MATHEMATICAL FORMULATION

### 4.1 Talent Search Master Equation

For candidate $C_i$ and target job requisition $J$, the algorithm calculates the Talent Search Score ($TSS$):

$$TSS(C_i \mid J) = w_{\text{req}} \cdot S_{\text{req}} + w_{\text{sen}} \cdot S_{\text{sen}} + w_{\text{evid}} \cdot S_{\text{evid}} + w_{\text{reg}} \cdot S_{\text{reg}} + w_{\text{audit}} \cdot S_{\text{audit}}$$

### 4.2 Approved Parameter Weights

The weights must obey this condition:

$$\sum w = 0.40 + 0.25 + 0.15 + 0.15 + 0.05 = 1.00$$

- $w_{\text{req}} = 0.40$ (Job Requisition Fit Weight)
- $w_{\text{sen}} = 0.25$ (Seniority Parity Weight)
- $w_{\text{evid}} = 0.15$ (Verifiable Evidence Rigor Weight)
- $w_{\text{reg}} = 0.15$ (Regulatory & Licensing Readiness Weight)
- $w_{\text{audit}} = 0.05$ (Lakehouse Data Contract & PII Audit Weight)

---

## 5. SUB-METRIC DEFINITIONS

### 5.1 Requisition Fit ($S_{\text{req}}$)
Calculated from the core capability overlap between candidate $C_i$ and job $J$:
- Same sector and same ANZSCO Unit Group: $S_{\text{req}} = 95.0$
- Same sector with transferable competency overlap: $S_{\text{req}} = 82.0$
- Adjacent transferable sector (e.g. Operations $\leftrightarrow$ Supply Chain): $S_{\text{req}} = 65.0$
- Cross-disciplinary: $S_{\text{req}} = 30.0$

### 5.2 Seniority Parity ($S_{\text{sen}}$)
Let $Y_i$ be verified candidate years of experience.  
Let $Y_{\text{target}}$ be the expected experience for the job:
- Junior role: $Y_{\text{target}} = 2.0\text{ yrs}$
- Mid-level role: $Y_{\text{target}} = 5.0\text{ yrs}$
- Senior / Lead role: $Y_{\text{target}} = 8.0\text{ yrs}$

The algorithm calculates:

$$S_{\text{sen}} = \max\left(25.0, \; 100.0 - \left(12.5 \cdot |Y_i - Y_{\text{target}}|\right)\right)$$

### 5.3 Verifiable Evidence Rigor ($S_{\text{evid}}$)
Measures the depth of quantifiable achievements in the candidate verified records ($0.0 - 100.0$).

### 5.4 Statutory & Licensing Readiness ($S_{\text{reg}}$)
- Full Australian accreditation held or no statutory license required: $S_{\text{reg}} = 100.0$
- Credential bridging assessment required (e.g. AHPRA, CPA, Engineers AU): $S_{\text{reg}} = 60.0$
- Severe unaddressed licensing deficiency: $S_{\text{reg}} = 20.0$

### 5.5 Lakehouse Data Contract Audit ($S_{\text{audit}}$)
Fixed at $100.0$ when the record successfully passes all dbt data contracts and SHA-256 PII scrub verification.

---

## 6. RECRUITER TALENT SHORTLIST RANKING PROCEDURE

1. Recruiter opens a job requisition.
2. The algorithm filters candidates in the lakehouse storage.
3. The algorithm evaluates $TSS(C_i \mid J)$ for all matching candidates.
4. The algorithm sorts candidates in descending order of $TSS$.
5. The dashboard presents the ranked talent queue with transparent match badges and gap highlights.
