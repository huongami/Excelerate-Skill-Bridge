
  
  create view "warehouse"."main"."stg_international_resumes__dbt_tmp" as (
    WITH raw_source AS (
    SELECT * FROM read_parquet('enterprise_pipeline/storage/silver/spark_silver_candidates.parquet')
)
SELECT
    candidate_id,
    full_name,
    origin_country,
    target_country,
    industry_category as sector,
    original_job_title,
    COALESCE(CAST(years_of_experience AS DOUBLE), 5.0) as years_of_experience,
    education,
    anzsco_code,
    anzsco_occupation,
    direct_skills,
    transferable_skills,
    skill_evidence_clean as skill_evidence,
    honest_gaps,
    transferability_rationale,
    ingestion_timestamp
FROM raw_source
WHERE candidate_id IS NOT NULL AND candidate_id != ''
  );
