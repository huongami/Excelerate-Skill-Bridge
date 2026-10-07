WITH jobs AS (
    SELECT * FROM "warehouse"."main"."stg_adzuna_jobs"
),
candidates AS (
    SELECT * FROM "warehouse"."main"."stg_international_resumes"
)
SELECT
    c.candidate_id,
    c.full_name as candidate_name,
    c.origin_country,
    c.sector as candidate_sector,
    c.anzsco_code as candidate_anzsco,
    c.years_of_experience,
    c.honest_gaps,
    j.job_id,
    j.job_title,
    j.company as employer_name,
    j.location as job_location,
    j.sector as job_sector,
    j.anzsco_code as job_anzsco,
    j.salary_range,
    j.posting_url,
    CASE 
        WHEN c.sector = j.sector AND c.anzsco_code = j.anzsco_code THEN 95.0
        WHEN c.sector = j.sector THEN 90.0
        WHEN (c.sector LIKE '%Operations%' AND j.sector LIKE '%Supply%') 
          OR (c.sector LIKE '%Finance%' AND j.sector LIKE '%Operations%') THEN 82.0
        ELSE 72.0
    END as match_score,
    CASE 
        WHEN c.sector = j.sector THEN 'Direct Industry Alignment'
        ELSE 'Transferable Cross-Sector Capability'
    END as match_tier,
    CURRENT_TIMESTAMP as dbt_updated_at
FROM candidates c
CROSS JOIN jobs j
WHERE c.sector = j.sector
   OR (c.sector IN ('Operations & Administration', 'Finance & Accounting', 'Technology & Data')
       AND j.sector IN ('Supply Chain & Logistics', 'Operations & Administration'))