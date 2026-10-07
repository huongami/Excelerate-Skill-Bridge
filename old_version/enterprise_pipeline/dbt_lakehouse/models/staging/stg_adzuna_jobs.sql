WITH raw_source AS (
    SELECT * FROM read_parquet('enterprise_pipeline/storage/silver/spark_silver_jobs.parquet')
)
SELECT
    job_id,
    TRIM(title) as job_title,
    company,
    location,
    industry_category as sector,
    anzsco_code,
    employment_type,
    CAST(salary_min AS DOUBLE) as salary_min,
    CAST(salary_max AS DOUBLE) as salary_max,
    salary_range,
    key_requirements,
    source_platform,
    posting_url,
    ingestion_timestamp
FROM raw_source
WHERE job_id IS NOT NULL AND job_id != ''
