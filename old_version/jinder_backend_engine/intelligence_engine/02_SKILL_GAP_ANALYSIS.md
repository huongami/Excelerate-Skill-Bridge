# TECHNICAL SPECIFICATION: SKILL GAP SEVERITY AND LEARNABILITY MODEL (SGF)
**Document Number:** IE-SPEC-002  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Classification:** Core Algorithm Specification  

---

## 1. IDENTIFICATION AND PURPOSE

This document gives the mathematical formula and the calculation steps for the Skill Gap Function (SGF).  
The algorithm identifies missing competencies between a candidate resume and a specific job description.  
The algorithm calculates:
1. The Gap Severity Index ($GSI$).
2. The Estimated Training Duration in months ($T_{\text{total}}$).
3. The Job Readiness Score ($JRS$).

---

## 2. APPLICABLE DOCUMENTS

The algorithm uses principles from these reference papers and standards:

1. **Autor, Levy, & Murnane (QJE 2003):** The Skill Content of Recent Technological Change.
2. **Deming & Kahn (2018):** Skill Requirements for Across-Firm Wage Inequality.
3. **Australian Qualifications Framework (AQF):** Learning Outcomes and Competency Benchmarks.

---

## 3. TECHNICAL TERMS AND DEFINITIONS

| Term | Approved Definition |
| :--- | :--- |
| **Skill Gap ($g_k$)** | A competency required by a job that the candidate resume does not show. |
| **Statutory Gap** | A legal license or government registration necessary to do the work in Australia. |
| **Core Domain Gap** | A primary technical method or engineering principle central to the job. |
| **Tool Gap** | A software package or utility program that a worker can learn quickly. |
| **Learnability Duration ($T_k$)** | The estimated time in calendar months to learn competency $g_k$. |

---

## 4. MATHEMATICAL FORMULATION

### 4.1 Gap Severity Master Equation

Let $G = \{g_1, g_2, \dots, g_m\}$ be the set of identified skill gaps.  
Each gap $g_k$ has an assigned severity category weight $W_{\text{cat}}(g_k)$ and a learnability duration $T_k$.

The algorithm calculates the Gap Severity Index ($GSI$):

$$GSI(C, J) = \min\left(100.0, \; \sum_{k=1}^{m} W_{\text{cat}}(g_k) \times \left(15.0 + 5.0 \cdot \ln(1 + T_k)\right)\right)$$

### 4.2 Job Readiness Score ($JRS$)

The Job Readiness Score shows the candidate readiness level after gap deduction:

$$JRS(C, J) = \max\left(0.0, \; 100.0 - GSI(C, J)\right)$$

### 4.3 Parallel Training Duration ($T_{\text{total}}$)

Candidates can learn some tools during the same calendar period.  
The algorithm calculates total bridge duration with parallel learning discount:

$$T_{\text{total}} = \max_{k=1\dots m}(T_k) + 0.20 \cdot \sum_{k \neq \text{argmax}} T_k$$

---

## 5. SEVERITY CATEGORIES AND WEIGHTS

The algorithm classifies each missing competency into one of four approved categories:

| Category Code | Category Name | Weight ($W_{\text{cat}}$) | Typical Duration ($T_k$) | Example in Australia |
| :---: | :--- | :---: | :---: | :--- |
| **CAT-1** | Statutory License | **1.00** | $6.0 - 18.0\text{ months}$ | AHPRA Registration, CPA AU, Engineers AU Stage 1 |
| **CAT-2** | Core Technical Discipline | **0.60** | $3.0 - 6.0\text{ months}$ | Distributed Systems Design, Clinical Triage Protocols |
| **CAT-3** | Tool or Platform | **0.25** | $0.5 - 2.0\text{ months}$ | Snowflake, dbt, AutoCAD, Salesforce CRM |
| **CAT-4** | Local Standard Orientation | **0.10** | $0.5 - 1.0\text{ month}$ | Australian PBS/Medicare guidelines, Australian WHS laws |

---

## 6. READINESS TIER CLASSIFICATION

The algorithm classifies the readiness score into three operational tiers:

```
[JRS >= 80.0]  --> LOW GAP (IMMEDIATE DEPLOYMENT)
                   Candidate needs only standard workplace onboarding (0 - 1 month).

[55.0 <= JRS < 80.0] --> MODERATE GAP (FAST-TRACK UPSKILLING)
                         Candidate needs short-course or tool certification (1 - 3 months).

[JRS < 55.0]   --> HIGH GAP (STRUCTURAL BRIDGING)
                   Candidate needs formal Australian statutory licensing or diploma (6+ months).
```

---

## 7. VERIFICATION EXAMPLE

### 7.1 Input Data
- **Candidate:** Minh Tuan Nguyen (Origin: Vietnam, 10 years experience)
- **Target Vacancy:** Australian Registered Nurse (Sydney Hospital)
- **Detected Gaps:**
  1. AHPRA Registration (Statutory License, CAT-1): $W_1 = 1.00, T_1 = 8.0\text{ months}$
  2. Australian PBS/Medicare Billing Guidelines (Local Standard, CAT-4): $W_2 = 0.10, T_2 = 1.0\text{ month}$
  3. Electronic Health Records System (e.g., Epic/Cerner, CAT-3): $W_3 = 0.25, T_3 = 1.0\text{ month}$

### 7.2 Step-by-Step Calculation
1. **Calculate Severity for Gap 1 (AHPRA):**
   $$\text{Sev}_1 = 1.00 \times (15.0 + 5.0 \cdot \ln(1 + 8.0)) = 1.00 \times (15.0 + 5.0 \cdot \ln(9.0)) = 1.00 \times (15.0 + 10.99) = 25.99$$

2. **Calculate Severity for Gap 2 (PBS Guidelines):**
   $$\text{Sev}_2 = 0.10 \times (15.0 + 5.0 \cdot \ln(1 + 1.0)) = 0.10 \times (15.0 + 3.47) = 1.85$$

3. **Calculate Severity for Gap 3 (EHR System):**
   $$\text{Sev}_3 = 0.25 \times (15.0 + 5.0 \cdot \ln(1 + 1.0)) = 0.25 \times (18.47) = 4.62$$

4. **Sum Gap Severity Index ($GSI$):**
   $$GSI = 25.99 + 1.85 + 4.62 = \mathbf{32.5}$$

5. **Calculate Job Readiness Score ($JRS$):**
   $$JRS = 100.0 - 32.5 = \mathbf{67.5\%}$$

6. **Calculate Parallel Bridge Duration ($T_{\text{total}}$):**
   $$T_{\text{total}} = 8.0 + 0.20 \times (1.0 + 1.0) = 8.0 + 0.40 = \mathbf{8.4\text{ months}}$$

7. **Determine Operational Tier:**
   $55.0 \le JRS < 80.0 \implies \textbf{MODERATE GAP (FAST-TRACK UPSKILLING)}$.
