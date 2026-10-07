# TECHNICAL SPECIFICATION: CANDIDATE TO ANZSCO SKILL MATCH MODEL (SMF)
**Document Number:** IE-SPEC-001  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Classification:** Core Algorithm Specification  

---

## 1. IDENTIFICATION AND PURPOSE

This document gives the mathematical formula and the calculation steps for the Skill Match Function (SMF).  
The algorithm calculates the match score between an international candidate profile and an Australian standard occupation.  
The algorithm uses the official Australian and New Zealand Standard Classification of Occupations (ANZSCO).

---

## 2. APPLICABLE DOCUMENTS

The algorithm uses principles from these reference papers and standards:

1. **Bastian et al. (ACM KDD 2014):** LinkedIn Skills: Large-Scale Topic Modeling and Graph Analysis.
2. **Peterson et al. (2001):** Understanding Work Using the O*NET Content Model.
3. **Australian Bureau of Statistics (ABS):** ANZSCO Structure and Occupational Definitions (Cat. 1220.0).

---

## 3. TECHNICAL TERMS AND DEFINITIONS

| Term | Approved Definition |
| :--- | :--- |
| **Candidate ($C$)** | A person who looks for work with recorded qualifications and experience. |
| **Occupation ($O$)** | A standard Australian job title with a 6-digit ANZSCO identification code. |
| **Taxonomy Tree** | The 5-level hierarchical classification tree defined by the ABS. |
| **Direct Skill** | A technical skill that belongs specifically to one occupational domain. |
| **Transferable Skill** | A methodology or practice that a worker can use across different industries. |
| **Skill Level ($L_O$)** | The formal education level defined by ANZSCO (Level 1 to Level 5). |

---

## 4. MATHEMATICAL FORMULATION

### 4.1 Master Equation

The algorithm calculates the final Skill Match Score ($SMF$) as follows:

$$SMF(C, O) = \min\left(100.0, \; \Big( w_1 \cdot S_{\text{tree}} + w_2 \cdot S_{\text{direct}} + w_3 \cdot S_{\text{trans}} \Big) \times \Phi(Y_C, L_O)\right)$$

### 4.2 Parameter Weights

The weights must obey this condition:

$$\sum_{i=1}^{3} w_i = w_1 + w_2 + w_3 = 1.00$$

Approved baseline values:
- $w_1 = 0.25$ (Taxonomy Tree Proximity Weight)
- $w_2 = 0.50$ (Direct Competency Overlap Weight)
- $w_3 = 0.25$ (Transferable Methodology Weight)

---

## 5. SUB-METRIC DEFINITIONS

### 5.1 Taxonomy Tree Score ($S_{\text{tree}}$)

Let $\text{Code}_C$ be the candidate primary ANZSCO code.  
Let $\text{Code}_O$ be the target ANZSCO code.  

The algorithm sets $S_{\text{tree}}$ with these conditions:

| Matching Condition | Prefix Overlap | Score ($S_{\text{tree}}$) |
| :--- | :---: | :---: |
| Exact Occupation Match | 6 digits | 100.0 |
| Same Unit Group | 4 digits | 85.0 |
| Same Minor Group | 3 digits | 65.0 |
| Same Sub-Major Group | 2 digits | 40.0 |
| Same Major Group | 1 digit | 20.0 |
| Different Major Groups | 0 digits | 0.0 |

---

### 5.2 Direct Competency Overlap Score ($S_{\text{direct}}$)

Let $K_C$ be the set of verified candidate skills.  
Let $K_O$ be the set of standard skills for occupation $O$.  
Let $\text{IDF}(t)$ be the Inverse Document Frequency weight for skill term $t$.

The algorithm calculates:

$$S_{\text{direct}} = \frac{\sum_{t \in K_C \cap K_O} \text{IDF}(t)}{\sum_{t \in K_O} \text{IDF}(t)} \times 100.0$$

When $K_O$ is empty, the algorithm sets $S_{\text{direct}} = 50.0$.

---

### 5.3 Transferable Methodology Score ($S_{\text{trans}}$)

Transferable methodologies include:
- Standard Operating Procedures (SOP)
- Quality Assurance (QA) and regulatory compliance
- Agile and project delivery frameworks
- Stakeholder communication and team leadership

The algorithm computes the cosine similarity between the candidate transferable vector $\vec{V}_C$ and the occupational task vector $\vec{V}_O$:

$$S_{\text{trans}} = \frac{\vec{V}_C \cdot \vec{V}_O}{\|\vec{V}_C\| \|\vec{V}_O\|} \times 100.0$$

---

### 5.4 Experience Calibration Multiplier ($\Phi$)

Let $Y_C$ be the verified years of experience of the candidate.  
Let $L_O$ be the ANZSCO Skill Level of the occupation ($1 \le L_O \le 5$).

The benchmark experience years $Y_{\text{req}}$ are:
- Level 1 (Bachelor degree or higher): $Y_{\text{req}} = 5.0\text{ years}$
- Level 2 (Associate degree or diploma): $Y_{\text{req}} = 3.0\text{ years}$
- Level 3 (Certificate IV or III): $Y_{\text{req}} = 2.0\text{ years}$
- Level 4 (Certificate II or III): $Y_{\text{req}} = 1.0\text{ year}$
- Level 5 (Certificate I or secondary education): $Y_{\text{req}} = 0.5\text{ years}$

The algorithm calculates the multiplier $\Phi$:

$$\Phi(Y_C, L_O) = \min\left(1.05, \; 0.85 + 0.15 \cdot \frac{Y_C}{Y_{\text{req}}(L_O)}\right)$$

---

## 6. OUTPUT TIER CLASSIFICATION

The algorithm classifies the match score into three operational tiers:

```
[Score >= 85.0]  --> DIRECT INDUSTRY ALIGNMENT
                     The candidate has immediate capability to do the job.

[70.0 <= Score < 85.0] --> TRANSFERABLE CROSS-SECTOR CAPABILITY
                           The candidate has core skills but needs brief orientation.

[Score < 70.0]   --> EMERGING CAREER BRIDGE
                     The candidate needs training before job placement.
```

---

## 7. VERIFICATION EXAMPLE

### 7.1 Input Data
- **Candidate:** Minh Tuan Nguyen (Origin: Vietnam)
- **Candidate ANZSCO:** `254411` (Registered Nurse)
- **Target ANZSCO:** `254411` (Registered Nurse)
- **Years of Experience ($Y_C$):** 10.0 years
- **ANZSCO Skill Level ($L_O$):** 1 ($Y_{\text{req}} = 5.0\text{ years}$)
- **Direct Skill Overlap:** $92.0\%$
- **Transferable Skill Overlap:** $88.0\%$

### 7.2 Step-by-Step Calculation
1. **Calculate Taxonomy Score ($S_{\text{tree}}$):**
   Exact 6-digit match $\implies S_{\text{tree}} = 100.0$.

2. **Calculate Direct Score ($S_{\text{direct}}$):**
   $S_{\text{direct}} = 92.0$.

3. **Calculate Transferable Score ($S_{\text{trans}}$):**
   $S_{\text{trans}} = 88.0$.

4. **Calculate Base Composite Score:**
   $$\text{Base} = (0.25 \times 100.0) + (0.50 \times 92.0) + (0.25 \times 88.0) = 25.0 + 46.0 + 22.0 = 93.0$$

5. **Calculate Experience Multiplier ($\Phi$):**
   $$\Phi = \min\left(1.05, \; 0.85 + 0.15 \cdot \frac{10.0}{5.0}\right) = \min(1.05, \; 0.85 + 0.30) = \min(1.05, 1.15) = 1.05$$

6. **Calculate Final Match Score ($SMF$):**
   $$SMF = \min(100.0, \; 93.0 \times 1.05) = \min(100.0, 97.65) = \mathbf{97.7\%}$$

7. **Determine Tier:**
   Score $97.7 \ge 85.0 \implies \textbf{Direct Industry Alignment}$.
