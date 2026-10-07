
  
  create view "warehouse"."main"."int_anzsco_occupations__dbt_tmp" as (
    WITH cand_anzsco AS (
    SELECT DISTINCT
        anzsco_code,
        anzsco_occupation,
        sector
    FROM "warehouse"."main"."stg_international_resumes"
),
job_anzsco AS (
    SELECT DISTINCT
        anzsco_code,
        sector as anzsco_occupation,
        sector
    FROM "warehouse"."main"."stg_adzuna_jobs"
)
SELECT * FROM cand_anzsco
UNION
SELECT * FROM job_anzsco
  );
