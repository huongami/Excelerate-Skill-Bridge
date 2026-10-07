# TECHNICAL SPECIFICATION: JOB SEEKER FEED RANKING ENGINE (JFR)
**Document Number:** IE-SPEC-005  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Classification:** Core System Algorithm Specification  

---

## 1. IDENTIFICATION AND PURPOSE

This document gives the mathematical formula and the calculation steps for the Job Seeker Feed Ranking Function (JFR).  
The algorithm ranks and sorts all Australian vacancies displayed on a job seeker portal.  
The algorithm optimizes:
1. Candidate capability match.
2. Salary attractiveness and compensation growth.
3. Geographic and work-mode alignment.
4. Posting freshness and employer diversity.

---

## 2. APPLICABLE DOCUMENTS

The algorithm uses principles from these reference papers and standards:

1. **Borisyuk et al. (ACM KDD 2016):** LiJar: Latent Factor Models for Job Recommendations at LinkedIn.
2. **Ramanath et al. (ACM RecSys 2018):** Two-Sided Marketplace Recommendations in Talent Acquisition.
3. **Burges (2010):** From RankNet to LambdaRank to LambdaMART: An Overview.

---

## 3. TECHNICAL TERMS AND DEFINITIONS

| Term | Approved Definition |
| :--- | :--- |
| **Feed Ranking Score ($FRS$)** | The final sorting score that sets the display position of a job in the user feed. |
| **Capability Match ($S_{\text{cap}}$)** | The verified skill alignment score between candidate $C$ and job $J$. |
| **Wage Upside ($S_{\text{wage}}$)** | The attractiveness of the job salary relative to the national sector baseline. |
| **Recency Decay ($\tau$)** | The reduction in job rank over time measured in calendar days. |
| **Diversity Penalty ($\delta_{\text{div}}$)** | A deduction to prevent one employer from filling the entire feed. |

---

## 4. MATHEMATICAL FORMULATION

### 4.1 Feed Ranking Master Equation

For candidate $C$ and vacancy $J_i$, the algorithm calculates the Feed Ranking Score ($FRS$):

$$FRS(J_i \mid C) = \Big( w_{\text{cap}} \cdot S_{\text{cap}} + w_{\text{wage}} \cdot S_{\text{wage}} + w_{\text{loc}} \cdot S_{\text{loc}} + w_{\text{rec}} \cdot S_{\text{rec}} \Big) \times \left(1.0 - \delta_{\text{div}}(J_i)\right)$$

### 4.2 Approved Parameter Weights

The weights must obey this condition:

$$w_{\text{cap}} + w_{\text{wage}} + w_{\text{loc}} + w_{\text{rec}} = 0.45 + 0.20 + 0.20 + 0.15 = 1.00$$

- $w_{\text{cap}} = 0.45$ (Capability & Skill Match Weight)
- $w_{\text{wage}} = 0.20$ (Salary Upside Weight)
- $w_{\text{loc}} = 0.20$ (Geographic Location Alignment Weight)
- $w_{\text{rec}} = 0.15$ (Posting Recency Weight)

---

## 5. SUB-METRIC DEFINITIONS

### 5.1 Capability Match Score ($S_{\text{cap}}$)
Derived directly from Formula 1 ($SMF$) and Formula 2 ($JRS$):

$$S_{\text{cap}} = 0.70 \cdot SMF(C, J_i) + 0.30 \cdot JRS(C, J_i)$$

### 5.2 Wage Upside Score ($S_{\text{wage}}$)
Let $M_i$ be the midpoint salary of job $J_i$ in AUD.  
Let $B_{\text{sector}}$ be the benchmark median salary for that Australian sector:

$$S_{\text{wage}} = \min\left(100.0, \; \max\left(20.0, \; 50.0 + \left(\frac{M_i - B_{\text{sector}}}{B_{\text{sector}}} \times 100.0\right)\right)\right)$$

### 5.3 Location Alignment Score ($S_{\text{loc}}$)
- Job is in candidate preferred city or is fully Remote: $S_{\text{loc}} = 100.0$
- Job is in the same Australian state (e.g., Regional NSW for Sydney seeker): $S_{\text{loc}} = 75.0$
- Job is in an interstate capital (e.g., Melbourne for Sydney seeker): $S_{\text{loc}} = 50.0$
- Job is in an interstate regional location: $S_{\text{loc}} = 25.0$

### 5.4 Posting Recency Score ($S_{\text{rec}}$)
Let $D$ be the age of the job posting in calendar days ($D \ge 0$).  
The algorithm applies exponential recency decay with half-life $\lambda = 0.05$ (approximately 14 days):

$$S_{\text{rec}} = 100.0 \cdot \exp(-0.05 \cdot D)$$

### 5.5 Employer Diversity Penalty ($\delta_{\text{div}}$)
Let $k$ be the count of higher-ranked vacancies from the same employer already in the top feed:

$$\delta_{\text{div}} = \min\left(0.40, \; k \times 0.15\right)$$

---

## 6. FEED SORTING PROCEDURE

1. Retrieve all active vacancies matching the candidate search filters.
2. For each vacancy, calculate $S_{\text{cap}}$, $S_{\text{wage}}$, $S_{\text{loc}}$, and $S_{\text{rec}}$.
3. Calculate initial composite score.
4. Iterate through candidate list and apply the employer diversity discount $\delta_{\text{div}}$.
5. Sort vacancies in descending order of $FRS$.
6. Render the personalized job cards with score badges.
