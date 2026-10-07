"""
DAG: Capability Alignment & Gold Business Marts Pipeline
Joins Silver Lakehouse tables in DuckDB to produce:
1. Gold Capability Alignment Matrix (Candidate vs Job match affinity & gaps)
2. Gold Market Insights Mart (Supply vs Demand, average compensation by ANZSCO)
3. App Serving Layer Synchronization
"""

import os
import json
import duckdb
from datetime import datetime
from data_pipeline.orchestrator.engine import DAG, Task
from data_pipeline.transforms.quality_checks import run_table_quality_contracts

def build_gold_alignment_mart(context, logger):
    """Task 1: Generate capability alignment cross-product and match scoring in DuckDB."""
    config = context.config
    duck_path = config["storage"]["duckdb_path"]
    gold_dir = config["storage"]["gold_dir"]
    os.makedirs(gold_dir, exist_ok=True)

    con = duckdb.connect(duck_path)

    # Analytical Join & Match Scoring in SQL
    con.execute("""
        CREATE OR REPLACE TABLE gold_capability_alignment_matrix AS
        SELECT 
            c.candidate_id,
            c.full_name as candidate_name,
            c.origin_country,
            c.industry_category as candidate_sector,
            c.anzsco_code as candidate_anzsco,
            c.anzsco_occupation as candidate_role,
            c.years_of_experience,
            c.honest_gaps,
            j.job_id,
            j.title as job_title,
            j.company as employer_name,
            j.location as job_location,
            j.industry_category as job_sector,
            j.anzsco_code as job_anzsco,
            j.salary_range,
            j.posting_url,
            -- Capability match scoring formula:
            CASE 
                WHEN c.industry_category = j.industry_category AND c.anzsco_code = j.anzsco_code THEN 95.0
                WHEN c.industry_category = j.industry_category THEN 90.0
                WHEN (c.industry_category LIKE '%Operations%' AND j.industry_category LIKE '%Supply%') 
                  OR (c.industry_category LIKE '%Finance%' AND j.industry_category LIKE '%Operations%') THEN 82.0
                ELSE 70.0
            END as match_score,
            CASE 
                WHEN c.industry_category = j.industry_category THEN 'Direct Industry Alignment'
                ELSE 'Transferable Cross-Sector Capability'
            END as match_tier,
            CURRENT_TIMESTAMP as computed_at
        FROM silver_candidates c
        CROSS JOIN silver_jobs j
        WHERE c.industry_category = j.industry_category
           OR (c.industry_category IN ('Operations & Administration', 'Finance & Accounting', 'Technology & Data') 
               AND j.industry_category IN ('Supply Chain & Logistics', 'Operations & Administration'));
    """)

    # Export Gold Parquet
    parquet_path = os.path.join(gold_dir, "gold_alignment_matrix.parquet")
    con.execute(f"COPY gold_capability_alignment_matrix TO '{parquet_path}' (FORMAT PARQUET);")

    count = con.execute("SELECT COUNT(*) FROM gold_capability_alignment_matrix").fetchone()[0]
    con.close()

    context.metrics["records_transformed"] = count
    context.metrics["records_loaded"] = count
    logger.log_event(context.run_id, "INFO", f"Generated Gold Alignment Matrix: {count} candidate-job pairs in DuckDB and Parquet.")

def build_gold_market_summary(context, logger):
    """Task 2: Aggregate market talent supply vs job demand by sector."""
    config = context.config
    duck_path = config["storage"]["duckdb_path"]
    gold_dir = config["storage"]["gold_dir"]

    con = duckdb.connect(duck_path)

    con.execute("""
        CREATE OR REPLACE TABLE gold_market_insights AS
        WITH job_stats AS (
            SELECT 
                industry_category,
                COUNT(*) as live_vacancies,
                ROUND(AVG(NULLIF(salary_min, 0)), 0) as avg_salary_min,
                ROUND(AVG(NULLIF(salary_max, 0)), 0) as avg_salary_max
            FROM silver_jobs
            GROUP BY industry_category
        ),
        candidate_stats AS (
            SELECT 
                industry_category,
                COUNT(*) as available_candidates,
                ROUND(AVG(years_of_experience), 1) as avg_experience_years
            FROM silver_candidates
            GROUP BY industry_category
        )
        SELECT 
            COALESCE(j.industry_category, c.industry_category) as sector,
            COALESCE(j.live_vacancies, 0) as live_vacancies,
            COALESCE(c.available_candidates, 0) as available_candidates,
            COALESCE(c.avg_experience_years, 0.0) as avg_candidate_experience_yrs,
            COALESCE(j.avg_salary_min, 80000) as sector_avg_salary_min,
            COALESCE(j.avg_salary_max, 130000) as sector_avg_salary_max,
            ROUND(CAST(COALESCE(c.available_candidates, 0) AS FLOAT) / GREATEST(COALESCE(j.live_vacancies, 1), 1), 2) as talent_coverage_ratio,
            CURRENT_TIMESTAMP as updated_at
        FROM job_stats j
        FULL OUTER JOIN candidate_stats c ON j.industry_category = c.industry_category;
    """)

    parquet_path = os.path.join(gold_dir, "gold_market_insights.parquet")
    con.execute(f"COPY gold_market_insights TO '{parquet_path}' (FORMAT PARQUET);")
    con.close()

    logger.log_event(context.run_id, "INFO", "Generated Gold Market Insights: Supply vs Demand & compensation bands.")

def export_app_serving_layer(context, logger):
    """Task 3: Synchronize data to the web app frontend layer."""
    config = context.config
    duck_path = config["storage"]["duckdb_path"]
    con = duckdb.connect(duck_path)

    # Fetch normalized jobs
    jobs = con.execute("SELECT * FROM silver_jobs").fetchdf().to_dict(orient="records")
    # Fetch normalized candidates
    cands = con.execute("SELECT * FROM silver_candidates").fetchdf().to_dict(orient="records")
    con.close()

    # Sync to data/
    with open("data/australian_jobs.json", "w", encoding="utf-8") as f:
        # Re-attach camelCase helpers
        for j in jobs:
            j["id"] = j.get("job_id")
            j["category"] = j.get("industry_category")
            j["salary"] = j.get("salary_range")
            j["anzsco"] = j.get("anzsco_code")
            j["source"] = j.get("source_platform")
            j["redirect_url"] = j.get("posting_url")
            j["requirements"] = [r.strip() for r in str(j.get("requirements", "")).split("|") if r.strip()]
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    logger.log_event(context.run_id, "INFO", f"Synchronized serving layer: {len(jobs)} jobs and {len(cands)} candidates.")

def quality_check_gold(context, logger):
    """Task 4: Run data quality contracts against gold mart."""
    config = context.config
    duck_path = config["storage"]["duckdb_path"]
    con = duckdb.connect(duck_path)
    results = run_table_quality_contracts(con, "gold_capability_alignment_matrix", context.run_id, logger)
    con.close()

    if results["failed"] > 0:
        raise ValueError(f"Data quality contracts failed for gold_capability_alignment_matrix: {results['failed']} checks failed!")
    logger.log_event(context.run_id, "INFO", f"All {results['passed']} data quality checks PASSED for gold marts.")

def create_alignment_matrix_dag():
    dag = DAG("alignment_gold_pipeline", "Build Gold Capability Alignment Matrix and Market Insights in DuckDB")
    
    t1 = dag.add_task(Task("build_gold_alignment_mart", build_gold_alignment_mart))
    t2 = dag.add_task(Task("build_gold_market_summary", build_gold_market_summary))
    t3 = dag.add_task(Task("export_app_serving_layer", export_app_serving_layer))
    t4 = dag.add_task(Task("quality_check_gold", quality_check_gold))

    t1 >> t2 >> t3 >> t4
    return dag
