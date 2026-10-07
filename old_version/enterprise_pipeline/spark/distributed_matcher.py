"""
Skill Bridge — Enterprise PySpark Distributed Capability Matcher
Performs high-throughput distributed cross-matching between international candidate capabilities
and Australian job vacancies using PySpark Broadcast Joins and Column Expressions.
Generates:
1. Gold Capability Alignment Matrix (Parquet)
2. Gold Market Demand & Compensation Summary (Parquet)
"""

import os
import sys
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, broadcast, when, round as spark_round, current_timestamp, avg, count, lit
)

def run_distributed_spark_matching(silver_dir, gold_dir):
    """Executes distributed matching in Spark."""
    spark = (
        SparkSession.builder
        .appName("Spark-Distributed-Capability-Matcher")
        .master("local[*]")
        .config("spark.driver.memory", "2g")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    start_time = time.time()
    os.makedirs(gold_dir, exist_ok=True)

    jobs_parquet = os.path.join(silver_dir, "spark_silver_jobs.parquet")
    cands_parquet = os.path.join(silver_dir, "spark_silver_candidates.parquet")

    print(f"\n[SPARK] Reading Silver Parquet tables...")
    jobs_df = spark.read.parquet(jobs_parquet)
    cands_df = spark.read.parquet(cands_parquet)

    # 1. Build Capability Alignment Cross Match using Spark Column Expressions
    print("[SPARK] Performing distributed capability matching...")
    joined_df = (
        cands_df.alias("cands").crossJoin(broadcast(jobs_df.alias("jobs")))
        .filter(
            (col("cands.industry_category") == col("jobs.industry_category")) |
            (col("cands.industry_category").isin("Operations & Administration", "Finance & Accounting") &
             col("jobs.industry_category").isin("Supply Chain & Logistics", "Operations & Administration"))
        )
        .select(
            col("candidate_id"),
            col("full_name").alias("candidate_name"),
            col("origin_country"),
            col("cands.industry_category").alias("candidate_sector"),
            col("cands.anzsco_code").alias("candidate_anzsco"),
            col("years_of_experience"),
            col("honest_gaps"),
            col("job_id"),
            col("title").alias("job_title"),
            col("company").alias("employer_name"),
            col("location").alias("job_location"),
            col("jobs.industry_category").alias("job_sector"),
            col("jobs.anzsco_code").alias("job_anzsco"),
            col("salary_range"),
            col("posting_url"),
            when(
                (col("cands.industry_category") == col("jobs.industry_category")) &
                (col("cands.anzsco_code") == col("jobs.anzsco_code")),
                lit(95.0)
            ).when(
                col("cands.industry_category") == col("jobs.industry_category"),
                lit(90.0)
            ).otherwise(lit(78.0)).alias("match_score"),
            when(
                col("cands.industry_category") == col("jobs.industry_category"),
                lit("Direct Industry Alignment")
            ).otherwise(lit("Transferable Cross-Sector Capability")).alias("match_tier"),
            current_timestamp().alias("computed_at")
        )
    )

    gold_matrix_path = os.path.join(gold_dir, "spark_gold_alignment_matrix.parquet")
    joined_df.write.mode("overwrite").parquet(gold_matrix_path)
    total_matches = joined_df.count()

    # 2. Build Gold Market Insights Mart
    print("[SPARK] Aggregating Gold Market Insights (Talent Supply vs Job Demand)...")
    market_df = (
        jobs_df.groupBy("industry_category")
        .agg(
            count("job_id").alias("live_vacancies"),
            spark_round(avg("salary_min"), 0).alias("avg_salary_min"),
            spark_round(avg("salary_max"), 0).alias("avg_salary_max")
        )
        .withColumnRenamed("industry_category", "sector")
        .withColumn("computed_at", current_timestamp())
    )

    gold_market_path = os.path.join(gold_dir, "spark_gold_market_insights.parquet")
    market_df.write.mode("overwrite").parquet(gold_market_path)

    duration = time.time() - start_time
    print(f"[SPARK] Completed Distributed Matching: {total_matches} pairs in {duration:.2f}s")
    spark.stop()
    return {"status": "SUCCESS", "matches_computed": total_matches, "duration_sec": duration}

if __name__ == "__main__":
    run_distributed_spark_matching(
        "enterprise_pipeline/storage/silver",
        "enterprise_pipeline/storage/gold"
    )
