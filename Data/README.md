# Data: Benchmark Datasets & Legal Provenance

This directory houses the structured reference ontologies, synthetic benchmark cohorts, and legal compliance documentation powering the **Jinder Platform**.

## Contents & Structure

```
Data/
├── DATA_PROVENANCE_AND_LEGALITY.md   # ⚖️ Official Australian Legal Compliance & Zero-Theft Statement
├── reference/                        # 🏛️ Australian ICT Taxonomy & Role Standards
│   ├── ict_taxonomy.json             # 172 Skills, 53 Roles, 20 Specialisations (CC BY 4.0 ABS)
│   ├── role-mappings.reference.json  # International-to-Australian role crosswalks
│   └── target-roles.json             # Target career roles
├── synthetic/                        # 🧪 100% Computationally Synthesized Evaluation Benchmarks
│   ├── 50_australian_jobs.json       # 50 Synthetic job requisitions across 3 ICT domains
│   ├── 50_talent_profiles.json       # 50 Anonymized talent competency vectors
│   └── demo_employer_jobs.json       # Pre-seeded employer demonstration requisitions
└── sample_csv/                       # 📊 De-identified CSV files for batch reader testing
    ├── australian_jobs_dataset.csv
    ├── international_candidates_dataset.csv
    └── real_resumes_dataset.csv
```

## Legal Assurance Summary
For full statutory references regarding the **Copyright Act 1968 (Cth)**, **Privacy Act 1988 (Cth)**, **OAIC De-identification Guidelines**, and **ABS CC BY 4.0 licensing**, please read [**`DATA_PROVENANCE_AND_LEGALITY.md`**](DATA_PROVENANCE_AND_LEGALITY.md).
