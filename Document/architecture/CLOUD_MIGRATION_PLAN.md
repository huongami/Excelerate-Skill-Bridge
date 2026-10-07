# Cloud Migration Plan — Jinder Platform on AWS

> **Status:** proposal for review (8 October 2026). Nothing in this file is built yet.
> **Scope:** move the platform from one laptop (SQLite file, local folder, plain HTTP) to AWS, and add a data platform with three layers (Bronze, Silver, Gold).
> **Related:** [Data flow](DATA_FLOW_ARCHITECTURE.md), [Data modeling](DATA_MODELING_ARCHITECTURE_DETAIL.md), [Gap analysis](../GAP_ANALYSIS.md).

**Cost note.** All prices are **estimates in USD per month**, on-demand, for the region **ap-southeast-2 (Sydney)**, before tax, credits and discounts. AWS prices change. Check every line in the [AWS Pricing Calculator](https://calculator.aws/) before a budget decision.

---

## 1. Why move, and the target in one sentence

**Today:** one Python process, one SQLite file (`var/jinder.db`), CV files in a local folder, plain HTTP, scores computed on every request, events written inside the request.

**Target:** a managed web stack in Sydney (CloudFront → containers → PostgreSQL + S3), with an event stream into an **S3 data lake** in three layers. The Gold layer feeds the charts in the app and the internal analytics.

Main reasons:
1. **Privacy and law** — the users are in Australia, and the data includes CVs. Keep all data in an Australian region (Privacy Act 1988, APP 8 on cross-border disclosure). Encrypt in transit and at rest.
2. **Close the gaps** in the gap analysis: encryption, HTTPS, async events, caching, virus scanning, versioned profiles, an LLM service.
3. **Scale** — more than one server process, and analytics that do not slow down the app.

---

## 2. Target architecture

![Jinder target cloud architecture on AWS](diagrams/07_cloud_architecture.png)

Source: [`diagrams/07_cloud_architecture.html`](diagrams/07_cloud_architecture.html). Icons: [`diagrams/icons/README.md`](diagrams/icons/README.md).

Text version:

```
                         ┌──────────────── AWS ap-southeast-2 (Sydney) ─────────────────┐
 Talent / Employer       │                                                               │
   browser ──HTTPS──► Route 53 ─► CloudFront + AWS WAF                                   │
                         │          ├── /*      ─► S3 (web client, static files)         │
                         │          └── /api/*  ─► ALB ─► ECS Fargate: API service       │
                         │                                   │   │   │                   │
                         │        ┌──────────────────────────┘   │   └──► SQS ─► Fargate │
                         │        ▼                              ▼          worker       │
                         │  RDS PostgreSQL (OLTP)        S3 uploads bucket   (CV/JD      │
                         │  Multi-AZ, KMS               (private, KMS,       parse, AI,  │
                         │        │                      malware scan)       email)      │
                         │        │                              │              │        │
                         │        │ CDC / export                 │        Amazon Bedrock │
                         │        ▼                              │        Amazon SES     │
                         │  ┌───────────── S3 DATA LAKE (Iceberg tables) ──────────────┐ │
                         │  │ BRONZE raw ─► Glue jobs ─► SILVER clean ─► dbt ─► GOLD   │ │
                         │  │   ▲ Kinesis Data Firehose (app events)                   │ │
                         │  └──────────────────────────────────────────────────────────┘ │
                         │        │ Gold → reverse ETL                  │ Athena         │
                         │        ▼                                     ▼                │
                         │  RDS "analytics" schema (app charts)   QuickSight (team)      │
                         │                                                               │
                         │  Shared: KMS · Secrets Manager · CloudWatch · CloudTrail ·    │
                         │          IAM · Lake Formation · Glue Data Catalog · ECR       │
                         └───────────────────────────────────────────────────────────────┘
```

### 2.1 Service choices (recommendation)

| Need | Today | Recommended AWS service | Why this choice | Alternative |
|---|---|---|---|---|
| Web client | `jinder_frontend/app` served by Python | **S3 + CloudFront** | Static files, cheap, global cache, HTTPS with ACM | Amplify Hosting |
| API | `start.py` (one process) | **ECS on Fargate** behind an **ALB** | Runs the current Python code in a container. No servers to manage. Scales by task count | EKS (more work), Lambda (needs a rewrite) |
| OLTP database | SQLite | **RDS for PostgreSQL** (Graviton, gp3) | Same relational model, managed backups, Multi-AZ | Aurora PostgreSQL Serverless v2 (better for spiky load, costs more at steady load) |
| CV and job description files | `var/uploads/` | **S3 private bucket**, SSE-KMS, pre-signed URLs | Private, durable, encrypted, lifecycle rules | — |
| Virus scanning | none | **GuardDuty Malware Protection for S3** | Scans each new upload | ClamAV in the worker |
| Background work | 2 threads in the API process | **SQS** + a **Fargate worker** service | The API stays fast; retries and a dead-letter queue | Lambda for small jobs |
| Email | SMTP outbox thread | **Amazon SES** (from the worker, outbox stays) | Cheap, bounce and complaint events | — |
| AI (CV parsing, translation, JD skills) | rule-based code | **Amazon Bedrock** (Claude, in Sydney), rule-based code as the fallback | Gap analysis Phase 6; data stays in the region; guardrails | Self-hosted model (much more work) |
| Cache | none | Start with PostgreSQL (precomputed tables); add **ElastiCache (Valkey)** in Growth | Closes the caching gap (D-3) | — |
| Secrets | `.env` file | **Secrets Manager** | Rotation, no secrets in code | SSM Parameter Store |
| Edge security | none | **AWS WAF** on CloudFront | Rate limits, common attack rules | — |
| Logs and metrics | console | **CloudWatch** (logs, metrics, alarms) + **CloudTrail** | Central logs, audit trail | — |
| Infrastructure as code | — | **Terraform** (or AWS CDK) | Repeatable staging and production | — |
| CI/CD | — | **GitHub Actions** → **ECR** → ECS deploy | The repo is already on GitHub | CodePipeline |

### 2.2 Environments

| Environment | Where | Notes |
|---|---|---|
| Local | Laptop, SQLite (as today) | Keep it for fast development and the tests |
| Staging | AWS, small sizes, Single-AZ | Turn off at night and at weekends to save cost |
| Production | AWS, Multi-AZ | Backups, alarms, WAF |

Use separate AWS accounts for staging and production (AWS Organizations), so that a mistake in staging cannot touch production data.

---

## 3. Data platform: three layers (medallion architecture)

![Bronze, Silver and Gold data layers](diagrams/08_medallion_data_layers.png)

Source: [`diagrams/08_medallion_data_layers.html`](diagrams/08_medallion_data_layers.html).

### 3.1 Principles
1. **The OLTP database stays the source of truth** for the app. The lake is for history, analytics and charts.
2. **Bronze is raw and immutable**, Silver is clean and conformed, Gold is ready to use.
3. **Privacy by layer:** personal data is separated in Silver. Gold has **no personal data** and only aggregates.
4. **Original CV files never go into the lake.** They stay in the uploads bucket.
5. Tables use **Apache Iceberg** on S3 (ACID, time travel, schema change, `MERGE` for CDC), registered in the **Glue Data Catalog**, with access through **Lake Formation**.

### 3.2 Bronze — raw data

| Source | How it arrives | Format and partition | Retention |
|---|---|---|---|
| All OLTP tables (`users`, `profiles`, `translated_skills`, `jobs`, `applications`, `application_history`, …) | Pilot: a nightly export job (Lambda / Fargate task). Growth: **AWS DMS** change data capture (CDC) | Parquet, `ingest_date=YYYY-MM-DD` | 13 months |
| App events (`job_appear`, `job_watch`, `profile_saved`, …) | The API sends events to **Kinesis Data Firehose** (no more synchronous insert in the request) | JSON → Parquet by Firehose, `event_date`, `event_type` | 13 months |
| Parse results (CV and JD) | Worker writes the result JSON | JSON in a **restricted** prefix (`bronze/restricted/`) | **30 days**, then delete |
| Email delivery events | SES → SNS → Firehose | JSON | 6 months |
| Reference data | Each new version of `ict_taxonomy.json` and the job catalogue | JSON, `version=` | Keep all versions |

Rules: write once, never update. Only the data platform role can read Bronze. The restricted prefix (personal data) has a separate KMS key and its own access list.

### 3.3 Silver — clean and conformed (ETL / ELT)

Jobs: **AWS Glue (PySpark)** reads Bronze, cleans, deduplicates and `MERGE`s into Iceberg tables.

| Silver table | Content | Notes |
|---|---|---|
| `dim_talent` (SCD type 2) | `talent_key`, level, years band, domain, specialisation, work modes, visibility, valid_from / valid_to | `talent_key` = HMAC of the user id. **No name, email or country.** The SCD2 history **is the versioned profile** (gap TR-JS-05) |
| `dim_employer` | `employer_key`, company, plan | |
| `dim_job` (SCD type 2) | job attributes, level, years, work mode, open / close dates | Keeps every edit (gap TR-R-07: change history) |
| `dim_skill` | skill name, group, from the taxonomy version | One list of names |
| `bridge_talent_skill` | accepted or edited skills only, level, years | Same rule as the shared profile |
| `bridge_job_skill` | required or preferred, level | |
| `fct_application` | one row per application, current status, origin, dates | |
| `fct_status_change` | from `application_history`: status, time, actor role | Add `from_status` here if the app does not have it yet |
| `fct_event` | typed and deduplicated events | Skips stay internal |
| `fct_notification` | sent, read, email status | |
| `pii_vault` | user id ↔ name, email | **Separate table, Lake Formation column rules, only for erasure and support.** A "delete my data" request removes the row and writes a tombstone; jobs drop the person from all layers |

Data quality checks (Glue Data Quality or dbt tests): unique keys, not null, values in the taxonomy, valid status values, referential checks. A failed check stops the publish to Gold.

### 3.4 Gold — ready for charts, reports and analytics

Jobs: **dbt Core** with the Athena adapter (SQL models with tests), run by **Step Functions** on an **EventBridge Scheduler** timetable (hourly or daily).

| Gold table | Used by | Grain |
|---|---|---|
| `gold_employer_pipeline_daily` | Employer charts: pipeline by stage | job × stage × day |
| `gold_job_interest_daily` | Employer charts: shown, opened, saved, applied | job × day |
| `gold_employer_kpis` | Employer Home: open jobs, jobs at target, waiting for response | employer × day |
| `gold_talent_profile_counts` | Talent: profile shown, opened, saved (owner only) | talent × week |
| `gold_skill_demand_weekly` | Talent insights: "skills to learn next", demand for a skill | skill × week |
| `gold_product_funnel` | Team analytics: sign-up → onboarding → apply → hire | day |
| `gold_match_quality` | Team: reports and skip rates per job, to improve ranking | job × week |

**Serving:**
- **App charts:** a reverse-ETL step copies the Gold tables into a read-only `analytics` schema in RDS after each run. `GET /api/stats` reads these tables instead of counting raw events in the request. This is faster and closes the caching gap for charts.
- **Team analytics:** Athena + QuickSight dashboards on Gold.
- **Privacy rule for Gold:** no personal data. A count that the other side can see is shown only when it is **5 or more** (k-anonymity threshold); a smaller count shows as "fewer than 5". No chart by nationality, gender or ethnicity.

### 3.5 Data flow through the layers

```
RDS (OLTP) ──CDC/export──►  BRONZE  ──Glue──►  SILVER  ──dbt──►  GOLD ──reverse ETL──► RDS analytics ──► app charts
API events ──Firehose────►    (raw,      (clean, PII        (aggregates,             └──► Athena ──► QuickSight
SES events ──Firehose────►   immutable)   separated)        no PII)
```

---

## 4. Migration plan

Total: about **12 weeks** with **2 engineers** (1 backend / data, 1 full-stack / DevOps). The phases match the [gap analysis plan](../GAP_ANALYSIS.md#9-enhancement-plan-future-versions).

| Phase | Weeks | Work | Done when |
|---|---|---|---|
| **0. Prepare the code** | 1–2 | Fix the `/admin` access control. Put the database behind one module: today there are **211 SQL calls in 13 files** and **17 SQLite-only statements** (`INSERT OR …`, `COLLATE NOCASE`, `AUTOINCREMENT`, JSON functions). Put file storage behind one interface (`parsing.py`, `db.py`). Read all settings from environment variables. | The tests pass on SQLite **and** on a local PostgreSQL (Docker) |
| **1. Foundation** | 2–3 | AWS accounts, Terraform, VPC (2 AZs), KMS keys, IAM roles, Secrets Manager, ECR, GitHub Actions pipeline, CloudWatch, CloudTrail, budgets and cost alarms | `terraform apply` builds staging from nothing |
| **2. App on AWS** | 3–6 | Container image; ECS Fargate API + worker; RDS PostgreSQL; S3 uploads with pre-signed URLs and malware scan; SQS for parsing; SES for email; S3 + CloudFront for the web client; WAF; HTTPS (ACM). Data migration script SQLite → PostgreSQL | Staging runs the full test suite and the browser journeys |
| **3. Cut-over** | 7 | Freeze writes, migrate data, check row counts, switch DNS, keep the laptop version read-only for 2 weeks | Production is live; rollback plan tested |
| **4. Bronze** | 7–8 | Firehose for events (remove the synchronous insert); nightly OLTP export to Bronze; SES events | Bronze has one full day of data |
| **5. Silver** | 8–10 | Glue jobs, Iceberg tables, `pii_vault`, data quality rules, erasure flow | Quality checks pass; a test "delete my data" removes the person from every layer |
| **6. Gold + serving** | 10–11 | dbt models, Step Functions schedule, reverse ETL into RDS `analytics`, `/api/stats` reads Gold, QuickSight dashboards | The app charts read Gold; dashboards are live |
| **7. AI and hardening** | 11–12 | Bedrock behind the parsing module (rule-based fallback), guardrails, AI input/output log without raw CV text; backup restore test, load test, privacy review | Restore test and load test pass; privacy review signed |

### Risks and controls

| Risk | Control |
|---|---|
| SQL dialect differences break features | Phase 0 runs the full test suite on PostgreSQL before any cloud work |
| Personal data copied into analytics | Separate `pii_vault`, Lake Formation rules, no PII in Gold, automated test on Gold columns |
| Cost grows quietly | AWS Budgets alerts at 50 / 80 / 100 %, staging scheduled off, tags per component |
| AI output is wrong or unsafe | Schema validation, rule-based fallback, the talent confirms every skill, CV text is data and never instructions |
| Data outside Australia | Only `ap-southeast-2`; Bedrock in-region; check CloudFront and SES settings |

---

## 5. Cost estimate

Three sizes. The numbers are rounded estimates (see the cost note at the top).

| Size | Talent | Employers | CVs read / month | API traffic |
|---|---|---|---|---|
| **Pilot** | about 1,000 | about 50 | about 500 | low |
| **Growth** | about 20,000 | about 1,000 | about 5,000 | medium |
| **Scale** | about 100,000 | about 5,000 | about 25,000 | high |

### 5.1 Production, per month (USD)

| Component | Pilot | Growth | Scale | Sizing assumption |
|---|---:|---:|---:|---|
| CloudFront + S3 (web client) | 3 | 20 | 80 | Data out grows with users |
| Route 53, ACM | 1 | 2 | 3 | ACM certificates are free |
| AWS WAF | 10 | 30 | 70 | Web ACL + rules + requests |
| ALB | 25 | 40 | 90 | Hours + capacity units |
| ECS Fargate — API | 45 | 135 | 450 | Pilot 2 × (0.5 vCPU, 1 GB); Growth 3 × (1 vCPU, 2 GB); Scale 6–10 tasks, autoscaling |
| ECS Fargate — worker | 22 | 90 | 270 | Parsing, AI calls, email |
| NAT gateway | 45 | 100 | 150 | 1 in Pilot, 2 (one per AZ) after; VPC endpoints for S3, ECR, Secrets lower data cost |
| RDS PostgreSQL | 35 | 165 | 650 | Pilot db.t4g.small Single-AZ + 20 GB; Growth db.t4g.medium Multi-AZ + 100 GB; Scale db.m7g.large Multi-AZ + read replica |
| ElastiCache (Valkey) | — | 25 | 120 | Added in Growth |
| S3 — uploads + lake | 5 | 25 | 120 | With lifecycle rules and Intelligent-Tiering |
| GuardDuty Malware Protection (S3) | 3 | 20 | 80 | Per GB scanned |
| SQS, SES, SNS | 2 | 15 | 60 | |
| Kinesis Data Firehose | 1 | 10 | 40 | Events to Bronze |
| AWS DMS (CDC) | — | 75 | 150 | Pilot uses a nightly export instead |
| AWS Glue (Bronze → Silver) | 10 | 120 | 400 | DPU-hours of scheduled jobs |
| Athena (dbt + queries) | 2 | 20 | 80 | Per TB scanned; Parquet and partitions keep it low |
| Step Functions, EventBridge, Lambda | 1 | 5 | 15 | |
| QuickSight | 24 | 130 | 300 | Pilot 1 author; Growth 3 authors + 20 readers |
| Amazon Bedrock (AI) | 25 | 300 | 1,500 | About 0.015–0.05 USD per CV read (depends on the model); plus JD reading and translation |
| CloudWatch, CloudTrail | 15 | 60 | 200 | Logs, metrics, alarms |
| Secrets Manager, KMS, ECR | 6 | 12 | 25 | |
| Backups (RDS snapshots, S3 versions) | 2 | 15 | 60 | |
| **Total production** | **≈ 280** | **≈ 1,410** | **≈ 4,910** | |

### 5.2 Other costs

| Item | Pilot | Growth | Scale | Note |
|---|---:|---:|---:|---|
| Staging environment | ≈ 110 | ≈ 250 | ≈ 450 | Smaller sizes, turned off outside working hours |
| AWS Support plan | 29 | 100 | 500 | Developer → Business (Business is a % of the bill, minimum 100) |
| **Total per month** | **≈ 420** | **≈ 1,760** | **≈ 5,860** | |
| **Total per year** | **≈ 5,000** | **≈ 21,000** | **≈ 70,000** | |

### 5.3 How to pay less

| Action | Typical saving | When |
|---|---|---|
| Compute Savings Plan (Fargate) — 1 year | about 20–50 % on Fargate | After 2–3 months of stable use |
| RDS Reserved Instances — 1 year | about 30–40 % on RDS | Growth and Scale |
| Graviton (ARM) for Fargate, RDS, ElastiCache | about 20 % | From the start |
| VPC endpoints instead of NAT traffic | most of the NAT data cost | From the start |
| Staging off at night and weekends | about 60 % of staging | From the start |
| Smaller AI model for simple steps, cache results by file hash | 50 % or more of Bedrock | From the start |
| Nightly export instead of DMS until CDC is needed | 75–150 per month | Pilot |
| AWS Activate credits for start-ups | credits instead of cash | Apply before the build |

With Savings Plans and Reserved Instances, Growth is about **1,200–1,400 per month** in total.

### 5.4 Not included

- People: about 12 weeks × 2 engineers for the migration, then part-time operation.
- Domain name, tax (GST), a penetration test, a privacy impact assessment, legal review.
- Data transfer above the assumptions, and Bedrock use above the CV volumes in the table.

---

## 6. Decisions needed

1. **Region:** Sydney only (recommended), or also Melbourne (`ap-southeast-4`) for disaster recovery.
2. **API compute:** ECS Fargate (recommended) or a rewrite for Lambda.
3. **Database:** RDS PostgreSQL (recommended) or Aurora Serverless v2.
4. **Transform tools:** Glue for Bronze → Silver and dbt for Silver → Gold (recommended), or one tool for both.
5. **AI provider and model** on Bedrock, and the monthly AI budget.
6. **Sign-in:** keep the current sign-in code, or move to Amazon Cognito (needed for email verification and password reset).
7. **Data retention periods** for each layer (the values in section 3.2 are proposals).
8. **Budget size** to plan for in the first year (Pilot or Growth).
