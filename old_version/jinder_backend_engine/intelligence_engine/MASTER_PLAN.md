# Skill Bridge Intelligence Engine — Research Architecture & Master Plan
> **Academic Foundations, Industrial Benchmarks, and Mathematical Modeling for Australian Talent & Job Intelligence**

---

## 1. Executive Summary & Literature Review

Modern talent intelligence platforms require mathematically rigorous, explainable, and multi-objective ranking architectures. Unlike basic keyword matching, enterprise systems must account for hierarchical occupational taxonomies (**ABS ANZSCO**), asymmetric skill importance, career adjacency, and two-sided market dynamics.

### 1.1 Reference Literature & Industry Systems
This framework draws direct inspiration from foundational research papers and production-grade architectures:

1. **LinkedIn Skill Genome & Taxonomy Mapping:**
   - *Bastian et al. (KDD 2014)*: "LinkedIn Skills: Large-Scale Topic Modeling and Graph Analysis for Skill Extraction."
   - *Zhang et al. (KDD 2016)*: "Name Entity Recognition and Standardization in Job Search and Recommendations."
   - *Application*: Taxonomy tree projection, weighted Jaccard similarity using Inverse Document Frequency ($\text{IDF}$), and occupational entity normalization.

2. **Occupational Content Models & Labor Economics:**
   - *Peterson et al. (2001) / O\*NET Content Model*: Structure of Knowledge, Skills, Abilities (KSAs), and Generalized Work Activities (GWAs).
   - *Australian Bureau of Statistics (ABS)*: Australian and New Zealand Standard Classification of Occupations (ANZSCO 2022/2026 6-digit classification tree).
   - *Deming & Kahn (QJE 2018)*: "Skill Requirements for Across-Firm Wage Inequality" — quantifying core cognitive vs non-cognitive vs statutory competencies.

3. **Job Representation & Vector Space Modeling:**
   - *Le et al. (WWW 2019)*: "Job2Vec: Learning Representations of Jobs for Career Path Modeling."
   - *Sivani et al. (RecSys 2021)*: Multi-aspect job similarity combining compensation, requirements, and geographic elasticity.

4. **Two-Sided Recommendation & Learning to Rank (LTR):**
   - *Borisyuk et al. (KDD 2016)*: "LiJar: Latent Factor Models for Job Recommendations at LinkedIn."
   - *Ramanath et al. (RecSys 2018)*: "Two-Sided Marketplace Recommendations in Talent Acquisition."
   - *Burges (2010)*: LambdaMART and Gradient Boosted Decision Trees for calibrated candidate relevancy and click-through optimization.

---

## 2. Architecture of the 6 Modular Intelligence Formulas

```
+----------------------------------------------------------------------------------------------------+
|                                  SKILL BRIDGE INTELLIGENCE ENGINE                                  |
+-----------------------------------+--------------------------------+-------------------------------+
|         CAPABILITY CORE           |       COMPARISON MATRICES      |       TWO-SIDED RANKING       |
+-----------------------------------+--------------------------------+-------------------------------+
| 1. Candidate vs ANZSCO Match      | 3. Job vs Job Proximity        | 5. Job Seeker Feed Ranking    |
|    Skill Alignment Score (SMF)    |    Substitutability (JJF)      |    Utility & Mobility (JFR)   |
|                                   |                                |                               |
| 2. CV vs Job Skill Gap            | 4. Candidate vs Candidate      | 6. HR Talent Search Ranking   |
|    Severity & Learnability (SGF)  |    Relative Edge Index (CCF)   |    Readiness & Merit (TSR)    |
+-----------------------------------+--------------------------------+-------------------------------+
```

---

### Formula 1: Candidate vs ANZSCO Taxonomy Skill Match ($SMF$)
- **Objective:** Quantify how strongly an international candidate's raw verified resume matches the official ABS ANZSCO unit group skill definitions.
- **Key Concepts:**
  - ABS ANZSCO 6-digit hierarchical tree distance ($D_{\text{tree}}$).
  - Direct Sector Skills vs Cross-Sector Transferable Skills.
  - TF-IDF Weighted Jaccard & Soft-Cosine with semantic word embeddings.
- **Output:** Normalized alignment score $[0.0, 100.0]$ and tier classification (`Direct Alignment`, `Transferable Adjacent`, `Emerging Bridge`).

---

### Formula 2: Resume vs Job Description Skill Gap ($SGF$)
- **Objective:** Detect missing competencies between a specific job vacancy and a candidate's resume, weighted by regulatory criticality and training velocity.
- **Key Concepts:**
  - Asymmetric penalty model: Missing mandatory statutory certifications (e.g., AHPRA, Engineers Australia, CPA) incurs hard penalties; missing secondary software tools incurs logarithmic penalties.
  - Learnability Distance ($L_d$): Estimated months required to bridge the gap in Australia.
  - Residual Gap Severity Index ($GSI$).
- **Output:** Categorized gap breakdown (`Critical Statutory`, `Domain Core`, `Minor Adaptation`) + Overall Gap Score $[0.0, 100.0]$.

---

### Formula 3: Job-to-Job Proximity & Substitutability ($JJF$)
- **Objective:** Enable job seekers to compare 2 or $N$ jobs side-by-side to understand career mobility, skill overlap, compensation parity, and work-life trade-offs.
- **Key Concepts:**
  - Occupational Jaccard index on requirements.
  - ANZSCO taxonomic graph distance.
  - Normalized wage midpoint parity.
  - Geographic & remote flexibility alignment.
- **Output:** Pairwise similarity matrix $JPI(J_a, J_b) \in [0.0, 100.0]$ + Differential feature vector (delta salary, delta requirements, delta seniority).

---

### Formula 4: Candidate-to-Candidate Benchmarking ($CCF$)
- **Objective:** Enable HR recruiters to compare 2 or more shortlisted candidates head-to-head or against an Australian industry cohort.
- **Key Concepts:**
  - Multi-Attribute Utility Theory (MAUT): Normalized dimensions across Skill Depth, Experience Velocity, Resume Evidence Rigor, and Transferability.
  - Bradley-Terry / Elo differential calculation ($\Delta_{A,B}$).
  - Trade-off matrix: Which candidate has higher ceiling vs lower immediate onboarding friction.
- **Output:** Relative Merit Score ($RMS$), Head-to-Head Delta ($\Delta$), and Strengths/Weaknesses radar chart points.

---

### Formula 5: Internal Feed Ranking Algorithm for Job Seekers ($JFR$)
- **Objective:** Real-time scoring function that ranks 460+ Australian vacancies when displayed on the Job Seeker's portal.
- **Key Concepts:**
  - Candidate Utility Function $U(J \mid C)$:
    $$\text{Score}(J \mid C) = w_1 \cdot \text{CapabilityMatch} + w_2 \cdot \text{WageGrowthPotential} + w_3 \cdot \text{LocationCommuteFit} + w_4 \cdot \text{RecencyFreshness} - w_5 \cdot \text{FatiguePenalty}$$
  - Diversity constraint: Prevent feed saturation by any single employer or location.
- **Output:** Ranked job feed array sorted by personalized relevance score.

---

### Formula 6: Internal Talent Search Ranking Algorithm for HR / Recruiters ($TSR$)
- **Objective:** Scoring function that ranks candidate profiles when a recruiter views an open requisition or filters talent pools.
- **Key Concepts:**
  - Recruiter Objective Function $R(C \mid J)$:
    $$\text{Score}(C \mid J) = \lambda_1 \cdot \text{JobRequirementFit} + \lambda_2 \cdot \text{ExperienceSeniorityFit} + \lambda_3 \cdot \text{VerifiableEvidenceScore} + \lambda_4 \cdot \text{VisaRegulatoryReadiness} - \lambda_5 \cdot \text{GapFriction}$$
  - PII masking compliance assurance and bias attenuation.
- **Output:** Ranked applicant shortlist with explainable justification tags.

---

## 3. Phased Execution Roadmap

As requested, development will proceed **iteratively, formula by formula**, storing all documentation, mathematical proofs, Python/PySpark implementations, and unit test suites in `intelligence_engine/`:

| Phase | Milestone | Deliverable | Status |
| :---: | :--- | :--- | :---: |
| **0** | **Master Architecture & Plan** | `intelligence_engine/MASTER_PLAN.md` | **COMPLETED** |
| **1** | **Formula 1: Candidate vs ANZSCO Skill Match** | `01_skill_matching_model.py` + Specification Doc | **NEXT UP** |
| **2** | **Formula 2: Skill Gap Severity & Learnability** | `02_skill_gap_analysis.py` + Specification Doc | Queued |
| **3** | **Formula 3: Job-to-Job Proximity & Comparison** | `03_job_to_job_comparison.py` + Specification Doc | Queued |
| **4** | **Formula 4: Candidate-to-Candidate Benchmarking** | `04_candidate_benchmarking.py` + Specification Doc | Queued |
| **5** | **Formula 5: Job Seeker Feed Ranking Engine** | `05_job_seeker_ranking_feed.py` + Specification Doc | Queued |
| **6** | **Formula 6: Recruiter Talent Search Ranking Engine** | `06_recruiter_candidate_ranking.py` + Specification Doc | Queued |
| **7** | **System Integration & Pipeline Verification** | Integration into PySpark Lakehouse & Web UI APIs | Queued |

---

## 4. Next Immediate Step
We will build **Phase 1: Formula 1 (Candidate vs ANZSCO Skill Match)** with full mathematical formulation, TF-IDF / taxonomy tree weighting, and executable PySpark/Python code tested against live dataset records.
