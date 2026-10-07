---
name: capability-gap-analyzer
description: Compare candidate skills against target job requirements, classify skill gaps into statutory blockers vs learnable tools, and estimate remediation time.
---

# Skill: Capability Gap Analyzer

## Overview
This skill computes the exact delta between what a candidate possesses and what an employer requires. Crucially, it categorizes missing competencies into **Statutory Blockers** (non-negotiable mandatory skills/licences) versus **Learnable Tools** (frameworks or tools that can be acquired on the job in 1-3 months).

## Inputs
- `candidate_skills`: Array of `{ name, level }` objects representing candidate competencies.
- `job_requirements`: Array of `{ name, level, must }` objects representing job demands.
- `job_domain`: The technical domain (`Software Engineering`, `AI & Machine Learning`, `Data`).

## Analysis Procedure

### Step 1: Gap Classification
For every requirement $r \in \text{job\_requirements}$:
1. If $\exists c \in \text{candidate\_skills}$ where $c.\text{name} == r.\text{name}$:
   - If $c.\text{level} \ge r.\text{level}$, it is a **Direct Match**.
   - If $c.\text{level} < r.\text{level}$, it is a **Proficiency Gap** ($\Delta = r.\text{level} - c.\text{level}$).
2. If $\nexists c \in \text{candidate\_skills}$ where $c.\text{name} == r.\text{name}$:
   - If $r.\text{must} == \text{true}$: **Mandatory Gap (Statutory Blocker)**.
   - If $r.\text{must} == \text{false}$: **Preferred Gap (Learnable Tool)**.

### Step 2: Time-to-Close Estimation
Calculate estimated study or upskilling time:
- Missing Learnable Tool (e.g., Redis, Tailwind): **1.0 month**.
- Moderate Library/Framework Gap (e.g., GraphQL, PyTorch): **2.0 months**.
- Core Foundational Gap (e.g., Distributed Systems, Machine Learning Foundations): **3.5 - 6.0 months**.
- Cap total estimated time at a realistic ceiling (e.g., 6 months for achievable transitions).

### Step 3: Upgrading Recommendations
Identify verified certification pathways from the Australian ICT reference list:
- e.g., Missing Cloud AWS -> Suggest `AWS Certified Developer - Associate`.
- e.g., Missing Kubernetes -> Suggest `Certified Kubernetes Administrator (CKA)`.

## Output Schema
```json
{
  "coverage_percentage": 75.0,
  "matched_count": 6,
  "total_required": 8,
  "statutory_blockers": [],
  "learnable_tools": [
    { "name": "Terraform", "required_level": 3, "estimated_months": 1.5 }
  ],
  "total_learning_time_months": 1.5,
  "recommended_certifications": ["HashiCorp Certified: Terraform Associate"]
}
```
