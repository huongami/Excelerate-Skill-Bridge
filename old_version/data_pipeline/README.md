# Skill Bridge — On-Premises Data Pipeline Engine 🇦🇺

An enterprise-grade, embedded, self-contained **On-Premises Data Pipeline** built for the Skill Bridge platform. It ingests live Australian job vacancies and real international candidate resumes, scrubs personal data (PII) under the **Australian Privacy Act 1988**, classifies occupations against the **ANZSCO** taxonomy, and computes capability alignment matrices inside an embedded **DuckDB Lakehouse**.

---

## 🏗️ Architecture: Medallion Lakehouse (On-Premises)

```
                    ┌──────────────────────────────────────────────┐
                    │            ON-PREMISES DATA PIPELINE         │
                    └──────────────────────────────────────────────┘
                                          │
       ┌──────────────────────────────────┴──────────────────────────────────┐
       ▼                                                                     ▼
[ Adzuna Australia API ]                                       [ Real Candidate Resumes ]
       │                                                                     │
       ▼                                                                     ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 1. BRONZE LAYER (Raw Ingestion Snapshots)                                          │
│    • storage/bronze/jobs_raw_<timestamp>.json                                     │
│    • storage/bronze/resumes_raw_<timestamp>.json                                  │
│    • Immutable landed data with batch timestamps & provenance metadata             │
└───────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 2. SILVER LAYER (Standardized & PII Scrubbed)                                     │
│    • On-Prem PII Scrubber (Masks emails, phone numbers, tax IDs, addresses)       │
│    • Australian ANZSCO Classification (ABS Unit Groups: 254411, 221111, 261313)   │
│    • Direct vs Transferable Capability Separation & Honest Gap Detection          │
│    • DuckDB Tables: `silver_jobs` (71 rows) | `silver_candidates` (80 rows)       │
│    • Parquet Exports: storage/silver/*.parquet                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 3. GOLD LAYER (Business Marts & Analytics)                                        │
│    • DuckDB Table: `gold_capability_alignment_matrix` (1,090 scored pairs)        │
│    • DuckDB Table: `gold_market_insights` (Talent supply vs Job demand)           │
│    • Parquet Exports: storage/gold/*.parquet                                      │
│    • Synchronizes Serving Layer to `data/` for web applications                   │
└───────────────────────────────────────────────────────────────────────────────────┘
                                          │
       ┌──────────────────────────────────┴──────────────────────────────────┐
       ▼                                                                     ▼
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│  DuckDB Embedded SQL Warehouse       │          │  SQLite Audit & Compliance Ledger     │
│  • Columnar execution                │          │  • Run history & task timestamps     │
│  • Parquet file caching              │          │  • Data quality assertion logs       │
│  • Zero-overhead local analytics     │          │  • System event logs                 │
└──────────────────────────────────────┘          └──────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
data_pipeline/
├── README.md                      # Complete documentation & usage guide
├── run.py                         # Master CLI runner
├── config/
│   └── pipeline_config.yaml       # Configuration (storage paths, thresholds, sources)
├── dags/
│   ├── job_ingestion_dag.py       # DAG 1: Australian Jobs Ingestion -> Silver
│   ├── resume_ingestion_dag.py    # DAG 2: Real Resumes & PII Scrubbing -> Silver
│   └── alignment_matrix_dag.py    # DAG 3: Gold Alignment Matrix & Market Insights
├── storage/
│   ├── warehouse.duckdb           # Embedded DuckDB Analytical Database
│   ├── pipeline_audit.db          # Embedded SQLite Audit Ledger
│   ├── bronze/                    # Raw immutable JSON batch snapshots
│   ├── silver/                    # Cleaned Parquet tables
│   └── gold/                      # Business Mart Parquet files
├── transforms/
│   ├── pii_scrubber.py            # PII masking (APPs compliant)
│   ├── anzsco_classifier.py       # Australian ANZSCO 4-6 digit occupation mapper
│   ├── capability_extractor.py    # Direct vs Transferable skills & honest gaps
│   └── quality_checks.py          # Data contract assertions (Great Expectations style)
├── orchestrator/
│   ├── engine.py                  # DAG executor with topological dependency ordering
│   └── audit_logger.py            # SQLite audit log manager
└── web/
    ├── dashboard.html             # High-tech On-Premises Pipeline Operations UI
    └── server.py                  # Self-contained embedded HTTP server & REST API
```

---

## 🚀 How to Run the Pipeline

### 1. Run Complete End-to-End Pipeline
Executes all 3 DAGs in topological sequence (Jobs -> Resumes -> Alignment) with automated data quality assertions:
```bash
python3 data_pipeline/run.py --all
```

### 2. Run a Specific DAG
```bash
# Ingest and standardize Australian vacancies
python3 data_pipeline/run.py --dag jobs

# Ingest and scrub real international resumes
python3 data_pipeline/run.py --dag resumes

# Build Gold capability matrix and market demand summary
python3 data_pipeline/run.py --dag alignment
```

### 3. Check Pipeline Status & Table Counts
```bash
python3 data_pipeline/run.py --status
```

### 4. Run Interactive SQL Query in DuckDB
Query the Lakehouse tables directly from the command line:
```bash
python3 data_pipeline/run.py --sql "SELECT sector, live_vacancies, available_candidates, sector_avg_salary_min, sector_avg_salary_max FROM gold_market_insights ORDER BY live_vacancies DESC"
```

---

## 🌐 On-Premises Web Operations Dashboard

Start the embedded, zero-dependency monitoring server:
```bash
python3 data_pipeline/run.py --web
```
Open your browser at: **`http://localhost:8085/dashboard`**

### Features:
- **Pipeline Health**: View Lakehouse storage size, records processed, and audit runs.
- **One-Click DAG Triggering**: Run any DAG or the full pipeline with live status updates.
- **Embedded DuckDB SQL Console**: Run analytical queries over DuckDB tables in the browser with formatted results.
- **Data Quality Contracts**: Review passed/failed contract assertions.
- **Audit Feed**: Inspect real-time execution logs from the SQLite ledger.

---

## ⚖️ Data Contracts & Quality Assertions

Every table in the pipeline is guarded by automated data contracts before data moves to downstream consumers:
1. **Primary Key Non-Nullability**: Asserts zero null or empty primary identifiers (`job_id`, `candidate_id`).
2. **ANZSCO Code Format**: Asserts that every code is a valid 4 to 6 digit Australian standard code.
3. **Salary Sanity**: Asserts `salary_max >= salary_min` and `salary_min >= 0`.
4. **Experience Range**: Asserts candidate experience is between 0 and 50 years.
5. **Evidence Completeness**: Asserts verbatim resume evidence has sufficient depth (> 20 characters).
6. **Match Score Boundedness**: Asserts capability alignment scores are strictly within $[0, 100]$.

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Returns Lakehouse table counts, DuckDB size, run summary |
| `GET` | `/api/logs` | Returns recent system and audit events |
| `GET` | `/api/quality` | Returns data contract assertion outcomes |
| `POST` | `/api/trigger` | Triggers DAG execution (`{"dag": "all" \| "jobs" \| "resumes" \| "alignment"}`) |
| `POST` | `/api/query` | Executes arbitrary DuckDB SQL query (`{"query": "SELECT ..."}`) |
