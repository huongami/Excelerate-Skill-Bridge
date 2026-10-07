---
name: skill-extraction-and-normalization
description: Extract technical and core competencies from unstructured CVs and job descriptions, normalizing them to the Australian ICT Taxonomy.
---

# Skill: Extraction & Normalization

## Overview
This skill provides automated parsing of resume text, candidate profiles, and job requisitions. It identifies candidate skills and maps non-standard international terminology into canonical Australian ICT skills defined in `ict_taxonomy.json`.

## Inputs
- `raw_text`: String containing unformatted CV content or Job Description.
- `target_domain`: Domain identifier (`Software Engineering`, `AI & Machine Learning`, `Data`).
- `taxonomy_reference`: Loaded reference dictionary from `ict_taxonomy.json`.

## Extraction Pipeline & Rules

### Step 1: Lexical & Synonym Matching
Scan the input text against canonical skill names, abbreviations, and aliases:
- e.g., *"k8s"* -> mapped to *"Kubernetes"*
- e.g., *"postgres"*, *"psql"* -> mapped to *"PostgreSQL"*
- e.g., *"NLP"*, *"BERT"*, *"Transformers"* -> mapped to *"Natural Language Processing (NLP)"*

### Step 2: Proficiency Level Determination
Determine proficiency level (1 to 5) based on contextual evidence:
- **Level 1 (Beginner):** Mentioned in coursework or introductory projects.
- **Level 2 (Junior):** 1-2 years applied experience or junior responsibilities.
- **Level 3 (Mid):** 3-5 years solid production delivery, independent development.
- **Level 4 (Senior):** 5+ years architectural design, code review, mentoring.
- **Level 5 (Lead/Expert):** Principal leadership, core systems ownership.

### Step 3: Evidence Grounding (No Hallucinations)
For each detected skill, record the exact sentence or line of evidence:
```json
{
  "name": "Docker",
  "level": 3,
  "evidence": "Containerized microservices using Docker and orchestrated multi-container setups."
}
```
If no textual evidence exists, the skill must not be injected.

## Output Schema
```json
{
  "skills": [
    { "name": "Python", "level": 4, "kind": "hard", "evidence": "Built high-throughput backend APIs in Python for 5 years." },
    { "name": "Docker", "level": 3, "kind": "hard", "evidence": "Containerized microservices using Docker." }
  ],
  "certifications": ["AWS Certified Solutions Architect - Associate"],
  "domain": "Software Engineering",
  "specialisation": "Backend Engineering"
}
```
