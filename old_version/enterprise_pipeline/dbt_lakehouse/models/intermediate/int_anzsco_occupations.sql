WITH cand_anzsco AS (
    SELECT DISTINCT
        anzsco_code,
        anzsco_occupation,
        sector
    FROM {{ ref('stg_international_resumes') }}
),
job_anzsco AS (
    SELECT DISTINCT
        anzsco_code,
        sector as anzsco_occupation,
        sector
    FROM {{ ref('stg_adzuna_jobs') }}
)
SELECT * FROM cand_anzsco
UNION
SELECT * FROM job_anzsco
