---
name: formula-engine-calculator
description: Execute the 6 deterministic mathematical alignment models (F-01 to F-06) for candidate matching, relative merit scoring, and ranking.
---

# Skill: Formula Engine Calculator

## Overview
This skill executes the core mathematical intelligence engine of Jinder without black-box neural networks or subjective bias. Every score is mathematically bounded between $[0, 100]$.

## Core Mathematical Models Executed

### F-01: Skill Match Frequency & Coverage (SMF)
Computes weighted coverage between candidate skills and job requirements:
$$SMF = \frac{\sum_{i \in \text{matched}} w_i \cdot \min(1.0, \frac{L_{c,i}}{L_{j,i}})}{\sum_{k \in \text{all}} w_k} \times 100$$
- Mandatory skills receive weight $w = 2.0$.
- Preferred skills receive weight $w = 1.0$.

### F-02: Gap Severity Index & Job Readiness Score (GSI & JRS)
Measures the penalty of missing capabilities, heavily penalizing statutory blockers:
$$GSI = \sum_{g \in \text{gaps}} \beta_g \cdot \text{Severity}(g)$$
$$JRS = \max(0, SMF - GSI)$$
- $\beta = 15.0$ for mandatory skills.
- $\beta = 5.0$ for optional tools.

### F-03: Job Proximity Index (JPI)
Computes vector distance across multiple job roles to identify career transition feasibility:
$$JPI(J_A, J_B) = 100 \times \left(1 - \frac{|S_A \Delta S_B|}{|S_A \cup S_B|}\right)$$

### F-04: Relative Merit Score (RMS - Zero-PII)
Normalizes candidate score against the applicant pool for a specific requisition:
$$RMS = \mu_{\text{pool}} + z \cdot \sigma_{\text{pool}} \quad \text{scaled to } [0, 100]$$
Guarantees fair distribution without revealing competitor identities.

### F-05: Feed Ranking Score (FRS)
Powers the candidate's personalized job discovery feed with behavioral affinity decay:
$$FRS = 0.50 \cdot SMF + 0.25 \cdot JRS + 0.15 \cdot \text{ExperienceMatch} + 0.10 \cdot \text{Affinity}$$

### F-06: Recruiter Talent Search Score (TSS)
Ranks candidate talent cards for employers based on verified competencies:
$$TSS = 0.45 \cdot SMF + 0.25 \cdot \text{LevelFit} + 0.15 \cdot \text{CertsAwards} + 0.15 \cdot \text{RecentActivity}$$

## Execution Guarantee
- **Deterministic:** Given identical inputs, formulas output identical scores.
- **Zero Rounding Flaws:** Precision maintained at floating point float64, rounded to 1 decimal place only for UI presentation.
